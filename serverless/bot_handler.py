"""
Trading Bot Lambda Handler
Triggered by EventBridge every 15 minutes.

Flow:
  1. Check kill switch in S3
  2. Connect to MetaAPI (XM account)
  3. Sync broker positions → update S3 (catch TP/SL hits)
  4. If no open position: fetch candles, run Strategy B, place trade if signal
  5. Update bot_status in S3
"""
import sys
import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

# Add trading_system to path so we can reuse strategy/indicators
sys.path.insert(0, str(Path(__file__).parent.parent / "trading_system"))

from s3_store import S3Store
from metaapi_client import MetaApiClient
from indicators import calculate_all_indicators
from strategy import StrategyB

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Strategy config (mirrors config.yaml defaults)
STRATEGY_CONFIG = {
    "strategy": {
        "rsi_period": 14,
        "atr_period": 14,
        "ema_period": 20,
        "atr_median_window": 20,
        "rsi_oversold": 30,
        "rsi_overbought": 70,
        "high_vol_tp_multiplier": 1.5,
        "high_vol_sl_multiplier": 1.0,
        "low_vol_tp_multiplier": 2.0,
        "low_vol_sl_multiplier": 1.0,
        "allowed_hours": [9, 10, 12, 14],
        "blocked_hours": [13, 16],
    },
    "data": {
        "symbol": os.environ.get("TRADING_SYMBOL", "EURUSD"),
        "timeframe": "M15",
    },
    "risk": {
        "position_size": float(os.environ.get("POSITION_SIZE", "0.01")),
        "max_daily_loss": float(os.environ.get("MAX_DAILY_LOSS", "5.0")),
        "max_open_positions": int(os.environ.get("MAX_OPEN_POSITIONS", "2")),
    },
}

# Pip values per instrument
_PIP_VALUES = {"JPY": 0.01}  # JPY pairs use 0.01, all others 0.0001


def _pip_size(instrument: str) -> float:
    return 0.01 if "JPY" in instrument.upper() else 0.0001


def _calc_pnl(entry: float, exit_price: float, direction: str, units: int, instrument: str) -> tuple:
    pip = _pip_size(instrument)
    if direction == "BUY":
        pips = (exit_price - entry) / pip
    else:
        pips = (entry - exit_price) / pip
    lots = units / 100_000
    pnl = round(pips * 10 * lots, 2)
    return round(pips, 1), pnl


