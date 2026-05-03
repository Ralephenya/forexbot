"""
Quick account & position status check — run any time via Cowork or terminal.

Usage:
    python status.py
    python status.py --symbol GBPJPY
"""
import sys
import yaml
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Quick status check")
    parser.add_argument("--symbol", type=str, help="Override symbol")
    parser.add_argument("--config", type=str, default="config.yaml")
    args = parser.parse_args()

    config_path = Path(__file__).parent / args.config
    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}")
        sys.exit(1)

    config = load_config(str(config_path))
    symbol = args.symbol or config["data"]["symbol"]

    from mt5_client import MT5Client
    mt5_cfg = config.get("mt5", {})

    print(f"\n{'='*55}")
    print(f"  STATUS CHECK  |  {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*55}")

    try:
        broker = MT5Client(
            account=mt5_cfg["account"],
            password=mt5_cfg["password"],
            server=mt5_cfg["server"],
            path=mt5_cfg.get("path", ""),
        )
    except Exception as e:
        print(f"\n  MT5: DISCONNECTED — {e}")
        print(f"{'='*55}\n")
        sys.exit(1)

    # Account info
    try:
        acc = broker.get_account_info()
        print(f"\n  MT5: CONNECTED")
        print(f"  Server:   {acc['server']}")
        print(f"  Balance:  ${acc['balance']:>10,.2f}")
        print(f"  Equity:   ${acc['equity']:>10,.2f}")
        print(f"  Margin:   ${acc['margin']:>10,.2f}")
        print(f"  Free:     ${acc['free_margin']:>10,.2f}")
        if acc['margin'] > 0:
            print(f"  Margin %: {acc['margin_level']:.1f}%")
    except Exception as e:
        print(f"\n  WARNING: Could not fetch account info — {e}")

    # Current price
    try:
        tick = broker.get_current_price(symbol)
        print(f"\n  {symbol} Price:")
        print(f"  Bid: {tick['bid']:.4f}  |  Ask: {tick['ask']:.4f}")
        spread = round((tick['ask'] - tick['bid']) * 10000, 1)
        print(f"  Spread: {spread:.1f} pips")
    except Exception as e:
        print(f"\n  WARNING: Could not fetch price for {symbol} — {e}")

    # Open positions
    try:
        positions = broker.get_open_positions(symbol=symbol)
        if positions:
            print(f"\n  Open Positions ({len(positions)}):")
            for p in positions:
                pip_value = 0.0001
                entry = p["price_open"]
                current = p["price_current"]
                direction = p["type"]
                pips = ((current - entry) / pip_value) if direction == "BUY" else ((entry - current) / pip_value)
                print(f"  {p['symbol']} {direction} {p['volume']:.2f} lots")
                print(f"    Entry: {entry:.4f}  Current: {current:.4f}  Pips: {pips:+.1f}")
                print(f"    TP: {p['tp']:.4f}  SL: {p['sl']:.4f}  Profit: ${p['profit']:+.2f}")
        else:
            print(f"\n  No open positions for {symbol}.")
    except Exception as e:
        print(f"\n  WARNING: Could not fetch positions — {e}")

    broker.shutdown()
    print(f"\n{'='*55}\n")


if __name__ == "__main__":
    main()
