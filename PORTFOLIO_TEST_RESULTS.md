# Multi-Pair Portfolio Test Results - Strategy B

## Test Period: June-December 2024 (7 months)
## Strategy: Regime-Switching System (Strategy B)
## Pairs: EUR/USD, GBP/USD, USD/JPY

---

## ❌ HYPOTHESIS REJECTED

**Expected:** Diversification across 3 pairs provides:
- More trading opportunities ✅ (815 vs 197 trades)
- Risk spreading ❌ (worse drawdown)
- Higher total returns ❌ (lost money vs profited)

**Actual Result:** Portfolio significantly underperformed single-pair approach

---

## RESULTS SUMMARY

### Overall Portfolio Performance

| Metric | Portfolio | EUR/USD Single | Difference |
|--------|-----------|----------------|------------|
| **Total P&L** | **-$17.20** ❌ | **+$2.11** ✅ | **-$19.31** (-916%) |
| **Win Rate** | 39.63% | 46.19% | -6.56% |
| **Total Trades** | 815 | 197 | +618 (more opportunities) |
| **Max Drawdown** | -$47.04 | -$0.61 | -$46.43 (77x worse!) |
| **Avg Pips** | -0.21 | +1.07 | -1.28 |

---

## INDIVIDUAL PAIR PERFORMANCE

| Pair | Trades | Win Rate | Total P&L | Avg Pips | Max Drawdown | Status |
|------|--------|----------|-----------|----------|--------------|--------|
| **USD/JPY** | 306 | 38.89% | **+$0.23** ✅ | +0.01 | -$34.99 | Only profitable |
| **EUR/USD** | 245 | 43.67% | **-$1.97** ❌ | -0.08 | -$9.70 | Lost money (vs +$2.11 standalone) |
| **GBP/USD** | 264 | 36.74% | **-$15.46** ❌❌ | -0.59 | -$23.52 | **Major drag** |

### Key Findings

1. **USD/JPY: Only profitable pair** (+$0.23, barely break-even)
2. **EUR/USD: Underperformed in portfolio** (-$1.97 vs +$2.11 standalone)
3. **GBP/USD: Major drag** (-$15.46, 90% of portfolio losses)

---

## MONTHLY PERFORMANCE

| Month | Total P&L | Trades | Win Rate | Status |
|-------|-----------|--------|----------|--------|
| June 2024 | -$11.29 | 103 | 35.92% | Worst month |
| July 2024 | **+$24.87** ✅ | 139 | 43.17% | **Best month** |
| August 2024 | +$2.52 | 131 | 42.75% | Good |
| September 2024 | -$5.53 | 98 | 39.80% | Poor |
| October 2024 | -$20.19 | 109 | 36.70% | **Worst month** |
| November 2024 | -$1.41 | 114 | 40.35% | Small loss |
| December 2024 | -$6.17 | 121 | 37.19% | Poor |

**Profitable Months:** 2 out of 7 (29%)
**Best Month:** July 2024 (+$24.87)
**Worst Months:** October 2024 (-$20.19), June 2024 (-$11.29)

---

## PAIR CORRELATION ANALYSIS

| Pair 1 | Pair 2 | Common Trade Days | Correlation % |
|--------|--------|-------------------|---------------|
| GBP/USD | EUR/USD | 122 | 87.77% |
| GBP/USD | USD/JPY | 126 | 88.11% |
| EUR/USD | USD/JPY | 131 | 91.61% |

**Key Insight:** Pairs are **highly correlated** (87-92% overlap in trading days). This means:
- **No real diversification benefit** - all pairs trade at similar times
- **Risk is NOT spread** - losses occur simultaneously
- **High correlation = false diversification**

---

## SUCCESS CRITERIA EVALUATION

| Criteria | Target | Actual | Status |
|----------|--------|--------|--------|
| Portfolio P&L > $4 | Beat EUR/USD ($2.11) | -$17.20 | ❌ **FAILED** |
| Win Rate > 45% | Better than single pair | 39.63% | ❌ **FAILED** |
| Max Drawdown < $10 | Acceptable risk | -$47.04 | ❌ **FAILED** (4.7x over) |
| Diversification benefit | Portfolio > Single | No | ❌ **FAILED** |

**All criteria FAILED.**

---

## WHY PORTFOLIO UNDERPERFORMED

### 1. **High Correlation Between Pairs**
- 87-92% trading day overlap
- Pairs trade at same times = no diversification
- Losses occur simultaneously (not spread out)

