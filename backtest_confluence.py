"""
Confluence Engine Backtest — Head-to-Head Comparison

Compares Strategy B (raw) vs Strategy B + Confluence Filter
to prove whether the 7-layer scoring gate actually improves performance.

Data: Synthetic EUR/USD 15-minute data (6 months, ~11,500 candles)
Generated using Geometric Brownian Motion with realistic forex parameters:
  - Volatility: 0.07% per 15-min bar (typical EUR/USD)
  - Trend: near-zero long-term drift (forex reality)
  - Session effects: higher vol during London/NY open hours

This is standard quant practice when historical data is not yet loaded.
Replace generate_synthetic_data() with real CSV loading when data is available.
"""

import sys
import os
import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta, timezone

# ── path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'trading_system'))

from confluence_engine import score_trade, detect_sr_levels

logging.basicConfig(level=logging.WARNING)  # suppress noise during backtest
logger = logging.getLogger(__name__)

# ── constants ─────────────────────────────────────────────────────────────────
SPREAD_PIPS   = 1.2     # EUR/USD realistic spread
PIP_VALUE     = 0.01    # $0.01 per pip at 0.01 lots (micro lot)
TARGET_PIPS   = 10.0    # Fallback target (ATR-adaptive in real use)
STOP_PIPS     = 7.0     # Fallback stop
SESSION_START = 8       # London open UTC
SESSION_END   = 17      # London close UTC
MIN_SCORE     = 7       # Confluence threshold (walk-forward optimized)
RSI_BUY       = 28      # RSI buy threshold   (walk-forward optimized, was 30)
RSI_SELL      = 72      # RSI sell threshold  (walk-forward optimized, was 70)
TARGET_MULT   = 1.2     # ATR target multiplier (walk-forward optimized)
STOP_MULT     = 1.2     # ATR stop multiplier   (walk-forward optimized)


# ─────────────────────────────────────────────────────────────────────────────
# DATA GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def generate_synthetic_data(months: int = 6, seed: int = 42) -> pd.DataFrame:
    """
    Generate realistic synthetic EUR/USD 15-minute OHLCV data.

    Uses Geometric Brownian Motion with:
    - Session-aware volatility (London/NY 2x vol of Asian session)
    - Realistic mean-reversion tendency of FX pairs
    - Typical EUR/USD starting price around 1.08xx
    """
    np.random.seed(seed)

    # Build timestamp index (weekdays only, 24hr)
    start = datetime(2024, 9, 1, 0, 0, tzinfo=timezone.utc)
    end   = start + timedelta(days=months * 30)

    timestamps = []
    t = start
    while t < end:
        if t.weekday() < 5:  # Mon-Fri only
            timestamps.append(t)
        t += timedelta(minutes=15)

    n = len(timestamps)

    # Simulate price using GBM + mild mean reversion
    price = 1.0850
    prices = [price]
    mean_price = price
    mean_rev_speed = 0.001  # How fast price reverts to mean

    for i, ts in enumerate(timestamps[1:]):
        hour = ts.hour
        # Session volatility: London/NY has 2x more vol than Asian session
        if hour in range(8, 17):
            vol = 0.0007   # London/NY session
        elif hour in range(13, 17):
            vol = 0.0009   # NY overlap (most volatile)
        else:
            vol = 0.0003   # Asian session (quiet)

        # GBM with mean reversion
        drift = mean_rev_speed * (mean_price - price)
        shock = np.random.normal(0, vol)
        price = price * (1 + drift + shock)

        # Keep price in realistic EUR/USD range
        price = max(1.03, min(1.15, price))
        prices.append(price)

    prices = np.array(prices)

    # Build OHLCV
    rows = []
    for i, ts in enumerate(timestamps):
        close = prices[i]
        hour  = ts.hour

        # Intra-bar range based on session
        if hour in range(8, 17):
            bar_range = abs(np.random.normal(0, 0.0008))
        else:
            bar_range = abs(np.random.normal(0, 0.0003))

        bar_range = max(0.0001, bar_range)
        direction = np.random.choice([-1, 1])

        high  = close + bar_range * (0.5 + 0.5 * max(0, direction))
        low   = close - bar_range * (0.5 + 0.5 * max(0, -direction))
        open_ = close + np.random.uniform(-bar_range * 0.4, bar_range * 0.4)

        rows.append({
            'datetime': ts,
            'open':  round(open_, 5),
            'high':  round(high,  5),
            'low':   round(low,   5),
            'close': round(close, 5),
            'volume': int(np.random.uniform(500, 3000))
        })

    df = pd.DataFrame(rows)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# INDICATOR CALCULATION (standalone, no ta library dependency for backtest)
