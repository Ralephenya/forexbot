"""
Single trading cycle — designed to be triggered by Claude Cowork on a schedule.

Run this every 15 minutes via Cowork task scheduler:
    python run_cycle.py
    python run_cycle.py --symbol GBPJPY
    python run_cycle.py --dry-run
"""
import sys
import yaml
import logging
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from logger import setup_logger
from database import Database
from data_feed import DataFeed
from indicators import calculate_all_indicators
from strategy import StrategyB
from position_manager import PositionManager
from risk_manager import RiskManager
from trade_logger import TradeLogger
from mt5_client import MT5Client


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Run one trading cycle")
    parser.add_argument("--symbol", type=str, help="Override trading symbol")
    parser.add_argument("--dry-run", action="store_true", help="Analyse only, no orders placed")
    parser.add_argument("--config", type=str, default="config.yaml", help="Config file path")
    args = parser.parse_args()

    config_path = Path(__file__).parent / args.config
    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}")
        sys.exit(1)

    config = load_config(str(config_path))
    setup_logger(config.get("logging", {}))
    logger = logging.getLogger(__name__)

    symbol = args.symbol or config["data"]["symbol"]
    dry_run = args.dry_run or config["risk"].get("demo_mode", True)

    print(f"\n{'='*60}")
    print(f"  TRADING CYCLE  |  {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Symbol: {symbol}  |  Dry-run: {dry_run}")
    print(f"{'='*60}")

    # --- Connect to MT5 ---
    mt5_cfg = config.get("mt5", {})
    try:
        broker = MT5Client(
            account=mt5_cfg["account"],
            password=mt5_cfg["password"],
            server=mt5_cfg["server"],
            path=mt5_cfg.get("path", ""),
        )
    except Exception as e:
        print(f"ERROR: MT5 connection failed — {e}")
        print("Make sure MetaTrader 5 is running on your laptop.")
        sys.exit(1)

    # --- Init components ---
    db = Database(config["database"]["path"])
    data_feed = DataFeed(broker, symbol, config["data"]["timeframe"])
    strategy = StrategyB(config)
    position_manager = PositionManager(db, broker)
    risk_manager = RiskManager(config, db)
    trade_logger = TradeLogger(
        config.get("logging", {}).get("file", "./logs/trading.log").replace(".log", "_trades.log")
    )

    # --- Kill switch / risk check ---
    if risk_manager.is_kill_switch_enabled():
        print("Kill switch is ON — no trades will be placed.")
        broker.shutdown()
        sys.exit(0)

    if not risk_manager.can_trade():
        print("Daily loss limit reached — trading paused for today.")
        broker.shutdown()
        sys.exit(0)

    # --- Account snapshot ---
    try:
        account = broker.get_account_info()
        print(f"\nAccount: {account['server']}")
        print(f"Balance:  ${account['balance']:,.2f}  |  Equity: ${account['equity']:,.2f}")
        print(f"Margin:   ${account['margin']:,.2f}  |  Free:   ${account['free_margin']:,.2f}")
    except Exception as e:
        print(f"WARNING: Could not fetch account info — {e}")

    # --- Skip if position already open ---
    if position_manager.has_open_position(symbol):
        pos = position_manager.get_open_position(symbol)
        try:
            broker_pos = broker.get_open_positions(symbol=symbol)
            if broker_pos:
                bp = broker_pos[0]
                pip_value = 0.0001
                direction = pos["direction"]
                entry = pos["entry_price"]
                current = bp["price_current"]
                pips = ((current - entry) / pip_value) if direction == "BUY" else ((entry - current) / pip_value)
                pnl = pips * 0.10 * (pos["units"] / 100000) / 0.01
                print(f"\nOpen position: {direction} {pos['units']/100000:.2f} lots @ {entry:.4f}")
                print(f"Current price: {current:.4f}  |  P&L: {pips:+.1f} pips  (${pnl:+.2f})")
        except Exception:
            print(f"\nOpen position detected — skipping signal check.")
        broker.shutdown()
        sys.exit(0)

    # --- Fetch data & calculate indicators ---
    print(f"\nFetching {config['data']['timeframe']} candles for {symbol}...")
    try:
        df = data_feed.get_candle_history(count=100)
    except Exception as e:
        print(f"ERROR: Failed to fetch market data — {e}")
        broker.shutdown()
        sys.exit(1)

    if df.empty:
        print("No market data returned — exiting.")
        broker.shutdown()
        sys.exit(1)

    df = calculate_all_indicators(
        df,
        rsi_period=config["strategy"]["rsi_period"],
        atr_period=config["strategy"]["atr_period"],
        ema_period=config["strategy"]["ema_period"],
        atr_median_window=config["strategy"]["atr_median_window"],
    )

    # --- Generate signal ---
    signal = strategy.generate_signal(df)

    if not signal or signal["action"] not in ("BUY", "SELL"):
        print("\nNo signal — market conditions not met.")
        broker.shutdown()
        sys.exit(0)

    print(f"\nSignal: {signal['action']}  Entry: {signal['entry_price']:.4f}")
    print(f"TP: {signal['take_profit']:.4f}  |  SL: {signal['stop_loss']:.4f}")

    if dry_run:
        print("\n[DRY RUN] Order NOT placed. Remove --dry-run or set demo_mode: false to trade.")
        trade_logger.log_signal(signal["action"], signal["entry_price"], symbol)
        broker.shutdown()
        sys.exit(0)

    # --- Risk checks ---
    open_count = len(db.get_open_trades())
    if not risk_manager.check_max_open_positions(open_count):
        print("Max open positions reached — skipping.")
        broker.shutdown()
        sys.exit(0)

    volume_lots = config["risk"]["position_size"]
    if not risk_manager.validate_position_size(int(volume_lots * 100000)):
        print("Position size validation failed — skipping.")
        broker.shutdown()
        sys.exit(0)

    # --- Place order ---
    direction_lots = volume_lots if signal["action"] == "BUY" else -volume_lots
    try:
        order = broker.place_market_order(
            instrument=symbol,
            units=direction_lots,
            direction=signal["action"],
            take_profit=signal["take_profit"],
            stop_loss=signal["stop_loss"],
        )
        trade_id = position_manager.open_position(order, signal)
        trade_logger.log_signal(signal["action"], signal["entry_price"], symbol)
        trade_logger.log_position_opened(volume_lots, symbol)
        trade_logger.log_tp_sl(signal["take_profit"], signal["stop_loss"])

        print(f"\nOrder placed successfully!")
        print(f"Trade ID: {trade_id}  |  Order: {order['order_id']}")
        print(f"Filled at: {order['price']:.4f}  |  Volume: {order['volume']:.2f} lots")
    except Exception as e:
        print(f"\nERROR: Order failed — {e}")
        trade_logger.log_error(f"Order failed: {str(e)[:80]}")

    broker.shutdown()
    print(f"\nCycle complete — {datetime.utcnow().strftime('%H:%M:%S UTC')}\n")


if __name__ == "__main__":
    main()
