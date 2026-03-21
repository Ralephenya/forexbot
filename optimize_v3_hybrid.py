"""
Confluence Optimizer v3 — HYBRID (best of v1 + v2)
====================================================
  A  trades (score 7-8) → Fixed target 1.5× ATR, stop 1.2× ATR (v1 consistency)
  A+ trades (score 9-10) → 3× ATR target, trailing stop, partial profit (v2 big wins)

Same GARCH data, same walk-forward.

Run: python optimize_v3_hybrid.py
"""

import numpy as np
from itertools import product

from optimize_confluence import (
    generate_garch_data, add_indicators, precompute_scores, df_to_arrays,
    run_backtest as run_v1
)


def run_backtest_v3(arrs, min_score=7, a_target=1.5, aplus_target=3.0,
                    stop_mult=1.2, trail_trigger=1.0, trail_dist=0.8,
                    partial_at=1.0, partial_pct=0.5,
                    spread_pips=1.2, session_start=8, session_end=17):
    """
    Hybrid: A-grade = fixed target. A+-grade = trailing stop + partial profit.
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
    d = 1
    ep = tp = sp = 0.0
    atr_entry = 0.0
    is_aplus  = False
    trail_on  = False
    partial_done = False
    pos_size  = 1.0

    a_wins = a_total = ap_wins = ap_total = 0
    a_pips = ap_pips = 0.0

    for i in range(220, n):
        hr = hour[i]
        c, h, l = close[i], high[i], low[i]

        if in_trade:
            fav = h if d == 1 else l
            move = (fav - ep) * d

            # ── Target hit ───────────────────────────────────────────
            target_hit = (d == 1 and h >= tp) or (d == -1 and l <= tp)
            stop_hit   = (d == 1 and l <= sp) or (d == -1 and h >= sp)

            if target_hit:
                if d == 1:
                    pips = (tp - ep) * 10000 * pos_size - spread_pips * pos_size
                else:
                    pips = (ep - tp) * 10000 * pos_size - spread_pips * pos_size
                pips_list.append(pips)
                if is_aplus: ap_pips += pips; ap_total += 1; ap_wins += 1 if pips > 0 else 0
                else:        a_pips  += pips; a_total  += 1; a_wins  += 1 if pips > 0 else 0
                in_trade = False; continue

            if stop_hit:
                if d == 1:
                    pips = (sp - ep) * 10000 * pos_size - spread_pips * pos_size
                else:
                    pips = (ep - sp) * 10000 * pos_size - spread_pips * pos_size
                pips_list.append(pips)
                if is_aplus: ap_pips += pips; ap_total += 1; ap_wins += 1 if pips > 0 else 0
                else:        a_pips  += pips; a_total  += 1; a_wins  += 1 if pips > 0 else 0
                in_trade = False; continue

            # ── A+ only: partial profit + trailing ───────────────────
            if is_aplus:
                if not partial_done and move >= partial_at * atr_entry:
                    ppips = (fav - ep) * d * 10000 * partial_pct - spread_pips * partial_pct
                    pips_list.append(ppips)
                    ap_pips += ppips
                    pos_size -= partial_pct
                    partial_done = True
                    sp = ep + d * spread_pips / 10000

                if not trail_on and move >= trail_trigger * atr_entry:
                    trail_on = True
                    sp = ep + d * spread_pips / 10000

                if trail_on:
                    new_sp = fav - d * trail_dist * atr_entry
                    if d == 1: sp = max(sp, new_sp)
                    else:      sp = min(sp, new_sp)

            # ── Session close ────────────────────────────────────────
            if hr >= session_end:
                pips = (c - ep) * 10000 * d * pos_size - spread_pips * pos_size
                pips_list.append(pips)
                if is_aplus: ap_pips += pips; ap_total += 1; ap_wins += 1 if pips > 0 else 0
                else:        a_pips  += pips; a_total  += 1; a_wins  += 1 if pips > 0 else 0
                in_trade = False
            continue

        # ── ENTRY ────────────────────────────────────────────────────
        if hr < session_start or hr >= session_end:
            continue

        bs, ss = b_sc[i], s_sc[i]
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

        is_aplus = (score >= 9)

        # A-grade: fixed target. A+: bigger target with trailing
        t_mult = aplus_target if is_aplus else a_target

        ep = c + d * half_s
        tp = ep + d * atr_pips * t_mult / 10000
        sp = ep - d * atr_pips * stop_mult / 10000

        in_trade = True
        trail_on = False
        partial_done = False
        pos_size = 1.0

    if not pips_list:
        return {'trades': 0, 'win_rate': 0.0, 'total_pips': 0.0,
                'profit_factor': 0.0, 'max_dd': 0.0, 'sharpe': 0.0,
                'calmar': 0.0, 'avg_win': 0.0, 'best': 0.0,
                'a_trades': 0, 'a_pips': 0, 'aplus_trades': 0, 'aplus_pips': 0}

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
        'best':          float(arr.max()),
        'a_trades':      a_total,
        'a_pips':        round(a_pips, 1),
        'a_wr':          round(a_wins / max(a_total, 1) * 100, 1),
        'aplus_trades':  ap_total,
        'aplus_pips':    round(ap_pips, 1),
        'aplus_wr':      round(ap_wins / max(ap_total, 1) * 100, 1),
    }


def walk_forward_v3(df, buy_score, sell_score, param_grid):
    total      = len(df)
    fold_size  = total // 12
    train_size = fold_size * 5

    folds = []
    for fold in range(4):
        ts = fold * fold_size
        te = ts + train_size
        oe = te + fold_size
        if oe > total: break

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
            r = run_backtest_v3(arrs_tr, **p)
            if r['trades'] >= 5 and r['profit_factor'] > best_pf:
                best_pf, best_p = r['profit_factor'], p

        if best_p is None: continue

        oos = run_backtest_v3(arrs_te, **best_p)
        folds.append({'fold': fold + 1, 'params': best_p, 'oos': oos})

    return folds


def main():
    print()
    print("=" * 75)
    print("  CONFLUENCE OPTIMIZER v3 — HYBRID")
    print("  A grade = fixed target  |  A+ grade = trailing + partial profit")
    print("  EUR/USD · 15-min · 12 months · GARCH + Regime Switching")
    print("=" * 75)

    print("\n[1/5] Generating data...")
    df = generate_garch_data(months=12, seed=42)
    df = add_indicators(df)
    df = df.dropna().reset_index(drop=True)
    print(f"      {len(df):,} candles")

    print("[2/5] Pre-computing scores...")
    rsi_combos = [(28, 72), (30, 70)]
    score_cache = {}
    for rb, rs in rsi_combos:
        bs, ss = precompute_scores(df, rsi_buy=rb, rsi_sell=rs)
        score_cache[(rb, rs)] = (bs, ss)

    param_grid = []
    for min_s, at, apt, sm in product(
        [6, 7],                    # min score
        [1.2, 1.5, 1.8],          # A-grade target
        [2.5, 3.0, 3.5],          # A+ target
        [1.0, 1.2],               # stop
    ):
        param_grid.append({
            'min_score':    min_s,
            'a_target':     at,
            'aplus_target': apt,
            'stop_mult':    sm,
        })

    print(f"[3/5] Grid: {len(param_grid)} combos × 4 folds × {len(rsi_combos)} RSI")
    print("      Running...")

    all_folds = []
    for (rb, rs) in rsi_combos:
        bs, ss = score_cache[(rb, rs)]
        folds = walk_forward_v3(df, bs, ss, param_grid)
        for f in folds:
            f['rsi'] = (rb, rs)
        all_folds.extend(folds)

    if not all_folds:
        print("  No folds."); return

    print(f"\n[4/5] OOS Results ({len(all_folds)} folds)\n")
    print(f"  {'Fold':<5} {'Min':<4} {'A×':<5} {'A+×':<5} {'SL×':<5} "
          f"{'Tr':<5} {'Win%':<7} {'Pips':<10} {'PF':<6} {'Best'}")
    print("  " + "-" * 65)

    oos_pips = []
    for f in all_folds:
        p, o = f['params'], f['oos']
        oos_pips.append(o['total_pips'])
        if o['trades'] == 0:
            print(f"  {f['fold']:<5} — no trades"); continue
        print(f"  {f['fold']:<5} {p['min_score']:<4} {p['a_target']:<5} "
              f"{p['aplus_target']:<5} {p['stop_mult']:<5} "
              f"{o['trades']:<5} {o['win_rate']:.1f}%  {o['total_pips']:>+9.1f} "
              f"{o['profit_factor']:.2f}   {o['best']:>+.1f}")

    avg = np.mean(oos_pips)
    pos = sum(1 for p in oos_pips if p > 0)
    print(f"\n  OOS avg pips: {avg:+.1f} | Profitable folds: {pos}/{len(all_folds)}")

    # Find best
    winning = [f for f in all_folds if f['oos']['total_pips'] > 0]
    if winning:
        votes = {}
        for f in winning:
            p = f['params']
            k = (p['min_score'], p['a_target'], p['aplus_target'],
                 p['stop_mult'], f['rsi'][0], f['rsi'][1])
            votes[k] = votes.get(k, 0) + f['oos']['profit_factor']
        bk = max(votes, key=votes.get)
        bmin, bat, bapt, bsm, brb, brs = bk
    else:
        bf = max(all_folds, key=lambda f: f['oos']['profit_factor'])
        p = bf['params']
        bmin, bat, bapt, bsm = p['min_score'], p['a_target'], p['aplus_target'], p['stop_mult']
        brb, brs = bf['rsi']

    print(f"\n[5/5] Final full-period backtest\n")
    print(f"  Best params:")
    print(f"    A grade  : fixed {bat}× ATR target, {bsm}× ATR stop (R:R {bat/bsm:.1f}:1)")
    print(f"    A+ grade : {bapt}× ATR target + trailing stop (R:R {bapt/bsm:.1f}:1)")
    print(f"    RSI      : ≤{brb} / ≥{brs}")
    print(f"    Min score: {bmin}/10")

    bs_f, ss_f = precompute_scores(df, rsi_buy=brb, rsi_sell=brs)
    arrs_f = df_to_arrays(df, bs_f, ss_f)

    v3 = run_backtest_v3(arrs_f, min_score=bmin, a_target=bat,
                          aplus_target=bapt, stop_mult=bsm)
    v1 = run_v1(arrs_f, min_score=7, target_mult=1.2, stop_mult=1.2)

    bs_raw, ss_raw = precompute_scores(df, rsi_buy=30, rsi_sell=70)
    arrs_raw = df_to_arrays(df, bs_raw, ss_raw)
    raw = run_v1(arrs_raw, min_score=1, target_mult=1.5, stop_mult=1.0)

    print()
    print("=" * 75)
    print(f"  {'METRIC':<26} {'RAW (no filt)':>14} {'v1 (fixed)':>12} {'v3 (hybrid)':>14}")
    print("=" * 75)

    rows = [
        ("Total Trades",      f"{raw['trades']}",  f"{v1['trades']}",  f"{v3['trades']}"),
        ("Win Rate",           f"{raw['win_rate']:.1f}%",  f"{v1['win_rate']:.1f}%",  f"{v3['win_rate']:.1f}%"),
        ("Total Pips (12m)",   f"{raw['total_pips']:+.0f}", f"{v1['total_pips']:+.0f}", f"{v3['total_pips']:+.0f}"),
        ("Pips / Month",       f"{raw['total_pips']/12:+.0f}", f"{v1['total_pips']/12:+.0f}", f"{v3['total_pips']/12:+.0f}"),
        ("Profit Factor",      f"{raw['profit_factor']:.2f}×", f"{v1['profit_factor']:.2f}×", f"{v3['profit_factor']:.2f}×"),
        ("Sharpe Ratio",       f"{raw['sharpe']:.1f}",   f"{v1['sharpe']:.1f}",   f"{v3['sharpe']:.1f}"),
        ("Max Drawdown",       f"{raw['max_dd']:.0f}",   f"{v1['max_dd']:.0f}",   f"{v3['max_dd']:.0f}"),
        ("Avg Win",            "—",                      "—",                     f"{v3['avg_win']:+.1f} pips"),
        ("Best Single Trade",  "—",                      "—",                     f"{v3['best']:+.1f} pips"),
    ]

    for label, rv, v1v, v3v in rows:
        improve = ""
        if 'v3' in v3v and v3v > v1v:
            improve = " ▲"
        print(f"  {label:<26} {rv:>14} {v1v:>12} {v3v:>14}")

    # A vs A+ breakdown
    print()
    print("  TRADE BREAKDOWN BY GRADE:")
    print(f"    A  trades:  {v3['a_trades']:>4} trades | {v3['a_wr']:.1f}% win | {v3['a_pips']:>+8.1f} pips")
    print(f"    A+ trades:  {v3['aplus_trades']:>4} trades | {v3['aplus_wr']:.1f}% win | {v3['aplus_pips']:>+8.1f} pips")

    print()
    print("=" * 75)

    v3_vs_v1 = v3['total_pips'] - v1['total_pips']
    pct = v3_vs_v1 / max(abs(v1['total_pips']), 1) * 100

    if v3['total_pips'] > v1['total_pips'] and v3['profit_factor'] >= v1['profit_factor']:
        print(f"  v3 BEATS v1 by {v3_vs_v1:+.0f} pips ({pct:+.0f}%)")
        print(f"  The hybrid approach WORKS:")
        print(f"    - A grades: consistent small wins with fixed targets")
        print(f"    - A+ grades: monster trades with trailing stops")
        print(f"  THIS IS THE PRODUCTION STRATEGY.")
    elif v3['profit_factor'] > 1.0:
        print(f"  v3 is profitable (PF {v3['profit_factor']:.2f}×) but v1 more consistent")
        print(f"  v3 vs v1: {v3_vs_v1:+.0f} pips ({pct:+.0f}%)")
        if v3['best'] > 100:
            print(f"  v3 catches bigger moves ({v3['best']:+.1f} pips best trade)")
            print(f"  Consider v3 if you want bigger individual wins")
    else:
        print(f"  Hybrid underperforms on this data. Stick with v1.")

    print()
    print(f"  FINAL RECOMMENDATION:")
    print(f"    MIN_SCORE_TO_TRADE  = {bmin}")
    print(f"    RSI_BUY_THRESHOLD   = {brb}")
    print(f"    RSI_SELL_THRESHOLD  = {brs}")
    print(f"    A_TARGET_ATR_MULT   = {bat}")
    print(f"    APLUS_TARGET_MULT   = {bapt}")
    print(f"    STOP_ATR_MULT       = {bsm}")
    print(f"    TRAIL_TRIGGER_ATR   = 1.0")
    print(f"    TRAIL_DISTANCE_ATR  = 0.8")
    print(f"    PARTIAL_AT_ATR      = 1.0")
    print(f"    PARTIAL_PCT         = 0.5")
    print("=" * 75)
    print()


if __name__ == "__main__":
    main()
