# AUD/USD Extended Hours Test - Results Summary

## Test Period
- **Data:** 60 days (yfinance limit - quick test)
- **Timeframe:** 15-minute candles
- **Pair:** AUD/USD
- **Baseline:** EUR/USD 15-minute (+$2.11, 46.19% win rate, 197 trades)

---

## ❌ HYPOTHESIS REJECTED

**Hypothesis:** AUD/USD + Sydney session = Extended trading hours = More opportunities = Higher profits

**Actual Result:** All AUD/USD configurations LOST money and underperformed EUR/USD significantly.

---

## Results Summary

| Configuration | Trades | Win Rate | Total P&L | Max Drawdown | Sharpe Ratio |
|---------------|--------|----------|-----------|--------------|--------------|
| **EUR/USD Baseline (London)** | 197 | **46.19%** | **+$2.11** | -$0.61 | **2.05** |
| AUD/USD Sydney Session | 335 | 25.67% | **-$2.82** | -$2.91 | -3.67 |
| AUD/USD London Session | 291 | 25.77% | **-$2.07** | -$1.87 | -2.69 |
| AUD/USD Combined Sessions | 618 | 25.73% | **-$4.83** | -$4.83 | -3.17 |

---

## Key Findings

### 1. **Profitability**
- **EUR/USD Baseline:** +$2.11 ✅
- **AUD/USD Sydney:** -$2.82 ❌ (-$4.93 worse)
- **AUD/USD London:** -$2.07 ❌ (-$4.18 worse)
- **AUD/USD Combined:** -$4.83 ❌ (-$6.94 worse)

### 2. **Win Rate**
- **EUR/USD Baseline:** 46.19% ✅
- **AUD/USD Sydney:** 25.67% ❌ (-20.52% worse)
- **AUD/USD London:** 25.77% ❌ (-20.42% worse)
- **AUD/USD Combined:** 25.73% ❌ (-20.46% worse)

### 3. **Trade Frequency**
- **EUR/USD Baseline:** 197 trades
- **AUD/USD Sydney:** 335 trades (+138, +70%)
- **AUD/USD London:** 291 trades (+94, +48%)
- **AUD/USD Combined:** 618 trades (+421, +214%)

**More trades, but ALL are losing trades!**

### 4. **Risk-Adjusted Returns (Sharpe Ratio)**
- **EUR/USD Baseline:** 2.05 ✅ (positive, good)
- **AUD/USD Sydney:** -3.67 ❌ (negative, terrible)
- **AUD/USD London:** -2.69 ❌ (negative, terrible)
- **AUD/USD Combined:** -3.17 ❌ (negative, terrible)

---

## Hour-by-Hour Analysis (Phase 1)

**Top Hours by Signal Count:**
1. Hour 20 (New York): 222 signals
2. Hour 21 (New York): 219 signals
3. Hour 19 (New York): 209 signals
4. Hour 22 (Sydney): 206 signals
5. Hour 0 (Sydney): 182 signals

**Summary by Session:**
- **Sydney Session:** 1,265 total signals (highest)
- **New York Session:** 938 signals
- **Tokyo Session:** 579 signals
- **London/New York Overlap:** 311 signals
- **Sydney/Tokyo Overlap:** 220 signals

**Finding:** Sydney session has the MOST signals, but the LOWEST win rate (25.67%).

---

## Why AUD/USD Failed

### 1. **Strategy B Not Suitable for AUD/USD**
- Strategy B was optimized for EUR/USD
- AUD/USD has different volatility characteristics
- Mean reversion/breakout logic may not work the same way

### 2. **Lower Win Rate Across All Sessions**
- All AUD/USD configurations had ~25% win rate
- EUR/USD had 46% win rate
- This suggests AUD/USD market structure doesn't match Strategy B's assumptions

### 3. **More Trades = More Losses**
- Combined sessions generated 618 trades (3x EUR/USD)
- But win rate was only 25%, so more trades = more losses
- Extended hours did NOT provide better opportunities

### 4. **Higher Volatility Doesn't Mean Better**
- AUD/USD is more volatile than EUR/USD
- But Strategy B's adaptive targets may not scale correctly
- Higher volatility = larger losses when trades fail

---

## Success Criteria Evaluation

| Criteria | Target | Best AUD/USD Result | Status |
|----------|--------|---------------------|--------|
| Total P&L > $2.11 | Beat EUR/USD | -$2.07 (London Session) | ❌ **FAILED** |
| Win Rate > 46% | Beat or match EUR/USD | 25.77% (London Session) | ❌ **FAILED** |
| Extended hours = More opportunities | More trades | 618 trades (Combined) | ⚠️ More trades, but all losing |
| Risk-Adjusted Returns | Sharpe > 2.0 | -2.69 (London Session) | ❌ **FAILED** |

**All criteria FAILED.**

---

## Recommendation

### ❌ **DO NOT TRADE AUD/USD WITH STRATEGY B**

**Reasons:**
1. **All configurations lost money:** -$2.07 to -$4.83
2. **Win rate too low:** ~25% vs 46% for EUR/USD
3. **Negative Sharpe ratios:** All configurations have terrible risk-adjusted returns
4. **Extended hours = More losses:** More trades, but all unprofitable

### ✅ **Stick with EUR/USD**

EUR/USD with Strategy B on London session remains the best option:
- **+$2.11 profit** vs losses on AUD/USD
- **46.19% win rate** vs 25% on AUD/USD
- **Sharpe ratio 2.05** vs negative on AUD/USD
- **197 trades** (manageable) vs 618 trades (all losing)

---

## Alternative Approaches (If You Want to Trade AUD/USD)

1. **Optimize Strategy B for AUD/USD:**
   - Re-test with different RSI thresholds
   - Adjust ATR multipliers
   - Test different time filters
   - May require extensive optimization

2. **Use a Different Strategy:**
   - Strategy B may not be suitable for AUD/USD
   - Consider trend-following strategies
   - Consider breakout strategies with different parameters

3. **Trade Different Sessions:**
   - Test if other sessions (Tokyo, New York) work better
   - May require session-specific optimization

4. **Accept Lower Performance:**
   - If you MUST trade AUD/USD, expect lower win rates
   - May need wider stops/targets
   - May need different position sizing

---

## Conclusion

### Hypothesis: REJECTED ❌

**Extended trading hours with AUD/USD do NOT improve performance:**

- **Profitability:** All AUD/USD configurations lost money (-$2.07 to -$4.83)
- **Win Rate:** ~25% vs 46% for EUR/USD (half the win rate)
- **Risk-Adjusted Returns:** Negative Sharpe ratios (terrible)
- **Extended Hours:** More trades, but all losing trades

**Strategy B is NOT suitable for AUD/USD. Extended hours provide more opportunities, but all are bad opportunities.**

**Recommendation: Stick with EUR/USD on London session.**

---

## Notes

1. **Test Limitations:** This test used 60 days of data (yfinance limit). Full 7-month test with HistData.com data may yield different results, but current results are strongly negative.

2. **Strategy-Specific:** These results are specific to Strategy B. A different strategy optimized for AUD/USD might perform better.

3. **Market Conditions:** Results may vary in different market conditions. Current results show consistent losses across all configurations.

---

**Status:** Test Complete - Hypothesis Rejected





