### 2. **GBP/USD Major Drag**
- -$15.46 loss (90% of portfolio losses)
- Only 36.74% win rate
- Strategy B doesn't work on GBP/USD

### 3. **EUR/USD Underperformed in Portfolio**
- Standalone: +$2.11 (46.19% win rate, 197 trades)
- In Portfolio: -$1.97 (43.67% win rate, 245 trades)
- **More trades = worse performance** (overtrading?)

### 4. **USD/JPY Barely Profitable**
- +$0.23 (38.89% win rate)
- Not enough to offset GBP/USD losses

### 5. **Extremely High Drawdown**
- -$47.04 vs -$0.61 (single pair)
- 77x worse risk management
- High correlation = simultaneous losses = larger drawdowns

---

## COMPARISON: PORTFOLIO vs SINGLE-PAIR

| Strategy | Trades | Win Rate | Total P&L | Max Drawdown | Sharpe Ratio |
|----------|--------|----------|-----------|--------------|--------------|
| **EUR/USD Single** | 197 | 46.19% | **+$2.11** ✅ | -$0.61 | 2.05 |
| **3-Pair Portfolio** | 815 | 39.63% | **-$17.20** ❌ | -$47.04 | Negative |

**Single-pair approach is FAR superior:**
- 8x better P&L (+$2.11 vs -$17.20)
- Higher win rate (46.19% vs 39.63%)
- 77x lower drawdown (-$0.61 vs -$47.04)
- Positive Sharpe ratio (2.05 vs negative)

---

## KEY LEARNINGS

### 1. **Diversification Requires Low Correlation**
- High correlation (87-92%) = no diversification benefit
- All pairs trade together = risk NOT spread
- Need uncorrelated assets for true diversification

### 2. **More Trades ≠ Better Performance**
- 815 trades vs 197 trades
- More trades = more transaction costs
- Overtrading reduces win rate and profitability

### 3. **Pair Selection Matters**
- GBP/USD: -$15.46 (major drag)
- Strategy B doesn't work on GBP/USD
- Should exclude underperforming pairs

### 4. **Portfolio Management Complexity**
- Managing 3 pairs simultaneously increases complexity
- Higher drawdowns require more capital
- More opportunities ≠ better risk-adjusted returns

### 5. **Quality Over Quantity**
- Single pair: Fewer, higher quality trades (46.19% win rate)
- Portfolio: More, lower quality trades (39.63% win rate)
- **Focus on best-performing pair**

---

## RECOMMENDATIONS

### ❌ Do NOT Use Multi-Pair Portfolio Approach

**Reasons:**
1. Significant underperformance (-$17.20 vs +$2.11)
2. Much higher drawdown (-$47.04 vs -$0.61)
3. Lower win rate (39.63% vs 46.19%)
4. High correlation = no diversification benefit
5. GBP/USD major drag (-$15.46)

### ✅ Stick with EUR/USD Single-Pair Strategy

**Why:**
- Proven profitable (+$2.11 over 7 months)
- Excellent win rate (46.19%)
- Low drawdown (-$0.61)
- Best Sharpe ratio (2.05)
- Simpler to manage
- Lower capital requirements

### Alternative: Two-Pair Portfolio (EUR/USD + USD/JPY Only)

If you want to test diversification:
- **Exclude GBP/USD** (major drag)
- **Test EUR/USD + USD/JPY only**
- Expected: Better than full portfolio, but likely worse than EUR/USD alone

---

## CONCLUSION

### Hypothesis: REJECTED ❌

**Multi-pair portfolio approach FAILED:**

- Portfolio: -$17.20 (significant loss)
- Single Pair: +$2.11 (profitable)
- Difference: -$19.31 (916% worse)

**Key Reasons:**
1. High correlation (87-92%) = no real diversification
2. GBP/USD major drag (-$15.46)
3. More trades = worse performance (overtrading)
4. Extremely high drawdown (-$47.04)

### Recommendation

**Use EUR/USD single-pair Strategy B approach:**
- ✅ Profitable (+$2.11)
- ✅ Good win rate (46.19%)
- ✅ Low drawdown (-$0.61)
- ✅ Best Sharpe ratio (2.05)
- ✅ Simpler and more manageable

**Diversification requires low correlation. These pairs are too highly correlated to provide diversification benefits.**

---

## Files Generated

- Portfolio results: `results/backtest_results_portfolio_strategy_b.csv`
- Comparison: `results/quant_analysis/portfolio_vs_single_comparison.csv`
- Analysis: `analyze_portfolio_results.py` output