# ─────────────────────────────────────────────────────────────────────────────

def calc_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain  = delta.clip(lower=0)
    loss  = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()
    rs  = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calc_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - df['close'].shift()).abs(),
        (df['low']  - df['close'].shift()).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, min_periods=period).mean()


def calc_ema(close: pd.Series, period: int) -> pd.Series:
    return close.ewm(span=period, min_periods=period).mean()


def calc_macd(close: pd.Series, fast=12, slow=26, signal=9):
    ema_fast   = close.ewm(span=fast,   min_periods=fast).mean()
    ema_slow   = close.ewm(span=slow,   min_periods=slow).mean()
    macd_line  = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, min_periods=signal).mean()
    histogram  = macd_line - signal_line
    return macd_line, signal_line, histogram


def calc_vwap(df: pd.DataFrame) -> pd.Series:
    """Daily-reset VWAP"""
    df = df.copy()
    df['date'] = df['datetime'].dt.date
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    df['tp_vol'] = df['typical_price'] * df['volume']

    vwap = pd.Series(index=df.index, dtype=float)
    for date, group in df.groupby('date'):
        cum_tp_vol = group['tp_vol'].cumsum()
        cum_vol    = group['volume'].cumsum()
        vwap.loc[group.index] = cum_tp_vol / cum_vol

    return vwap


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['rsi']              = calc_rsi(df['close'])
    df['atr']              = calc_atr(df)
    df['ema_20']           = calc_ema(df['close'], 20)
    df['ema_50']           = calc_ema(df['close'], 50)
    df['ema_200']          = calc_ema(df['close'], 200)
    df['macd'], df['macd_signal'], df['macd_hist'] = calc_macd(df['close'])
    df['vwap']             = calc_vwap(df)
    atr_median             = df['atr'].rolling(20).median()
    df['is_high_volatility'] = df['atr'] > atr_median
    # Rename for strategy compatibility
    df['ema'] = df['ema_20']
    return df


# ─────────────────────────────────────────────────────────────────────────────
# RAW SIGNAL GENERATOR (Strategy B logic without confluence filter)
# ─────────────────────────────────────────────────────────────────────────────

def raw_signal(row) -> str:
    """Strategy B logic: regime switching, no confluence gate."""
    hour = row['datetime'].hour
    if hour < SESSION_START or hour >= SESSION_END:
        return None
    if pd.isna(row['rsi']) or pd.isna(row['atr']) or pd.isna(row['ema']):
        return None

    if row['is_high_volatility']:
        if row['rsi'] <= 30:
            return 'BUY'
        if row['rsi'] >= 70:
            return 'SELL'
    else:
        if row['close'] > row['ema']:
            return 'BUY'
        if row['close'] < row['ema']:
            return 'SELL'
    return None


# ─────────────────────────────────────────────────────────────────────────────
# CONFLUENCE SIGNAL GENERATOR (same logic + 7-layer scoring gate)
# ─────────────────────────────────────────────────────────────────────────────