def handler(event, context):
    """
    Lambda entry point — called by EventBridge every 15 minutes.
    Also accepts manual invocation with {"action": "status"} for health checks.
    """
    logger.info(f"Bot Lambda triggered | event: {json.dumps(event)}")

    # Manual status check
    if isinstance(event, dict) and event.get("action") == "status":
        store = S3Store()
        return {"statusCode": 200, "body": store.get_system_state()}

    store = S3Store()

    # ── 1. Kill switch check ─────────────────────────────────────────────────
    state = store.get_system_state()
    if state.get("kill_switch", False):
        logger.info("Kill switch is ON — skipping trading cycle")
        return {"statusCode": 200, "body": "kill_switch_active"}

    store.update_system_state({"bot_status": "RUNNING", "last_run": datetime.utcnow().isoformat()})

    # ── 2. Connect to MetaAPI ────────────────────────────────────────────────
    try:
        broker = MetaApiClient()
    except Exception as e:
        logger.error(f"MetaAPI connection failed: {e}")
        store.update_system_state({"bot_status": f"ERROR: {str(e)[:80]}"})
        return {"statusCode": 500, "body": f"MetaAPI connection failed: {e}"}

    instrument = STRATEGY_CONFIG["data"]["symbol"]
    position_size = STRATEGY_CONFIG["risk"]["position_size"]

    # ── 3. Sync broker positions with S3 ─────────────────────────────────────
    # Detect TP/SL hits: trades open in S3 but closed at broker
    try:
        broker_positions = broker.get_open_positions(symbol=instrument)
        broker_tickets = {str(p["ticket"]) for p in broker_positions}

        open_in_db = store.get_open_trades()
        for db_trade in open_in_db:
            ticket = db_trade.get("broker_ticket", "")
            if ticket and ticket not in broker_tickets:
                # Position closed at broker (TP/SL hit) — update S3
                try:
                    current = broker.get_current_price(instrument)
                    exit_price = current["bid"] if db_trade["direction"] == "BUY" else current["ask"]
                except Exception:
                    exit_price = db_trade.get("entry_price", 0)

                pips, pnl = _calc_pnl(
                    db_trade["entry_price"], exit_price,
                    db_trade["direction"], db_trade["units"], instrument,
                )
                store.update_trade(db_trade["id"], {
                    "status": "CLOSED",
                    "exit_price": exit_price,
                    "pips": pips,
                    "pnl": pnl,
                    "exit_reason": "TP/SL",
                })
                logger.info(f"Synced closed trade #{db_trade['id']} | pips={pips} pnl=${pnl}")
    except Exception as e:
        logger.warning(f"Position sync error (non-fatal): {e}")

    # ── 4. Check if we already have an open position ─────────────────────────
    open_trades = store.get_open_trades()
    has_position = any(t.get("instrument") == instrument for t in open_trades)

    if has_position:
        logger.info(f"Already have an open position on {instrument} — skipping signal check")
        return {"statusCode": 200, "body": "position_exists"}

    # Check max open positions across all instruments
    if len(open_trades) >= STRATEGY_CONFIG["risk"]["max_open_positions"]:
        logger.info("Max open positions reached")
        return {"statusCode": 200, "body": "max_positions_reached"}

    # ── 5. Check daily loss limit ─────────────────────────────────────────────
    summary = store.get_account_summary()
    if summary["today_pnl"] <= -abs(STRATEGY_CONFIG["risk"]["max_daily_loss"]):
        logger.warning(f"Daily loss limit hit (${summary['today_pnl']:.2f}) — stopping for today")
        return {"statusCode": 200, "body": "daily_loss_limit"}

    # ── 6. Fetch candles and run strategy ────────────────────────────────────
    try:
        df = broker.get_candles(instrument, count=100, granularity="M15")
        if df.empty:
            logger.warning("No candle data returned from MetaAPI")
            return {"statusCode": 200, "body": "no_candle_data"}
    except Exception as e:
        logger.error(f"Failed to fetch candles: {e}")
        return {"statusCode": 500, "body": f"candle_fetch_failed: {e}"}

    df = calculate_all_indicators(df)
    strategy = StrategyB(STRATEGY_CONFIG)
    signal = strategy.generate_signal(df)

    if not signal or signal.get("action") not in ("BUY", "SELL"):
        logger.info("No signal generated this cycle")
        return {"statusCode": 200, "body": "no_signal"}

    logger.info(
        f"Signal: {signal['action']} | entry={signal['entry_price']:.5f} "
        f"TP={signal['take_profit']:.5f} SL={signal['stop_loss']:.5f} "
        f"regime={signal['volatility_regime']}"
    )

    # ── 7. Place the order ───────────────────────────────────────────────────
    try:
        order = broker.place_market_order(
            instrument=instrument,
            units=position_size,
            direction=signal["action"],
            take_profit=signal["take_profit"],
            stop_loss=signal["stop_loss"],
        )
    except Exception as e:
        logger.error(f"Order placement failed: {e}")
        store.update_system_state({"last_error": str(e)[:120]})
        return {"statusCode": 500, "body": f"order_failed: {e}"}

    # ── 8. Record trade in S3 ────────────────────────────────────────────────
    trade_id = store.save_trade({
        "timestamp": datetime.utcnow().isoformat(),
        "instrument": instrument,
        "direction": signal["action"],
        "entry_price": order.get("price", signal["entry_price"]),
        "units": int(position_size * 100_000),
        "take_profit": signal["take_profit"],
        "stop_loss": signal["stop_loss"],
        "status": "OPEN",
        "strategy_name": "StrategyB",
        "broker_ticket": str(order.get("position_id", "")),
        "volatility_regime": signal["volatility_regime"],
    })

    logger.info(f"Trade #{trade_id} placed successfully | order={order.get('order_id')}")

    return {
        "statusCode": 200,
        "body": {
            "trade_id": trade_id,
            "action": signal["action"],
            "instrument": instrument,
            "entry": order.get("price"),
            "take_profit": signal["take_profit"],
            "stop_loss": signal["stop_loss"],
        },
    }
