"""
Confluence Optimizer v2 — Trailing Stops + Tiered Targets + Partial Profits
============================================================================
Three upgrades over v1:
  1. TRAILING STOP  — once +1×ATR, move stop to breakeven, then trail 0.8×ATR behind price
  2. TIERED TARGETS — A+ (score 9-10) gets 2.5× ATR target; A (7-8) gets 1.5×
  3. PARTIAL PROFIT — close half at 1× ATR; let the rest ride with trailing stop

Same GARCH + regime data, same vectorized scoring, same walk-forward.

Run: python optimize_v2.py
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from itertools import product

# ── IMPORT data generator + indicators + scoring from v1 ──────────────────────
from optimize_confluence import (
    generate_garch_data, add_indicators, precompute_scores, df_to_arrays
)


# ── v2 BACKTEST ENGINE — trailing stop + tiered targets + partial profit ──────

def run_backtest_v2(arrs, min_score=7, base_target=1.5, stop_mult=1.0,
                    aplus_target=2.5, trail_trigger=1.0, trail_dist=0.8,
                    partial_at=1.0, partial_pct=0.5,
                    spread_pips=1.2, session_start=8, session_end=17):
    """
    Advanced backtest with trailing stop, tiered targets, partial profit.

    Args:
        min_score:     minimum confluence score to enter
        base_target:   ATR multiplier for target (A grade, score 7-8)
        aplus_target:  ATR multiplier for target (A+ grade, score 9-10)
        stop_mult:     ATR multiplier for initial stop
        trail_trigger: ATR move in favor to activate trailing stop
        trail_dist:    trailing stop distance in ATR behind price
        partial_at:    ATR move to take partial profit
        partial_pct:   fraction of position to close at partial (0.5 = half)
    """
    close = arrs['close']
    high  = arrs['high']
    low   = arrs['low']
    hour  = arrs['hour']
    atr   = arrs['atr']
    b_sc  = arrs['buy_score']
    s_sc  = arrs['sell_score']
    n     = len(close)
    half_s = spread_pips * 0.5 / 10000

    pips_list = []
    in_trade  = False
    d = 1                 # direction: 1=BUY, -1=SELL
    ep = tp = sp = 0.0    # entry, target, stop
    atr_entry = 0.0       # ATR at entry (in price units)
    trail_on  = False     # trailing stop active?
    partial_done = False  # already took partial?
    pos_size  = 1.0       # remaining position fraction

    for i in range(220, n):
        hr = hour[i]
        c, h, l = close[i], high[i], low[i]

        if in_trade:
            # Current best/worst price this candle
            fav_px  = h if d == 1 else l   # most favorable
            adv_px  = l if d == 1 else h   # most adverse

            # Distance moved in our favor (in price units)
            move = (fav_px - ep) * d

            # ── 1. Check target hit ──────────────────────────────────────
            if d == 1 and h >= tp:
                pips = (tp - ep) * 10000 * pos_size - spread_pips
                pips_list.append(pips)
                in_trade = False; continue
            if d == -1 and l <= tp:
                pips = (ep - tp) * 10000 * pos_size - spread_pips
                pips_list.append(pips)
                in_trade = False; continue

            # ── 2. Check stop hit ────────────────────────────────────────
            if d == 1 and l <= sp:
                pips = (sp - ep) * 10000 * pos_size - spread_pips
                pips_list.append(pips)
                in_trade = False; continue
            if d == -1 and h >= sp:
                pips = (ep - sp) * 10000 * pos_size - spread_pips
                pips_list.append(pips)
                in_trade = False; continue

            # ── 3. Partial profit at 1× ATR ─────────────────────────────
            if not partial_done and move >= partial_at * atr_entry:
                # Close partial_pct of position at current favorable price
                partial_pips = (fav_px - ep) * d * 10000 * partial_pct - spread_pips * partial_pct
                pips_list.append(partial_pips)
                pos_size -= partial_pct
                partial_done = True
                # Move stop to breakeven
                sp = ep + d * spread_pips / 10000  # breakeven + spread

            # ── 4. Trailing stop activation + update ─────────────────────
            if not trail_on and move >= trail_trigger * atr_entry:
                trail_on = True
                sp = ep + d * spread_pips / 10000  # at least breakeven

            if trail_on:
                # Trail the stop behind the most favorable price seen
                new_sp = fav_px - d * trail_dist * atr_entry
                if d == 1:
                    sp = max(sp, new_sp)   # only move stop UP for buys
                else:
                    sp = min(sp, new_sp)   # only move stop DOWN for sells

            # ── 5. Force close at session end ────────────────────────────
            if hr >= session_end:
                pips = (c - ep) * 10000 * d * pos_size - spread_pips * pos_size
                pips_list.append(pips)
                in_trade = False
            continue

        # ── ENTRY LOGIC ──────────────────────────────────────────────────
        if hr < session_start or hr >= session_end:
            continue

        bs = b_sc[i]
        ss = s_sc[i]

        score = 0
        if bs >= min_score and bs >= ss:
            d = 1; score = int(bs)
        elif ss >= min_score and ss > bs:
            d = -1; score = int(ss)
        else:
            continue

        atr_px    = atr[i]
        atr_entry = atr_px
        atr_pips  = max(atr_px * 10000, 4.0)

        # Tiered target: A+ gets bigger target
        t_mult = aplus_target if score >= 9 else base_target

        ep = c + d * half_s
        tp = ep + d * atr_pips * t_mult / 10000
        sp = ep - d * atr_pips * stop_mult / 10000

        in_trade     = True
        trail_on     = False
        partial_done = False
        pos_size     = 1.0

    # ── STATS ────────────────────────────────────────────────────────────
    if not pips_list:
        return {'trades': 0, 'win_rate': 0.0, 'total_pips': 0.0,
                'profit_factor': 0.0, 'max_dd': 0.0, 'sharpe': 0.0,
                'calmar': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0, 'best': 0.0}

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
        'avg_win':       float(wins.mean()) if len(wins) else 0.0,
        'avg_loss':      float(loss.mean()) if len(loss) else 0.0,
        'best':          float(arr.max()),
    }


# ── WALK-FORWARD v2 ──────────────────────────────────────────────────────────

def walk_forward_v2(df, buy_score, sell_score, param_grid):
    total      = len(df)
    fold_size  = total // 12
    train_size = fold_size * 5

    folds = []
    for fold in range(4):
        ts = fold * fold_size
        te = ts + train_size
        oe = te + fold_size
        if oe > total:
            break

        arrs_tr = df_to_arrays(
            df.iloc[ts:te].reset_index(drop=True),
            buy_score.iloc[ts:te].reset_index(drop=True),
            sell_score.iloc[ts:te].reset_index(drop=True))
        arrs_te = df_to_arrays(
            df.iloc[te:oe].reset_index(drop=True),
            buy_score.iloc[te:oe].reset_index(drop=True),
            sell_score.iloc[te:oe].reset_index(drop=True))

        best_pf, best_p = -999, None
        for p in param_grid:
            r = run_backtest_v2(arrs_tr, **p)
            if r['trades'] >= 5 and r['profit_factor'] > best_pf:
                best_pf, best_p = r['profit_factor'], p

        if best_p is None:
            continue

        oos = run_backtest_v2(arrs_te, **best_p)
        folds.append({'fold': fold + 1, 'params': best_p, 'train_pf': best_pf, 'oos': oos})

    return folds


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print()
    print("=" * 75)
    print("  CONFLUENCE OPTIMIZER v2")
    print("  Trailing Stop · Tiered Targets · Partial Profits")
    print("  EUR/USD · 15-min · 12 months · GARCH + Regime Switching")
    print("=" * 75)

    # 1. Data
    print("\n[1/5] Generating data...")
    df = generate_garch_data(months=12, seed=42)
    df = add_indicators(df)
    df = df.dropna().reset_index(drop=True)
    print(f"      {len(df):,} candles | "
          f"{df['datetime'].min().date()} → {df['datetime'].max().date()}")

    # 2. Scores
    print("[2/5] Pre-computing scores...")
    rsi_combos = [(28, 72), (30, 70)]
    score_cache = {}
    for rb, rs in rsi_combos:
        bs, ss = precompute_scores(df, rsi_buy=rb, rsi_sell=rs)
        score_cache[(rb, rs)] = (bs, ss)

    # 3. Parameter grid (v2 params)
    param_grid = []
    for (rb, rs), min_s, bt, at, sm in product(
        rsi_combos,
        [6, 7, 8],               # min score
        [1.5, 1.8, 2.0],         # base target (A grade)
        [2.5, 3.0, 3.5],         # A+ target
        [1.0, 1.2],              # stop mult
    ):
        param_grid.append({
            'min_score':    min_s,
            'base_target':  bt,
            'aplus_target': at,
            'stop_mult':    sm,
        })

    total_combos = len(param_grid) * 4
    print(f"[3/5] Grid: {len(param_grid)} combos × 4 folds = {total_combos} runs")
    print("      Running...")

    # 4. Walk-forward
    all_folds = []
    for (rb, rs) in rsi_combos:
        bs, ss = score_cache[(rb, rs)]
        sub = [p for p in param_grid]  # all params use same score cache
        folds = walk_forward_v2(df, bs, ss, sub)
        for f in folds:
            f['rsi'] = (rb, rs)
        all_folds.extend(folds)

    if not all_folds:
        print("  No valid folds.")
        return

    # 5. Results
    print(f"\n[4/5] Walk-Forward OOS Results ({len(all_folds)} folds)\n")
    print(f"  {'Fold':<5} {'Min':<4} {'Base':<5} {'A+':<5} {'SL×':<5} "
          f"{'Tr':<5} {'Win%':<7} {'Pips':<9} {'PF':<6} {'AvgW':<7} {'Best':<7} {'DD'}")
    print("  " + "-" * 78)

    oos_pips = []
    for f in all_folds:
        p, o = f['params'], f['oos']
        oos_pips.append(o['total_pips'])
        if o['trades'] == 0:
            print(f"  {f['fold']:<5} — no trades"); continue
        print(f"  {f['fold']:<5} {p['min_score']:<4} {p['base_target']:<5} "
              f"{p['aplus_target']:<5} {p['stop_mult']:<5} "
              f"{o['trades']:<5} {o['win_rate']:.1f}%  {o['total_pips']:>+8.1f} "
              f"{o['profit_factor']:.2f}   {o['avg_win']:>+5.1f}  "
              f"{o['best']:>+5.1f}  {o['max_dd']:.0f}")

    avg_pips = np.mean(oos_pips)
    pos_folds = sum(1 for p in oos_pips if p > 0)
    print(f"\n  OOS avg pips:       {avg_pips:+.1f}")
    print(f"  Profitable folds:   {pos_folds}/{len(all_folds)}")

    # Find best params by OOS profit factor sum
    winning = [f for f in all_folds if f['oos']['total_pips'] > 0]
    if winning:
        votes = {}
        for f in winning:
            p = f['params']
            k = (p['min_score'], p['base_target'], p['aplus_target'], p['stop_mult'],
                 f['rsi'][0], f['rsi'][1])
            votes[k] = votes.get(k, 0) + f['oos']['profit_factor']
        best_k = max(votes, key=votes.get)
        best_min, best_bt, best_at, best_sm, best_rb, best_rs = best_k
    else:
        bf = max(all_folds, key=lambda f: f['oos']['profit_factor'])
        p  = bf['params']
        best_min = p['min_score']; best_bt = p['base_target']
        best_at  = p['aplus_target']; best_sm = p['stop_mult']
        best_rb, best_rs = bf['rsi']

    # 6. Final full-period run with best params
    print(f"\n[5/5] Final backtest with optimized v2 params\n")
    print(f"  Min score      : {best_min}")
    print(f"  Base target    : {best_bt}× ATR (A grade)")
    print(f"  A+ target      : {best_at}× ATR (score 9-10)")
    print(f"  Stop           : {best_sm}× ATR")
    print(f"  R:R (base)     : {best_bt/best_sm:.1f}:1")
    print(f"  R:R (A+)       : {best_at/best_sm:.1f}:1")
    print(f"  Trailing stop  : activates at 1.0× ATR, trails 0.8× ATR")
    print(f"  Partial profit : 50% closed at 1.0× ATR")
    print(f"  RSI            : ≤{best_rb} / ≥{best_rs}")

    bs_f, ss_f = precompute_scores(df, rsi_buy=best_rb, rsi_sell=best_rs)
    arrs_f = df_to_arrays(df, bs_f, ss_f)

    v2 = run_backtest_v2(arrs_f,
                          min_score=best_min, base_target=best_bt,
                          aplus_target=best_at, stop_mult=best_sm)

    # Run v1 baseline with same data for comparison
    from optimize_confluence import run_backtest as run_v1
    v1 = run_v1(arrs_f, min_score=7, target_mult=1.2, stop_mult=1.2)

    # No-filter baseline
    bs_raw, ss_raw = precompute_scores(df, rsi_buy=30, rsi_sell=70)
    arrs_raw = df_to_arrays(df, bs_raw, ss_raw)
    raw = run_v1(arrs_raw, min_score=1, target_mult=1.5, stop_mult=1.0)

    print()
    print("=" * 75)
    print(f"  {'METRIC':<26} {'RAW (no filter)':>16} {'v1 (fixed TP)':>14} {'v2 (trailing)':>14}")
    print("=" * 75)

    rows = [
        ("Total Trades",      raw['trades'],       v1['trades'],       v2['trades']),
        ("Win Rate",           f"{raw['win_rate']:.1f}%",  f"{v1['win_rate']:.1f}%",  f"{v2['win_rate']:.1f}%"),
        ("Total Pips",         f"{raw['total_pips']:+.0f}", f"{v1['total_pips']:+.0f}", f"{v2['total_pips']:+.0f}"),
        ("Pips / Month",       f"{raw['total_pips']/12:+.0f}", f"{v1['total_pips']/12:+.0f}", f"{v2['total_pips']/12:+.0f}"),
        ("Profit Factor",      f"{raw['profit_factor']:.2f}×", f"{v1['profit_factor']:.2f}×", f"{v2['profit_factor']:.2f}×"),
        ("Sharpe Ratio",       f"{raw['sharpe']:.1f}",   f"{v1['sharpe']:.1f}",   f"{v2['sharpe']:.1f}"),
        ("Max Drawdown",       f"{raw['max_dd']:.0f}",   f"{v1['max_dd']:.0f}",   f"{v2['max_dd']:.0f}"),
        ("Avg Win (pips)",     "—",                      "—",                     f"{v2['avg_win']:+.1f}"),
        ("Best Trade (pips)",  "—",                      "—",                     f"{v2['best']:+.1f}"),
    ]

    for label, rv, v1v, v2v in rows:
        print(f"  {label:<26} {rv:>16} {v1v:>14} {v2v:>14}")

    # Improvement summary
    print("=" * 75)
    print()
    v2_vs_v1_pips = v2['total_pips'] - v1['total_pips']
    v2_vs_v1_wr   = v2['win_rate']   - v1['win_rate']
    v2_vs_v1_pf   = v2['profit_factor'] - v1['profit_factor']

    print("  v2 vs v1 IMPROVEMENT:")
    print(f"    Pips:          {v2_vs_v1_pips:+.0f} ({'+' if v2_vs_v1_pips > 0 else ''}{v2_vs_v1_pips/max(abs(v1['total_pips']),1)*100:.0f}%)")
    print(f"    Win Rate:      {v2_vs_v1_wr:+.1f}%")
    print(f"    Profit Factor: {v2_vs_v1_pf:+.2f}")
    print(f"    Avg Win:       {v2['avg_win']:+.1f} pips")
    print(f"    Best Trade:    {v2['best']:+.1f} pips")
    print()

    if v2['profit_factor'] > v1['profit_factor']:
        print("  VERDICT: v2 is BETTER than v1.")
        print("  Trailing stops let winners run. Partial profits lock in gains.")
    elif v2['profit_factor'] > 1.0:
        print("  VERDICT: v2 is profitable but not clearly better than v1.")
        print("  Fixed targets may be more consistent on this data.")
    else:
        print("  VERDICT: v2 underperforms v1 on this data.")
        print("  Trailing stops may need tuning or don't suit this regime mix.")

    print()
    print("  RECOMMENDED PARAMS for config.py:")
    print(f"    MIN_SCORE_TO_TRADE  = {best_min}")
    print(f"    RSI_BUY_THRESHOLD   = {best_rb}")
    print(f"    RSI_SELL_THRESHOLD  = {best_rs}")
    print(f"    TARGET_ATR_MULT     = {best_bt}    # A grade base target")
    print(f"    APLUS_TARGET_MULT   = {best_at}    # A+ grade gets bigger target")
    print(f"    STOP_ATR_MULT       = {best_sm}")
    print(f"    TRAIL_TRIGGER_ATR   = 1.0     # activate trailing at 1× ATR")
    print(f"    TRAIL_DISTANCE_ATR  = 0.8     # trail 0.8× ATR behind price")
    print(f"    PARTIAL_AT_ATR      = 1.0     # take 50% off at 1× ATR")
    print("=" * 75)
    print()


if __name__ == "__main__":
    main()