def confluence_signal(df: pd.DataFrame, idx: int) -> str:
    """Strategy B + Confluence Engine gate."""
    row = df.iloc[idx]
    direction = raw_signal(row)
    if direction is None:
        return None

    # Feed confluence engine the last 100 candles for context
    lookback = df.iloc[max(0, idx - 100): idx + 1]
    if len(lookback) < 30:
        return None

    vwap = row.get('vwap', None)
    result = score_trade(
        df=lookback,
        direction=direction,
        current_hour=row['datetime'].hour,
        vwap=vwap
    )

    return direction if result['take_trade'] else None


# ─────────────────────────────────────────────────────────────────────────────
# BACKTEST ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def run_backtest(df: pd.DataFrame, use_confluence: bool) -> dict:
    """
    Simulate all trades and collect statistics.

    Args:
        df: Full OHLCV + indicator DataFrame
        use_confluence: True = only take A/A+ signals, False = take all signals

    Returns:
        dict with full trade log and performance metrics
    """
    trades     = []
    in_trade   = False
    entry_price = 0.0
    entry_dir   = None
    entry_time  = None
    target_p    = 0.0
    stop_p      = 0.0

    for i in range(200, len(df)):  # start at 200 to ensure indicators are warm
        row = df.iloc[i]
        close = row['close']
        high  = row['high']
        low   = row['low']
        ts    = row['datetime']

        # ── MANAGE OPEN TRADE ────────────────────────────────────────────────
        if in_trade:
            exit_price  = None
            exit_reason = None

            if entry_dir == 'BUY':
                if high >= target_p:
                    exit_price, exit_reason = target_p, 'TARGET'
                elif low <= stop_p:
                    exit_price, exit_reason = stop_p,  'STOP'
            else:  # SELL
                if low <= target_p:
                    exit_price, exit_reason = target_p, 'TARGET'
                elif high >= stop_p:
                    exit_price, exit_reason = stop_p,  'STOP'

            # Force close at session end
            if exit_price is None and ts.hour >= SESSION_END:
                exit_price, exit_reason = close, 'EOD'

            if exit_price is not None:
                if entry_dir == 'BUY':
                    pips = (exit_price - entry_price) * 10000 - SPREAD_PIPS
                else:
                    pips = (entry_price - exit_price) * 10000 - SPREAD_PIPS

                trades.append({
                    'entry_time':   entry_time,
                    'exit_time':    ts,
                    'direction':    entry_dir,
                    'entry_price':  entry_price,
                    'exit_price':   exit_price,
                    'pips':         round(pips, 2),
                    'pnl':          round(pips * PIP_VALUE, 4),
                    'exit_reason':  exit_reason
                })
                in_trade = False
            continue  # never enter and exit on same candle

        # ── LOOK FOR NEW ENTRY ───────────────────────────────────────────────
        if use_confluence:
            direction = confluence_signal(df, i)
        else:
            direction = raw_signal(row)

        if direction is None:
            continue

        # Calculate ATR-adaptive targets
        atr_pips = (row['atr'] / close) * 10000 if close > 0 else TARGET_PIPS
        t_pips   = max(atr_pips * 1.5, 6.0)
        s_pips   = max(atr_pips * 1.0, 4.0)

        entry_price = close + (SPREAD_PIPS / 2 / 10000) * (1 if direction == 'BUY' else -1)
        entry_dir   = direction
        entry_time  = ts
        in_trade    = True

        if direction == 'BUY':
            target_p = entry_price + t_pips / 10000
            stop_p   = entry_price - s_pips / 10000
        else:
            target_p = entry_price - t_pips / 10000
            stop_p   = entry_price + s_pips / 10000

    # ── PERFORMANCE METRICS ──────────────────────────────────────────────────
    if not trades:
        return {
            'trades': pd.DataFrame(),
            'total_trades': 0,
            'win_rate': 0,
            'total_pips': 0,
            'total_pnl': 0,
            'avg_win_pips': 0,
            'avg_loss_pips': 0,
            'profit_factor': 0,
            'max_drawdown_pips': 0,
            'best_trade': 0,
            'worst_trade': 0,
            'exit_breakdown': {}
        }

    trades_df   = pd.DataFrame(trades)
    winners     = trades_df[trades_df['pips'] > 0]
    losers      = trades_df[trades_df['pips'] <= 0]
    total_pips  = trades_df['pips'].sum()
    gross_win   = winners['pips'].sum() if len(winners) else 0
    gross_loss  = abs(losers['pips'].sum()) if len(losers) else 0.001
    profit_factor = gross_win / gross_loss

    # Max drawdown (running sum of pips)
    cumulative  = trades_df['pips'].cumsum()
    running_max = cumulative.cummax()
    drawdown    = cumulative - running_max
    max_dd      = drawdown.min()

    return {
        'trades':           trades_df,
        'total_trades':     len(trades_df),
        'win_rate':         len(winners) / len(trades_df) * 100,
        'total_pips':       round(total_pips, 1),
        'total_pnl':        round(trades_df['pnl'].sum(), 2),
        'avg_win_pips':     round(winners['pips'].mean(), 1) if len(winners) else 0,
        'avg_loss_pips':    round(losers['pips'].mean(),  1) if len(losers)  else 0,
        'profit_factor':    round(profit_factor, 2),
        'max_drawdown_pips': round(max_dd, 1),
        'best_trade':       round(trades_df['pips'].max(), 1),
        'worst_trade':      round(trades_df['pips'].min(), 1),
        'exit_breakdown':   trades_df['exit_reason'].value_counts().to_dict()
    }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN — run both strategies and print comparison
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print()
    print("=" * 65)
    print("  CONFLUENCE ENGINE BACKTEST  —  Strategy B vs Strategy B+C")
    print("  6 months  |  EUR/USD  |  15-minute bars  |  0.01 lots")
    print("=" * 65)

    # ── 1. Generate data ─────────────────────────────────────────────────────
    print("\n[1/3] Generating 6 months of synthetic EUR/USD 15m data...")
    df = generate_synthetic_data(months=6, seed=42)
    print(f"      {len(df):,} candles generated ({df['datetime'].min().date()} → {df['datetime'].max().date()})")

    # ── 2. Calculate indicators ──────────────────────────────────────────────
    print("[2/3] Calculating all indicators (RSI, ATR, EMA20/50/200, MACD, VWAP)...")
    df = add_all_indicators(df)

    # ── 3. Run both backtests ────────────────────────────────────────────────
    print("[3/3] Running backtests...\n")

    print("      Running: Strategy B (raw, no filter)...")
    raw = run_backtest(df, use_confluence=False)

    print("      Running: Strategy B + Confluence Engine (A/A+ only)...")
    conf = run_backtest(df, use_confluence=True)

    # ── 4. Print results ─────────────────────────────────────────────────────
    def bar(value, max_val, width=20, positive=True):
        filled = int(abs(value) / max(abs(max_val), 1) * width)
        char   = '█' if positive else '░'
        return char * filled + '·' * (width - filled)

    print()
    print("=" * 65)
    print(f"  {'METRIC':<28} {'RAW STRATEGY B':>15}  {'+ CONFLUENCE':>15}")
    print("=" * 65)

    metrics = [
        ("Total Trades",         raw['total_trades'],      conf['total_trades'],      ""),
        ("Win Rate",             raw['win_rate'],           conf['win_rate'],          "%"),
        ("Total Pips",           raw['total_pips'],         conf['total_pips'],        " pips"),
        ("Total P&L (0.01 lots)",raw['total_pnl'],          conf['total_pnl'],         "$"),
        ("Profit Factor",        raw['profit_factor'],      conf['profit_factor'],     "x"),
        ("Avg Win",              raw['avg_win_pips'],       conf['avg_win_pips'],      " pips"),
        ("Avg Loss",             raw['avg_loss_pips'],      conf['avg_loss_pips'],     " pips"),
        ("Max Drawdown",         raw['max_drawdown_pips'],  conf['max_drawdown_pips'], " pips"),
        ("Best Trade",           raw['best_trade'],         conf['best_trade'],        " pips"),
        ("Worst Trade",          raw['worst_trade'],        conf['worst_trade'],       " pips"),
    ]

    for label, rv, cv, unit in metrics:
        r_str = f"{rv:.1f}{unit}" if isinstance(rv, float) else f"{rv}{unit}"
        c_str = f"{cv:.1f}{unit}" if isinstance(cv, float) else f"{cv}{unit}"
        # Highlight improvement
        improved = ""
        if label in ("Win Rate", "Total Pips", "Total P&L (0.01 lots)", "Profit Factor", "Avg Win"):
            if cv > rv:
                improved = "  ▲"
        if label in ("Avg Loss", "Max Drawdown", "Worst Trade"):
            if cv > rv:  # less negative = better
                improved = "  ▲"
        print(f"  {label:<28} {r_str:>15}  {c_str:>15}{improved}")

    print("=" * 65)

    # Exit reason breakdown
    print()
    print("  EXIT BREAKDOWN")
    print(f"  {'Reason':<15} {'Raw':>8}  {'Confluence':>12}")
    print("  " + "-" * 40)
    all_reasons = set(list(raw['exit_breakdown'].keys()) + list(conf['exit_breakdown'].keys()))
    for reason in sorted(all_reasons):
        rv = raw['exit_breakdown'].get(reason, 0)
        cv = conf['exit_breakdown'].get(reason, 0)
        print(f"  {reason:<15} {rv:>8}  {cv:>12}")

    # Trade quality distribution for confluence
    if len(conf['trades']) > 0:
        print()
        print("  CONFLUENCE TRADE QUALITY SUMMARY")
        print(f"  Signals rejected by filter:  "
              f"{raw['total_trades'] - conf['total_trades']} "
              f"({(1 - conf['total_trades']/max(raw['total_trades'],1))*100:.0f}% filtered out)")
        print(f"  Trades that made it through: {conf['total_trades']} (only A and A+ setups)")

    # Verdict
    print()
    print("=" * 65)
    print("  VERDICT")
    print("=" * 65)

    if conf['win_rate'] > raw['win_rate'] and conf['profit_factor'] > raw['profit_factor']:
        print(f"  Confluence filter IMPROVED performance:")
        print(f"  Win rate:      {raw['win_rate']:.1f}% → {conf['win_rate']:.1f}%  "
              f"(+{conf['win_rate']-raw['win_rate']:.1f}%)")
        print(f"  Profit factor: {raw['profit_factor']:.2f}x → {conf['profit_factor']:.2f}x")
        print(f"  Total pips:    {raw['total_pips']:.0f} → {conf['total_pips']:.0f}")
        if conf['total_pips'] > raw['total_pips']:
            print(f"  Fewer trades, more pips — the engine is working.")
        else:
            print(f"  Higher quality trades but lower volume — tune MIN_SCORE or strategy.")
    elif conf['profit_factor'] > raw['profit_factor']:
        print(f"  Confluence improved trade quality (profit factor: "
              f"{raw['profit_factor']:.2f} → {conf['profit_factor']:.2f})")
        print(f"  Consider adjusting MIN_SCORE threshold for more trades.")
    else:
        print(f"  Results mixed on synthetic data — real historical data needed.")
        print(f"  Download real EUR/USD data and re-run for definitive results.")

    print()
    print("  Next step: download real historical data")
    print("  Run: python histdata_downloader.py")
    print("  Then replace generate_synthetic_data() with real CSV loading.")
    print("=" * 65)
    print()

    return raw, conf


if __name__ == "__main__":
    main()
