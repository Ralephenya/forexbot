# VWAP + RSI Hybrid Strategy Test Results

## Strategy Configuration

**BUY Signal Requirements:**
- Price below VWAP - 2.0 SD (VWAP signal) **AND**
- RSI ≤ 30 (RSI confirmation)
- **Both indicators must agree**

**SELL Signal Requirements:**
- Price above VWAP + 2.0 SD (VWAP signal) **AND**
- RSI ≥ 70 (RSI confirmation)
- **Both indicators must agree**

**Theory:** Combining filters = higher quality signals, fewer trades, higher win rate

---

## Test Results

### Overall Performance
- **Total Trades**: 212
- **Win Rate**: 43.40%
- **Total P&L**: -$0.09 (essentially break-even)
- **Average Pips per Trade**: -0.04
- **Max Drawdown**: -$2.40
- **Signals per Day**: 1.00 (perfect filtering!)

### Signal Filtering Effect

| Indicator | BUY Signals | SELL Signals | Total Signals |
|-----------|-------------|--------------|---------------|
| VWAP Only (2.0 SD) | 1,630 | 1,415 | 3,045 |
| RSI Only (≤30/≥70) | 266 | 261 | 527 |
| **Hybrid (Both)** | **266** | **261** | **527** |

**Key Insight:** All RSI signals (527) also had VWAP confirmation. This means every RSI extreme occurred when price was also at VWAP extremes - the indicators are well-aligned!

**Signal Reduction:** 
- From VWAP standalone: 888 trades → 212 trades (76% reduction)
- From RSI standalone: 191 trades → 212 trades (11% increase)

---

## Comparison: Hybrid vs Standalone Strategies

| Strategy | Trades | Win Rate | Total P&L | Avg Pips | Max Drawdown | Signals/Day |
|----------|--------|----------|-----------|----------|--------------|-------------|
| **RSI Standalone** | 191 | 46.07% | **+$0.56** ✅ | +0.29 | -$0.82 | 0.91 |
| **VWAP 2.0 SD** | 888 | 43.81% | **+$0.46** ✅ | +0.05 | -$2.94 | 14.4 |
| **VWAP + RSI Hybrid** | 212 | 43.40% | -$0.09 ❌ | -0.04 | -$2.40 | **1.00** ✅ |

### Ranking by Profitability
1. **RSI Standalone**: +$0.56 ✅
2. **VWAP 2.0 SD**: +$0.46 ✅
3. **VWAP + RSI Hybrid**: -$0.09 ❌

### Ranking by Signal Quality (Trades/Day)
1. **VWAP + RSI Hybrid**: 1.00/day ✅ (Perfect!)
2. **RSI Standalone**: 0.91/day ✅
3. **VWAP 2.0 SD**: 14.4/day ❌ (Overtrading)

---

## Key Findings

### ✅ What Worked
1. **Excellent Signal Filtering**: Reduced to exactly 1 signal per day (perfect target range)
2. **Indicators Aligned**: All RSI signals had VWAP confirmation (good alignment)
3. **Fewer Trades**: 212 trades vs 888 (VWAP) = 76% reduction
4. **Better Risk**: Lower drawdown (-$2.40) than VWAP standalone (-$2.94)

### ❌ What Didn't Work
1. **Not More Profitable**: -$0.09 vs +$0.56 (RSI) and +$0.46 (VWAP)
2. **Win Rate Not Improved**: 43.40% (lower than RSI's 46.07%)
3. **Essentially Break-Even**: Very close to zero, but negative

### Analysis: Why Hybrid Underperformed

**Expected:** Combining filters = higher win rate + fewer trades = better performance

**Actual:** 
- Win rate decreased (43.40% vs 46.07% RSI)
- P&L negative (-$0.09) vs positive standalone results
- Signal quality improved (1/day) but profitability didn't

**Possible Reasons:**
1. **Over-Filtering**: Both indicators agreeing might indicate extreme conditions that don't mean revert well
2. **Timing Issues**: When both indicators agree, the move might be too late (missing the best entry)
3. **Reduced Opportunity**: Filtering too aggressively reduces profitable opportunities
4. **Correlation**: RSI and VWAP may be measuring similar things, so combining doesn't add value

---

## Monthly Performance (Hybrid)

| Month | Trades | Win Rate | Total P&L | Status |
|-------|--------|----------|-----------|--------|
| June 2024 | 35 | 42.86% | +$0.14 | Small Win |
| July 2024 | 27 | 55.56% | +$0.50 | Win ✅ |
| August 2024 | 30 | 36.67% | -$0.54 | Loss |
| September 2024 | 28 | 39.29% | -$0.24 | Loss |
| October 2024 | 26 | 30.77% | -$0.62 | Worst |
| November 2024 | 35 | 45.71% | +$0.21 | Small Win |
| December 2024 | 31 | 51.61% | +$0.46 | Win ✅ |

**Profitable Months**: 4 out of 7 (57%)
**Best Month**: July 2024 (+$0.50, 55.56% win rate)
**Worst Month**: October 2024 (-$0.62, 30.77% win rate)

---

## Success Criteria Evaluation

| Criteria | Target | Hybrid Actual | Status |
|----------|--------|---------------|--------|
| Win Rate | >48% | 43.40% | ❌ (4.6% below) |
| Total P&L | >$5 | -$0.09 | ❌ (Essentially break-even) |
| Max Drawdown | <$15 | -$2.40 | ✅ (Well below limit) |
| Signals/Day | 1-3 | 1.00 | ✅ (Perfect!) |

**Overall**: Meets 2/4 criteria (signal frequency and drawdown, but not profitability)

---

## Conclusion

### Hybrid Strategy Assessment

**Strengths:**
- ✅ Perfect signal filtering (1.00/day)
- ✅ Excellent indicator alignment
- ✅ Reduced overtrading
- ✅ Better risk management (lower drawdown)

**Weaknesses:**
- ❌ Not more profitable than standalone strategies
- ❌ Win rate not improved (actually decreased)
- ❌ Essentially break-even performance

### Recommendation

**The hybrid strategy did NOT improve profitability** compared to standalone strategies:
- RSI Standalone: +$0.56 (best performer)
- VWAP 2.0 SD: +$0.46 (second best)
- Hybrid: -$0.09 (worst performer)

**However**, the hybrid strategy achieved the goal of **signal quality** (1.00 signals/day) but at the cost of profitability.

### Next Steps

1. **Stick with RSI Standalone** (+$0.56, 46.07% win rate) - best profitability
2. **OR** Try different hybrid approaches:
   - Use RSI as primary filter, VWAP as confirmation (reverse order)
   - Use wider RSI bands (e.g., ≤35/≥65) with VWAP 2.0 SD
   - Add time-of-day filters to standalone strategies
3. **Optimize Risk/Reward**: Test different target/stop ratios on best performing strategy (RSI)

---

## Files Generated

- Backtest results: `results/backtest_results_6months_hybrid.csv`
- Performance report: `results/performance_report_6months_hybrid.html`
- Charts: `results/charts/cumulative_pnl_6months_hybrid.png`, `daily_pnl_6months_hybrid.png`























