"""
Daily P&L report — triggered by Claude Cowork each morning.

Usage:
    python daily_report.py              # Yesterday's summary
    python daily_report.py --days 7     # Last 7 days
    python daily_report.py --today      # Today so far
"""
import sys
import yaml
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime, timedelta, date


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r") as f:
        import yaml
        return yaml.safe_load(f)


def fetch_trades(db_path: str, from_date: date, to_date: date) -> list:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM trades
        WHERE date(entry_time) >= ? AND date(entry_time) <= ?
        ORDER BY entry_time ASC
        """,
        (from_date.isoformat(), to_date.isoformat()),
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def fetch_closed_trades(db_path: str, from_date: date, to_date: date) -> list:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM trades
        WHERE status = 'CLOSED'
          AND date(exit_time) >= ? AND date(exit_time) <= ?
        ORDER BY exit_time ASC
        """,
        (from_date.isoformat(), to_date.isoformat()),
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def print_report(trades: list, from_date: date, to_date: date, label: str):
    print(f"\n{'='*60}")
    print(f"  DAILY REPORT  |  {label}")
    print(f"  Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}")

    if not trades:
        print("\n  No closed trades in this period.")
        print(f"{'='*60}\n")
        return

    total_pnl = 0.0
    total_pips = 0.0
    wins = 0
    losses = 0

    print(f"\n{'#':<4} {'Symbol':<10} {'Dir':<5} {'Entry':>10} {'Exit':>10} {'Pips':>8} {'P&L':>10} {'Exit Reason'}")
    print("-" * 65)

    for i, t in enumerate(trades, 1):
        entry = float(t.get("entry_price", 0) or 0)
        exit_p = float(t.get("exit_price", 0) or 0)
        direction = t.get("direction", "?")
        symbol = t.get("instrument", "?")
        units = float(t.get("units", 0) or 0)
        reason = t.get("exit_reason", "?") or "?"

        pip_value = 0.0001
        if exit_p and entry:
            pips = ((exit_p - entry) / pip_value) if direction == "BUY" else ((entry - exit_p) / pip_value)
            lots = units / 100000
            pnl = pips * 0.10 * lots / 0.01
        else:
            pips = 0.0
            pnl = float(t.get("pnl", 0) or 0)

        total_pips += pips
        total_pnl += pnl
        if pnl >= 0:
            wins += 1
        else:
            losses += 1

        pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
        pips_str = f"{pips:+.1f}"
        print(f"{i:<4} {symbol:<10} {direction:<5} {entry:>10.4f} {exit_p:>10.4f} {pips_str:>8} {pnl_str:>10} {reason}")

    total_trades = wins + losses
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    total_pnl_str = f"+${total_pnl:.2f}" if total_pnl >= 0 else f"-${abs(total_pnl):.2f}"

    print("-" * 65)
    print(f"\n  Trades:    {total_trades}  (W: {wins}  L: {losses}  WR: {win_rate:.0f}%)")
    print(f"  Total P&L: {total_pnl_str}")
    print(f"  Total Pips: {total_pips:+.1f}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Daily trading report")
    parser.add_argument("--days", type=int, default=1, help="Number of past days to report (default: 1 = yesterday)")
    parser.add_argument("--today", action="store_true", help="Report for today so far")
    parser.add_argument("--config", type=str, default="config.yaml", help="Config file path")
    args = parser.parse_args()

    config_path = Path(__file__).parent / args.config
    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}")
        sys.exit(1)

    config = load_config(str(config_path))
    db_path = config["database"]["path"]

    today = date.today()

    if args.today:
        from_date = today
        to_date = today
        label = f"Today ({today.isoformat()})"
    elif args.days == 1:
        from_date = today - timedelta(days=1)
        to_date = today - timedelta(days=1)
        label = f"Yesterday ({from_date.isoformat()})"
    else:
        from_date = today - timedelta(days=args.days)
        to_date = today
        label = f"Last {args.days} days ({from_date.isoformat()} to {to_date.isoformat()})"

    try:
        trades = fetch_closed_trades(db_path, from_date, to_date)
        print_report(trades, from_date, to_date, label)
    except Exception as e:
        print(f"ERROR: Could not generate report — {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
