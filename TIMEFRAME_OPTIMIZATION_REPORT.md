# Strategy B Timeframe Optimization Report
## 15-Minute vs 30-Minute vs 1-Hour Comparison

### Test Period: June-December 2024 (7 months)
### Strategy: Regime-Switching System (Strategy B)
### Pair: EUR/USD

---

## HYPOTHESIS

**30-Minute is "Goldilocks Timeframe":**
- Less noisy than 15-minute (better signal quality)
- More trades than 1-hour (more opportunities)
- Could optimize the trade-off

---

## RESULTS SUMMARY

| Timeframe | Trades | Win Rate | Total P&L | Avg Pips | Max Drawdown | Sharpe Ratio | Profit Factor | Avg Duration |
|-----------|--------|----------|-----------|----------|--------------|--------------|---------------|--------------|
| **15-Minute** | 197 | 46.19% | **+$2.11** ✅ | +1.07 | -$0.61 | **2.05** | 1.34 | 2.34 hours |
| **30-Minute** | 172 | 43.02% | **-$1.52** ❌ | -0.89 | -$1.79 | -1.22 | 0.82 | 8.56 hours |
| **1-Hour** | 140 | 47.86% | +$1.79 | +1.28 | -$1.00 | 1.72 | 1.29 | 6.99 hours |

---

## SUCCESS CRITERIA (30-Minute)

| Criteria | Target | 30-Minute Actual | Status |
|----------|--------|------------------|--------|
| Total P&L > $2.11 | Beat 15-min baseline | -$1.52 | ❌ **FAILED** |
| Win Rate > 46% | Better than 15-min | 43.02% | ❌ **FAILED** |
| Sharpe Ratio > 2.05 | Best risk-adjusted | -1.22 | ❌ **FAILED** |

**All criteria FAILED.**

---

## DETAILED ANALYSIS

### ❌ HYPOTHESIS REJECTED

**30-Minute is NOT the "Goldilocks timeframe"**

### Trade Frequency Comparison
- **15-Minute:** 197 trades (most frequent) ✅
- **30-Minute:** 172 trades (middle ground)
- **1-Hour:** 140 trades (least frequent)

### Profitability Comparison
- **15-Minute:** +$2.11 (best) ✅
- **30-Minute:** -$1.52 (worst) ❌
- **1-Hour:** +$1.79 (second best)

### Win Rate Comparison
- **1-Hour:** 47.86% (highest) ✅
- **15-Minute:** 46.19% (second)
- **30-Minute:** 43.02% (lowest) ❌

### Risk-Adjusted Returns (Sharpe Ratio)
- **15-Minute:** 2.05 (best) ✅
- **1-Hour:** 1.72 (second)
- **30-Minute:** -1.22 (negative, worst) ❌

### Trade Duration
- **15-Minute:** 2.34 hours average (fastest exits)
- **30-Minute:** 8.56 hours average (longest)
- **1-Hour:** 6.99 hours average

---

## KEY FINDINGS

### 1. **30-Minute Underperformed Significantly**
- Lost money: -$1.52 vs +$2.11 (15-min) and +$1.79 (1-hour)
- Lower win rate: 43.02% vs 46.19% (15-min) and 47.86% (1-hour)
- Negative Sharpe ratio: -1.22 (unacceptable risk-adjusted returns)

### 2. **15-Minute is Optimal**
- Best profitability: +$2.11
- Best Sharpe ratio: 2.05
- Good win rate: 46.19%
- Fastest trade duration: 2.34 hours

### 3. **1-Hour is Second Best**
- Profitable: +$1.79
- Highest win rate: 47.86%
- Good Sharpe ratio: 1.72
- Longer trade duration: 6.99 hours

### 4. **Why 30-Minute Failed**
- **Longer trade duration:** 8.56 hours average (vs 2.34 for 15-min)
  - Trades held too long = more exposure to adverse moves
  - Higher risk without higher reward
  
- **Lower win rate:** 43.02% (vs 46.19% for 15-min)
  - Signal quality degraded at 30-minute
  - Not enough "sweet spot" benefit
  
- **Negative average pips:** -0.89 (vs +1.07 for 15-min)
  - Losing trades larger than winning trades
  - Poor risk/reward ratio

---

## RECOMMENDATION

### ✅ **USE 15-MINUTE TIMEFRAME**

**Reasons:**
1. **Best profitability:** +$2.11 (vs -$1.52 for 30-min, +$1.79 for 1-hour)
2. **Best risk-adjusted returns:** Sharpe 2.05 (vs -1.22 for 30-min, 1.72 for 1-hour)
3. **Good win rate:** 46.19% (acceptable)
4. **Fastest trade duration:** 2.34 hours (less exposure time)
5. **Best profit factor:** 1.34 (vs 0.82 for 30-min, 1.29 for 1-hour)

### ❌ **DO NOT USE 30-MINUTE TIMEFRAME**

**Reasons:**
1. **Lost money:** -$1.52 (unprofitable)
2. **Negative Sharpe ratio:** -1.22 (poor risk-adjusted returns)
3. **Lowest win rate:** 43.02%
4. **Longest trade duration:** 8.56 hours (too much exposure)
5. **Negative average pips:** -0.89 (losing strategy)

### Alternative: 1-Hour Timeframe

If you prefer fewer trades:
- **Profitable:** +$1.79
- **Highest win rate:** 47.86%
- **Good Sharpe ratio:** 1.72
- **Fewer trades:** 140 (vs 197 for 15-min)

**But 15-minute is still better overall.**

---

## Files Generated

- 30-minute data: `data/eurusd_30min_6months.csv`
- 30-minute signals: `data/eurusd_30min_6months_strategy_b_signals.csv`
- 30-minute results: `results/backtest_results_strategy_b_30min.csv`
- 3-way comparison: `results/quant_analysis/timeframe_comparison_3way.csv`

