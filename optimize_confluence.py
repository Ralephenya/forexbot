"""
Walk-Forward Confluence Optimizer
==================================
Realistic GARCH + regime-switching synthetic EUR/USD data.
Vectorized scoring. Walk-forward validation. Professional report.

Run: python optimize_confluence.py
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from itertools import product

# ── REALISTIC DATA GENERATOR ─────────────────────────────────────────────────

def generate_garch_data(months=12, seed=42):
    np.random.seed(seed)
    start = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)

    # Build 15-min weekday timestamps
    ts, t = [], start
    while len(ts) < months * 30 * 24 * 4:
        if t.weekday() < 5:
            ts.append(t)
        t += timedelta(minutes=15)
    n = len(ts)

    # ── GARCH(1,1) volatility ────────────────────────────────────────────────
    omega, alpha, beta = 1e-7, 0.08, 0.90
    h = np.zeros(n)
    eps = np.random.standard_normal(n)
    h[0] = omega / (1 - alpha - beta)
    for i in range(1, n):
        h[i] = omega + alpha * (eps[i-1] * np.sqrt(h[i-1]))**2 + beta * h[i-1]

    # ── Markov regime switching: 0=ranging, 1=trending ───────────────────────
    regime = np.zeros(n, dtype=int)
    # Transition matrix: P(trend→range)=0.02, P(range→trend)=0.01
    for i in range(1, n):
        if regime[i-1] == 0:  # ranging
            regime[i] = 1 if np.random.rand() < 0.008 else 0
        else:                  # trending
            regime[i] = 0 if np.random.rand() < 0.015 else 1

    # ── Session volatility multiplier ────────────────────────────────────────
    hours = np.array([t.hour for t in ts])
    sess_mult = np.where(np.isin(hours, [8, 9, 10, 13, 14, 15]), 2.2,
                np.where(np.isin(hours, [11, 12, 16]), 1.5,
                np.where(np.isin(hours, [0,1,2,3,4,5,22,23]), 0.4, 1.0)))

    # ── Price simulation ─────────────────────────────────────────────────────
    price = 1.0850
    prices = [price]
    trend_direction = 1
    trend_strength = 0.0

    for i in range(1, n):
        vol = np.sqrt(h[i]) * sess_mult[i]
        if regime[i] == 1:  # trending
            if i > 1 and regime[i-1] == 0:  # just switched to trend
                trend_direction = np.random.choice([-1, 1])
                trend_strength = np.random.uniform(0.0002, 0.0006)
            drift = trend_direction * trend_strength
        else:               # ranging — mild mean reversion
            drift = 0.001 * (1.0850 - price)

        shock = np.random.normal(0, vol)
        price = price * (1 + drift) + shock
        price = np.clip(price, 1.02, 1.16)
        prices.append(price)

    prices = np.array(prices)

    # ── Build OHLCV ──────────────────────────────────────────────────────────
    rows = []
    for i, t in enumerate(ts):
        c = prices[i]
        vol_bar = np.sqrt(h[i]) * sess_mult[i]
        rng = max(abs(np.random.normal(0, vol_bar * 2.5)), 0.00005)
        sign = np.random.choice([-1, 1])
        h_ = c + rng * (0.5 + 0.5 * max(0, sign))
        l_ = c - rng * (0.5 + 0.5 * max(0, -sign))
        o_ = c + np.random.uniform(-rng * 0.4, rng * 0.4)
        rows.append({
            'datetime': t,
            'open':  round(o_, 5),
            'high':  round(h_, 5),
            'low':   round(l_,  5),
            'close': round(c,   5),
            'volume': int(np.random.uniform(300, 4000) * sess_mult[i]),
            'regime': regime[i],
        })

    return pd.DataFrame(rows)


# ── INDICATORS ───────────────────────────────────────────────────────────────

def add_indicators(df):
    df = df.copy()
    c = df['close']

    # RSI
    delta = c.diff()
    gain  = delta.clip(lower=0)
    loss  = -delta.clip(upper=0)
    ag = gain.ewm(alpha=1/14, min_periods=14).mean()
    al = loss.ewm(alpha=1/14, min_periods=14).mean()
    df['rsi'] = 100 - 100 / (1 + ag / al.replace(0, np.nan))

    # ATR
    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - c.shift()).abs(),
        (df['low']  - c.shift()).abs(),
    ], axis=1).max(axis=1)
    df['atr'] = tr.ewm(alpha=1/14, min_periods=14).mean()

    # EMAs
    df['ema20']  = c.ewm(span=20,  min_periods=20).mean()
    df['ema50']  = c.ewm(span=50,  min_periods=50).mean()
    df['ema200'] = c.ewm(span=200, min_periods=200).mean()

    # MACD
    fast  = c.ewm(span=12, min_periods=12).mean()
    slow  = c.ewm(span=26, min_periods=26).mean()
    macd  = fast - slow
    df['macd']        = macd
    df['macd_signal'] = macd.ewm(span=9, min_periods=9).mean()

    # VWAP (daily reset)
    df['date'] = df['datetime'].dt.date
    tp = (df['high'] + df['low'] + df['close']) / 3
    df['tp_vol'] = tp * df['volume']
    vwap = pd.Series(index=df.index, dtype=float)
    for _, grp in df.groupby('date'):
        vwap.loc[grp.index] = grp['tp_vol'].cumsum() / grp['volume'].cumsum()
    df['vwap'] = vwap

    # Volatility regime
    atr_med = df['atr'].rolling(20).median()
    df['high_vol'] = (df['atr'] > atr_med).astype(int)

    # Session score
    prime = [8, 9, 10, 13, 14]
    dead  = [0, 1, 2, 3, 4, 5, 22, 23]
    hr    = df['datetime'].dt.hour
    df['prime_session'] = hr.isin(prime).astype(int)
    df['dead_session']  = hr.isin(dead).astype(int)

    # S/R proximity — rolling 50-bar high/low as proxy
    df['sr_high'] = df['high'].rolling(50).max()
    df['sr_low']  = df['low'].rolling(50).min()

    return df


# ── VECTORIZED CONFLUENCE SCORING ─────────────────────────────────────────────

def precompute_scores(df, rsi_buy=30, rsi_sell=70):
    """
    Returns buy_score and sell_score Series (0-10) for every row.
    Matches the 7-layer confluence engine logic.
    """
    c = df['close']

    # L1: HTF alignment (2 pts)
    buy_l1  = ((df.ema20 > df.ema50) & (df.ema50 > df.ema200)).astype(int) * 2
    sell_l1 = ((df.ema20 < df.ema50) & (df.ema50 < df.ema200)).astype(int) * 2

    # L2: RSI extreme (2 pts: 1 for moderate, +1 for very extreme)
    buy_l2  = (df.rsi <= rsi_buy).astype(int) + (df.rsi <= rsi_buy - 5).astype(int)
    sell_l2 = (df.rsi >= rsi_sell).astype(int) + (df.rsi >= rsi_sell + 5).astype(int)

    # L3: S/R proximity (2 pts)
    sr_prox = df.atr * 0.5
    buy_l3  = (np.abs(c - df.sr_low)  <= sr_prox).astype(int) * 2
    sell_l3 = (np.abs(c - df.sr_high) <= sr_prox).astype(int) * 2

    # L4: VWAP (1 pt)
    buy_l4  = (c < df.vwap).astype(int)
    sell_l4 = (c > df.vwap).astype(int)

    # L5: Prime session (1 pt)
    buy_l5  = df.prime_session
    sell_l5 = df.prime_session

    # L6: MACD (1 pt)
    buy_l6  = (df.macd > df.macd_signal).astype(int)
    sell_l6 = (df.macd < df.macd_signal).astype(int)

    # L7: Volatility regime (1 pt)
    buy_l7  = df.high_vol
    sell_l7 = df.high_vol

    buy_score  = buy_l1  + buy_l2  + buy_l3  + buy_l4  + buy_l5  + buy_l6  + buy_l7
    sell_score = sell_l1 + sell_l2 + sell_l3 + sell_l4 + sell_l5 + sell_l6 + sell_l7

    return buy_score.clip(0, 10), sell_score.clip(0, 10)


# ── BACKTEST ENGINE (numpy arrays — no pandas iloc in hot loop) ───────────────

def df_to_arrays(df, buy_score, sell_score):
    """Extract all needed columns as numpy arrays once."""
    return {
        'close':      df['close'].to_numpy(),
        'high':       df['high'].to_numpy(),
        'low':        df['low'].to_numpy(),
        'hour':       df['datetime'].dt.hour.to_numpy(),
        'atr':        df['atr'].to_numpy(),
        'buy_score':  buy_score.to_numpy(),
        'sell_score': sell_score.to_numpy(),
    }


def run_backtest(arrs, min_score=7, target_mult=1.5, stop_mult=1.0,
                 spread_pips=1.2, session_start=8, session_end=17):
    close  = arrs['close']
    high   = arrs['high']
    low    = arrs['low']
    hour   = arrs['hour']
    atr    = arrs['atr']
    b_sc   = arrs['buy_score']
    s_sc   = arrs['sell_score']
    n      = len(close)
    half_s = spread_pips * 0.5 / 10000

    pips_list = []
    in_trade  = False
    entry_dir = 1          # 1 = BUY, -1 = SELL
    entry_px  = target_p = stop_p = 0.0

    for i in range(220, n):
        hr = hour[i]
        c  = close[i]
        h  = high[i]
        l  = low[i]

        if in_trade:
            if entry_dir == 1:
                if h >= target_p:
                    pips_list.append((target_p - entry_px) * 10000 - spread_pips)
                    in_trade = False; continue
                if l <= stop_p:
                    pips_list.append((stop_p - entry_px) * 10000 - spread_pips)
                    in_trade = False; continue
            else:
                if l <= target_p:
                    pips_list.append((entry_px - target_p) * 10000 - spread_pips)
                    in_trade = False; continue
                if h >= stop_p:
                    pips_list.append((entry_px - stop_p) * 10000 - spread_pips)
                    in_trade = False; continue
            if hr >= session_end:
                pips = (c - entry_px) * 10000 * entry_dir - spread_pips
                pips_list.append(pips)
                in_trade = False
            continue

        if hr < session_start or hr >= session_end:
            continue

        bs = b_sc[i]
        ss = s_sc[i]
        if bs >= min_score and bs >= ss:
            d = 1
        elif ss >= min_score and ss > bs:
            d = -1
        else:
            continue

        atr_p = max(atr[i] * 10000, 4.0)
        ep    = c + d * half_s
        tp    = ep + d * atr_p * target_mult / 10000
        sp    = ep - d * atr_p * stop_mult   / 10000

        entry_dir = d; entry_px = ep; target_p = tp; stop_p = sp
        in_trade  = True

    if not pips_list:
        return {'trades': 0, 'win_rate': 0.0, 'total_pips': 0.0,
                'profit_factor': 0.0, 'max_dd': 0.0, 'sharpe': 0.0, 'calmar': 0.0}

    arr  = np.array(pips_list, dtype=np.float64)
    wins = arr[arr > 0]
    loss = arr[arr <= 0]
    cum  = np.cumsum(arr)
    dd   = float((cum - np.maximum.accumulate(cum)).min())
    pf   = float(wins.sum() / max(abs(loss.sum()), 0.001))
    sr   = float(arr.mean() / (arr.std() + 1e-9) * np.sqrt(252 * 26))
    cal  = float(cum[-1] / max(abs(dd), 1.0))

    return {
        'trades':        len(arr),
        'win_rate':      float(len(wins) / len(arr) * 100),
        'total_pips':    float(arr.sum()),
        'profit_factor': pf,
        'max_dd':        dd,
        'sharpe':        sr,
        'calmar':        cal,
    }


# ── WALK-FORWARD OPTIMIZATION ─────────────────────────────────────────────────

def walk_forward_optimize(df, buy_score, sell_score, param_grid):
    """
    4-fold walk-forward: train 5 months → test 1 month, roll 1 month.
    Converts to numpy arrays once per fold for speed.
    """
    total      = len(df)
    fold_size  = total // 12
    train_size = fold_size * 5

    folds = []
    for fold in range(4):
        train_start = fold * fold_size
        train_end   = train_start + train_size
        test_end    = train_end + fold_size
        if test_end > total:
            break

        df_tr  = df.iloc[train_start:train_end].reset_index(drop=True)
        df_te  = df.iloc[train_end:test_end].reset_index(drop=True)
        bs_tr  = buy_score.iloc[train_start:train_end].reset_index(drop=True)
        ss_tr  = sell_score.iloc[train_start:train_end].reset_index(drop=True)
        bs_te  = buy_score.iloc[train_end:test_end].reset_index(drop=True)
        ss_te  = sell_score.iloc[train_end:test_end].reset_index(drop=True)

        # Convert to numpy once
        arrs_tr = df_to_arrays(df_tr, bs_tr, ss_tr)
        arrs_te = df_to_arrays(df_te, bs_te, ss_te)

        best_pf, best_params = -999, None
        for params in param_grid:
            r = run_backtest(arrs_tr,
                             min_score=params['min_score'],
                             target_mult=params['target_mult'],
                             stop_mult=params['stop_mult'])
            if r['trades'] >= 5 and r['profit_factor'] > best_pf:
                best_pf, best_params = r['profit_factor'], params

        if best_params is None:
            continue

        oos = run_backtest(arrs_te,
                           min_score=best_params['min_score'],
                           target_mult=best_params['target_mult'],
                           stop_mult=best_params['stop_mult'])

        folds.append({'fold': fold + 1, 'best_params': best_params,
                      'train_pf': best_pf, 'oos': oos})

    return folds


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print()
    print("=" * 70)
    print("  WALK-FORWARD CONFLUENCE OPTIMIZER")
    print("  EUR/USD · 15-min · 12 months · GARCH + Regime Switching")
    print("=" * 70)

    # 1. Generate data
    print("\n[1/5] Generating 12 months of GARCH + regime-switching data...")
    df = generate_garch_data(months=12, seed=42)
    df = add_indicators(df)
    df = df.dropna().reset_index(drop=True)
    print(f"      {len(df):,} candles  |  "
          f"{df['datetime'].min().date()} → {df['datetime'].max().date()}")
    trend_pct = df['regime'].mean() * 100
    print(f"      Trending regime: {trend_pct:.1f}%  |  Ranging: {100-trend_pct:.1f}%")

    # 2. Pre-compute scores for RSI grid (heaviest computation once per RSI combo)
    print("\n[2/5] Pre-computing confluence scores for RSI grid...")
    rsi_combos = [(28, 72), (30, 70), (32, 68)]
    score_cache = {}
    for rb, rs in rsi_combos:
        bs, ss = precompute_scores(df, rsi_buy=rb, rsi_sell=rs)
        score_cache[(rb, rs)] = (bs, ss)
    print(f"      {len(rsi_combos)} RSI combos × precomputed vectorized scores ✓")

    # 3. Build parameter grid
    param_grid = []
    for (rb, rs), min_s, t_mult, s_mult in product(
        rsi_combos,
        [5, 6, 7, 8],           # min confluence score
        [1.2, 1.5, 1.8, 2.0],  # target ATR multiplier
        [0.8, 1.0, 1.2],        # stop ATR multiplier
    ):
        param_grid.append({
            'rsi_buy':     rb,
            'rsi_sell':    rs,
            'min_score':   min_s,
            'target_mult': t_mult,
            'stop_mult':   s_mult,
        })
    total_combos = len(param_grid) * 4  # × 4 folds
    print(f"\n[3/5] Walk-forward grid: {len(param_grid)} param combos × 4 folds = {total_combos} runs")

    # 4. Run walk-forward
    print("      Running... (this takes ~15s)")
    all_folds = []
    for (rb, rs) in rsi_combos:
        bs, ss = score_cache[(rb, rs)]
        sub_grid = [p for p in param_grid if p['rsi_buy'] == rb and p['rsi_sell'] == rs]
        folds = walk_forward_optimize(df, bs, ss, sub_grid)
        all_folds.extend(folds)

    if not all_folds:
        print("  ERROR: No valid folds found. Exiting.")
        return

    # 5. Print fold-by-fold OOS results
    print(f"\n[4/5] Walk-Forward OOS Results ({len(all_folds)} folds)\n")
    print(f"  {'Fold':<6} {'Min':<4} {'RSI B/S':<9} {'TP×':<5} {'SL×':<5} "
          f"{'Trades':<8} {'WinRate':<9} {'Pips':<8} {'PF':<6} {'Sharpe':<8} {'MaxDD'}")
    print("  " + "-" * 75)

    oos_pips_all = []
    for f in all_folds:
        p  = f['best_params']
        o  = f['oos']
        oos_pips_all.append(o['total_pips'])
        win_str  = f"{o['win_rate']:.1f}%" if o['trades'] else "—"
        pf_str   = f"{o['profit_factor']:.2f}" if o['trades'] else "—"
        sh_str   = f"{o['sharpe']:.2f}" if o['trades'] else "—"
        dd_str   = f"{o['max_dd']:.1f}" if o['trades'] else "—"
        pip_str  = f"{o['total_pips']:+.1f}" if o['trades'] else "—"
        print(f"  {f['fold']:<6} {p['min_score']:<4} "
              f"{p['rsi_buy']}/{p['rsi_sell']:<6} "
              f"{p['target_mult']:<5} {p['stop_mult']:<5} "
              f"{o['trades']:<8} {win_str:<9} {pip_str:<8} "
              f"{pf_str:<6} {sh_str:<8} {dd_str}")

    # 6. Aggregate OOS stats
    avg_oos_pips = np.mean(oos_pips_all)
    pos_folds    = sum(1 for p in oos_pips_all if p > 0)

    print()
    print(f"  OOS avg pips/month:  {avg_oos_pips:+.1f}")
    print(f"  Profitable folds:    {pos_folds}/{len(all_folds)}")

    # 7. Find consensus best params (most frequent in winning folds)
    winning_folds = [f for f in all_folds if f['oos']['total_pips'] > 0]
    if winning_folds:
        param_votes = {}
        for f in winning_folds:
            p = f['best_params']
            key = (p['min_score'], p['rsi_buy'], p['rsi_sell'],
                   p['target_mult'], p['stop_mult'])
            param_votes[key] = param_votes.get(key, 0) + f['oos']['profit_factor']
        best_key = max(param_votes, key=param_votes.get)
        best_min, best_rb, best_rs, best_tm, best_sm = best_key
    else:
        # Fall back to fold with max profit factor
        best_f    = max(all_folds, key=lambda f: f['oos']['profit_factor'])
        p         = best_f['best_params']
        best_min  = p['min_score']
        best_rb   = p['rsi_buy']
        best_rs   = p['rsi_sell']
        best_tm   = p['target_mult']
        best_sm   = p['stop_mult']

    # 8. Final full-period backtest with optimized params
    print(f"\n[5/5] Final full-period backtest with optimized parameters\n")
    print(f"  Optimal params:")
    print(f"    Min confluence score : {best_min}/10")
    print(f"    RSI buy / sell       : ≤{best_rb} / ≥{best_rs}")
    print(f"    Target mult (ATR×)   : {best_tm}")
    print(f"    Stop mult   (ATR×)   : {best_sm}")
    print(f"    R:R ratio            : {best_tm/best_sm:.2f}:1")

    bs_final, ss_final = precompute_scores(df, rsi_buy=best_rb, rsi_sell=best_rs)
    arrs_final = df_to_arrays(df, bs_final, ss_final)
    final = run_backtest(arrs_final,
                         min_score=best_min,
                         target_mult=best_tm,
                         stop_mult=best_sm)

    # Also run raw baseline (min_score=1 = no filter)
    bs_raw, ss_raw = precompute_scores(df, rsi_buy=30, rsi_sell=70)
    arrs_raw = df_to_arrays(df, bs_raw, ss_raw)
    baseline = run_backtest(arrs_raw, min_score=1,
                            target_mult=1.5, stop_mult=1.0)

    print()
    print("=" * 70)
    print(f"  {'METRIC':<30} {'BASELINE (no filter)':>20}  {'OPTIMIZED':>15}")
    print("=" * 70)

    def fmt(v, unit=''):
        if v == 0 and unit == '%': return '0.0%'
        return f"{v:+.1f}{unit}" if unit in (' pips', '') else f"{v:.2f}{unit}"

    rows_out = [
        ("Total Trades",         baseline['trades'],        final['trades'],        ''),
        ("Win Rate",             baseline['win_rate'],       final['win_rate'],      '%'),
        ("Total Pips (12m)",     baseline['total_pips'],     final['total_pips'],    ' pips'),
        ("Avg Pips / Month",     baseline['total_pips']/12,  final['total_pips']/12, ' pips'),
        ("Profit Factor",        baseline['profit_factor'],  final['profit_factor'], 'x'),
        ("Sharpe Ratio",         baseline['sharpe'],         final['sharpe'],        ''),
        ("Calmar Ratio",         baseline['calmar'],         final['calmar'],        ''),
        ("Max Drawdown",         baseline['max_dd'],         final['max_dd'],        ' pips'),
    ]
    for label, bv, ov, unit in rows_out:
        bstr = f"{bv:.1f}{unit}" if isinstance(bv, float) else f"{bv}{unit}"
        ostr = f"{ov:.1f}{unit}" if isinstance(ov, float) else f"{ov}{unit}"
        improve = ""
        if label in ("Win Rate", "Total Pips (12m)", "Profit Factor", "Sharpe Ratio", "Calmar Ratio", "Avg Pips / Month"):
            if ov > bv: improve = "  ▲ BETTER"
        if label == "Max Drawdown":
            if ov > bv: improve = "  ▲ BETTER"
        print(f"  {label:<30} {bstr:>20}  {ostr:>15}{improve}")

    print("=" * 70)

    # Monthly breakdown (estimate per fold)
    print()
    print("  WALK-FORWARD MONTHLY SUMMARY")
    print(f"  {'Month':<8} {'Trades':<8} {'Win%':<8} {'Pips':>8}  {'PF':>6}")
    print("  " + "-" * 42)
    for i, f in enumerate(all_folds, 1):
        o = f['oos']
        if o['trades'] == 0:
            print(f"  {i:<8} {'—':>6}")
            continue
        pip_str = f"{o['total_pips']:+.1f}"
        print(f"  {i:<8} {o['trades']:<8} {o['win_rate']:.1f}%    "
              f"{pip_str:>8}   {o['profit_factor']:.2f}")

    print()
    print("=" * 70)
    print("  VERDICT")
    print("=" * 70)

    if final['profit_factor'] > 1.3 and final['win_rate'] > 50:
        grade = "DEPLOYABLE"
        msg   = "Strategy is profitable with positive expectancy. Trade it."
    elif final['profit_factor'] > 1.0:
        grade = "PROMISING"
        msg   = "Positive edge exists. Run on demo before live."
    else:
        grade = "NEEDS WORK"
        msg   = "No consistent edge on synthetic data. Revisit logic."

    print(f"  Grade: {grade}")
    print(f"  {msg}")
    print(f"  Win Rate:      {final['win_rate']:.1f}%")
    print(f"  Profit Factor: {final['profit_factor']:.2f}x")
    print(f"  Sharpe:        {final['sharpe']:.2f}")
    print(f"  Avg/Month:     {final['total_pips']/12:+.1f} pips")
    print()
    print("  To use these params — set in backtest_confluence.py and config.py:")
    print(f"    MIN_SCORE_TO_TRADE  = {best_min}")
    print(f"    RSI_BUY_THRESHOLD   = {best_rb}")
    print(f"    RSI_SELL_THRESHOLD  = {best_rs}")
    print(f"    TARGET_ATR_MULT     = {best_tm}")
    print(f"    STOP_ATR_MULT       = {best_sm}")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
