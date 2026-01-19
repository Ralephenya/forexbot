# Strategy B News Filter Test Results

## Test Period: June-December 2024 (7 months)
## Strategy: Regime-Switching System (Strategy B) with News Filter
## Pair: EUR/USD 15-Minute

---

## ❌ HYPOTHESIS REJECTED

**Expected:** Avoiding major news events improves consistency and win rate  
**Actual:** News filter REDUCED performance across all metrics

---

## MAJOR NEWS EVENTS FILTERED

### Events Calendar (June-December 2024)

- **NFP (Non-Farm Payrolls):** 7 events (first Friday of each month)
- **FOMC Meetings:** 5 events (Federal Reserve decisions)
- **ECB Decisions:** 5 events (European Central Bank)
- **US CPI:** 7 events (inflation data)
- **US GDP:** 5 events (quarterly releases)
- **Central Bank Speeches:** 9 events (ECB/Fed press conferences)

**Total Events:** 38 major news releases

### Filter Rules Applied

- **1 hour BEFORE** major news → Filtered out
- **2 hours AFTER** major news → Filtered out
- **411 candles filtered** (2.8% of total data)

---

## RESULTS SUMMARY

| Version | Trades | Win Rate | Total P&L | Avg Pips | Max Drawdown | Sharpe Ratio | Profit Factor |
|---------|--------|----------|-----------|----------|--------------|--------------|---------------|
| **WITHOUT News Filter** | 310 | 43.87% | **$0.00** | +0.00 | -$1.20 | 0.00 | 1.00 |
| **WITH News Filter** | 296 | 41.89% | **-$0.67** | -0.23 | -$1.27 | -0.35 | 0.95 |

---

## KEY FINDINGS

### 1. **Profitability**
- **WITHOUT News Filter:** $0.00 (break-even)
- **WITH News Filter:** -$0.67 (loss)
- **Difference:** -$0.67 (news filter reduced profitability)

### 2. **Win Rate**
- **WITHOUT News Filter:** 43.87%
- **WITH News Filter:** 41.89%
- **Difference:** -1.98% (news filter reduced win rate)

### 3. **Max Drawdown**
- **WITHOUT News Filter:** -$1.20
- **WITH News Filter:** -$1.27
- **Difference:** +$0.07 worse (news filter increased drawdown)

### 4. **Trade Frequency**
- **WITHOUT News Filter:** 310 trades
- **WITH News Filter:** 296 trades
- **Difference:** -14 trades (-4.5% fewer trades)

---

## SUCCESS CRITERIA EVALUATION

| Criteria | Target | WITH News Filter | Status |
|----------|--------|------------------|--------|
| Win Rate > 47% | Higher than baseline | 41.89% | ❌ **FAILED** |
| Total P&L > $2.00 | Higher or similar | -$0.67 | ❌ **FAILED** |
| Lower Drawdown | More consistent | -$1.27 (worse) | ❌ **FAILED** |

**All criteria FAILED.**

---

## WHY NEWS FILTER FAILED

### 1. **Filtered Out Profitable Trades**
- News events can create volatility, but Strategy B's adaptive targets may actually benefit from increased volatility
- The filter removed 14 potential trades, some of which may have been profitable

### 2. **Reduced Win Rate**
- Win rate decreased from 43.87% to 41.89% (-1.98%)
- Filtered trades might have been higher quality signals

### 3. **Lower Profitability**
- Lost $0.67 vs break-even ($0.00)
- News filter reduced overall profitability

### 4. **Increased Drawdown**
- Drawdown increased from -$1.20 to -$1.27
- Less diversification in trade timing = more concentrated risk

### 5. **Negative Sharpe Ratio**
- Sharpe ratio: -0.35 (vs 0.00 for baseline)
- Risk-adjusted returns worsened significantly

---

## ANALYSIS: Why News Filter Doesn't Help Strategy B

### Strategy B's Adaptive Nature

Strategy B uses **adaptive targets based on ATR**:
- **High volatility (mean reversion):** 1.5x ATR target
- **Low volatility (breakout):** 2.0x ATR target

### News Events Create Volatility

- Major news releases cause **spikes in volatility**
- Strategy B's adaptive targets **adjust to volatility**
- Filtering out news periods may remove **opportunities** where adaptive targets excel

### Time Filtering Already in Place

Strategy B already filters by:
- **Optimal hours:** 9, 10, 12, 14 UTC
- **Avoid hours:** 13, 16 UTC

Many news events occur during optimal trading hours, so the news filter may be removing good trading opportunities.

---

## RECOMMENDATION

### ❌ **DO NOT USE NEWS FILTER**

**Reasons:**
1. **Reduced profitability:** -$0.67 vs $0.00 (lost money)
2. **Lower win rate:** 41.89% vs 43.87% (-1.98%)
3. **Increased drawdown:** -$1.27 vs -$1.20
4. **Negative Sharpe ratio:** -0.35 (poor risk-adjusted returns)
5. **Fewer trading opportunities:** 296 vs 310 trades (-4.5%)

### ✅ **Stick with Strategy B WITHOUT News Filter**

Strategy B's adaptive targets are designed to handle volatility, including news-driven volatility. The time-based filtering (optimal hours) is sufficient.

---

## ALTERNATIVE APPROACHES

If you want to manage news risk:

1. **Reduce position size** around major news (instead of avoiding trades)
2. **Widen stops** during high-impact news (let Strategy B's adaptive stops handle it)
3. **Monitor news calendar** but don't filter - just be aware
4. **Test different filter windows** (e.g., 30 min before, 1 hour after) - though results suggest this won't help

---

## CONCLUSION

### Hypothesis: REJECTED ❌

**News filter does NOT improve Strategy B performance:**

- **Profitability:** Reduced from $0.00 to -$0.67
- **Win Rate:** Reduced from 43.87% to 41.89%
- **Drawdown:** Increased from -$1.20 to -$1.27
- **Sharpe Ratio:** Negative (-0.35)

**Strategy B's adaptive targets are designed to handle volatility, including news-driven volatility. Additional news filtering is counterproductive.**

---

## Files Generated

- News events calendar: `news_filter.py` (38 events)
- Results WITH filter: `results/backtest_results_strategy_b_with_news_filter.csv`
- Results WITHOUT filter: `results/backtest_results_strategy_b_no_news_filter.csv`
- Comparison: `results/quant_analysis/news_filter_comparison.csv`























