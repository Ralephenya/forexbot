# Strategy B: Timeframe Comparison Report
## 15-Minute vs 1-Hour Performance Analysis

### Test Period: June 2024 - December 2024 (7 months)
### Strategy: Regime-Switching System (Strategy B)
### Pair: EUR/USD

---

## HYPOTHESIS

**Original Hypothesis:** Larger timeframe (1-hour) = larger profits with same edge

**Result:** ❌ **HYPOTHESIS REJECTED**

---

## COMPARISON RESULTS

| Metric | 15-Minute | 1-Hour | Difference |
|--------|-----------|--------|------------|
| **Total P&L** | **+$2.11** ✅ | +$1.79 | -$0.32 (-15%) |
| **Win Rate** | 46.19% | **47.86%** ✅ | +1.67% |
| **Total Trades** | 197 | **140** ✅ | -57 (29% fewer) |
| **Avg Pips per Trade** | +1.07 | **+1.28** ✅ | +0.21 |
| **Max Drawdown** | **-$0.61** ✅ | -$1.00 | -$0.39 |
| **Sharpe Ratio** | **2.05** ✅ | 1.72 | -0.33 |
| **Profit Factor** | **1.34** ✅ | 1.29 | -0.05 |
| **Avg Duration (hours)** | 2.34 | **6.99** | +4.65 |

---

## KEY FINDINGS

### 1. PROFITABILITY
- **15-Minute wins:** +$2.11 vs +$1.79 (15% more profitable)
- However, 1-hour still profitable (+$1.79)
- Both timeframes significantly outperform baseline RSI (+$0.56)

### 2. WIN RATE
- **1-Hour wins:** 47.86% vs 46.19% (+1.67% improvement)
- Higher win rate on larger timeframe suggests better signal quality
- Fewer false signals due to less noise

### 3. TRADE FREQUENCY
- **1-Hour:** 140 trades (29% fewer than 15-minute)
- Less trading = lower transaction costs
- More selective entries = higher quality signals

### 4. RISK-ADJUSTED RETURNS
- **15-Minute wins:** Sharpe 2.05 vs 1.72
- Higher Sharpe indicates better risk-adjusted returns
- However, 1.72 is still excellent (above 1.0 threshold)

### 5. TRADE DURATION
- **1-Hour:** Average 7 hours vs 2.3 hours (15-minute)
- Longer holding periods = less active management needed
- Better for part-time traders

---

## DETAILED ANALYSIS

### Profitability Breakdown

**15-Minute Timeframe:**
- Total P&L: +$2.11
- Trades: 197
- Avg P&L per trade: +$0.011
- More trades = more opportunities to capture edge

**1-Hour Timeframe:**
- Total P&L: +$1.79
- Trades: 140
- Avg P&L per trade: +$0.013
- Higher average per trade, but fewer total trades

### Win Rate Analysis

**Why 1-Hour has Higher Win Rate:**
1. Less noise = cleaner signals
2. Longer timeframes filter out false breakouts
3. More reliable mean reversion patterns
4. Better trend identification

**Trade-off:** Higher win rate but lower total profit due to fewer trades

### Risk Management

**15-Minute:**
- Lower drawdown: -$0.61
- Better Sharpe ratio: 2.05
- More consistent returns

**1-Hour:**
- Higher drawdown: -$1.00 (but still acceptable)
- Lower Sharpe: 1.72 (still good)
- Longer trades = larger potential swings

---

## CONCLUSION

### ❌ Hypothesis Rejected

**The 1-hour timeframe does NOT produce larger profits than 15-minute.**

However, the results reveal important trade-offs:

### 15-Minute Advantages:
✅ **Higher total profit** (+$2.11 vs +$1.79)
✅ **Better Sharpe ratio** (2.05 vs 1.72)
✅ **Lower drawdown** (-$0.61 vs -$1.00)
✅ **More opportunities** (197 vs 140 trades)

### 1-Hour Advantages:
✅ **Higher win rate** (47.86% vs 46.19%)
✅ **Fewer trades** (140 vs 197) = less work
✅ **Higher avg pips per trade** (+1.28 vs +1.07)
✅ **Longer duration** = less active management

---

## RECOMMENDATION

### For Maximum Profitability: Use 15-Minute ⭐
- Best total P&L (+$2.11)
- Best Sharpe ratio (2.05)
- Lowest drawdown (-$0.61)
- More trading opportunities

### For Better Win Rate & Less Work: Use 1-Hour
- Higher win rate (47.86%)
- Fewer trades (140 vs 197)
- Better for part-time traders
- Less active management required

**Both timeframes significantly outperform the baseline RSI strategy (+$0.56), proving the pattern-based edge works across timeframes.**

---

## SCALING ANALYSIS

### Does the Edge Scale to Larger Timeframes?

**Yes and No:**

✅ **The edge DOES scale:**
- Both timeframes profitable (+$2.11 and +$1.79)
- Both significantly beat baseline (+$0.56)
- Pattern-based filtering works on both timeframes
- Higher win rate on larger timeframe (47.86% vs 46.19%)

❌ **But scaling doesn't improve total profit:**
- 15-minute: +$2.11 (higher total)
- 1-hour: +$1.79 (lower total but better win rate)

**Conclusion:** The edge exists on both timeframes, but **frequency matters**. More trades on 15-minute = more opportunities to capture the edge, resulting in higher total profit.

**However**, 1-hour provides:
- Higher win rate (quality over quantity)
- Less active management
- Better for part-time traders
- Still highly profitable (+$1.79, 220% above baseline)

---

## FILES GENERATED

- 1-hour aggregated data: `data/eurusd_1hour_6months.csv`
- Strategy B signals (1-hour): `data/eurusd_1hour_6months_strategy_b_signals.csv`
- Backtest results (1-hour): `results/backtest_results_strategy_b_1hour.csv`
- Comparison: `results/quant_analysis/timeframe_comparison.csv`























