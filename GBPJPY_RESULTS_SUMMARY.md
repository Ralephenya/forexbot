# GBP/JPY Strategy B Test Results

## ⚠️ IMPORTANT: Data Limitations

**Test Period:**
- GBP/JPY: 60 days (Oct 12, 2025 - Jan 2, 2026) - **Limited data from yfinance**
- EUR/USD: 7 months (June - December 2024) - Full period

**This is NOT a fair comparison** due to:
1. Different time periods
2. Much shorter test period for GBP/JPY (60 days vs 210 days)
3. Different market conditions

---

## RESULTS SUMMARY

### Overall Performance

| Metric | EUR/USD | GBP/JPY | Status |
|--------|---------|---------|--------|
| **Total P&L** | **+$2.11** ✅ | **-$0.30** ❌ | EUR/USD wins |
| **Win Rate** | 46.19% | 39.34% | EUR/USD better |
| **Total Trades** | 197 | 122 | GBP/JPY fewer |
| **Max Drawdown** | -$0.61 | **-$21.30** ❌ | GBP/JPY much worse |
| **Sharpe Ratio** | 2.05 | -0.02 | EUR/USD much better |
| **Profit Factor** | 1.34 | 1.00 | EUR/USD better |

### ❌ Hypothesis REJECTED

**Expected:** GBP/JPY produces 1.5-2x profits ($3.17-$4.22)
**Actual:** GBP/JPY loses money (-$0.30)

**EUR/USD significantly outperforms GBP/JPY** on this limited dataset.

---

## KEY FINDINGS

### 1. Volatility Regime Performance (GBP/JPY)

| Regime | Trades | Total P&L | Win Rate | Status |
|--------|--------|-----------|----------|--------|
| **High Volatility** | 32 | **+$8.58** ✅ | 46.88% | **WINNER** |
| **Low Volatility** | 90 | **-$8.88** ❌ | 36.67% | **LOSER** |

**Critical Insight:**
- High volatility regime works well (mean reversion profitable)
- Low volatility regime is terrible (breakout strategy fails)
- **Low volatility trades account for 74% of trades but all losses**

### 2. Time-of-Day Performance (GBP/JPY)

| Hour | Trades | Total P&L | Win Rate | Status |
|------|--------|-----------|----------|--------|
| 14 | 31 | **+$15.56** ✅✅ | 54.84% | **EXCELLENT** |
| 12 | 37 | -$1.70 | 35.14% | Poor |
| 10 | 28 | -$3.74 | 35.71% | Poor |
| 9 | 26 | -$10.41 | 30.77% | **WORST** |

**Key Finding:**
- **Hour 14 is exceptional** (+$15.56, 54.84% win rate)
- Other hours (9, 10, 12) are all negative
- If trading only Hour 14: +$15.56 profit (but only 31 trades)

### 3. Risk Analysis

**Max Drawdown: -$21.30** (vs -$0.61 for EUR/USD)
- This is **35x worse** than EUR/USD
- Suggests GBP/JPY's higher volatility creates much larger risk
- Drawdown too high for acceptable trading

---

## WHY GBP/JPY UNDERPERFORMED

### 1. **Low Volatility Regime Failure**
- 90 trades in low volatility (breakout strategy)
- All losing money (-$8.88 total)
- 36.67% win rate (too low)
- **Breakout strategy doesn't work on GBP/JPY**

### 2. **Wider Spread Impact**
- GBP/JPY: 2.5 pip spread (vs 1.0 pip for EUR/USD)
- 2.5x wider spread = higher transaction costs
- More impact on lower win rate trades

### 3. **Higher Volatility = Higher Risk**
- GBP/JPY's higher volatility creates larger drawdowns
- -$21.30 drawdown vs -$0.61 for EUR/USD
- Risk/reward not favorable

### 4. **Data Period Issues**
- Only 60 days of data (vs 210 days for EUR/USD)
- Different time period (future data?)
- May not represent typical market conditions

---

## SUCCESS CRITERIA EVALUATION

| Criteria | Target | GBP/JPY Actual | Status |
|----------|--------|----------------|--------|
| Total P&L > $2.11 | Beat EUR/USD | -$0.30 | ❌ Failed |
| Win Rate > 46% | Beat EUR/USD | 39.34% | ❌ Failed |
| Max Drawdown < $2.00 | Acceptable risk | -$21.30 | ❌ Failed (10x over) |

**All criteria FAILED.**

---

## RECOMMENDATIONS

### ❌ Do NOT Use Strategy B on GBP/JPY (Current Configuration)

**Reasons:**
1. Unprofitable overall (-$0.30)
2. Extremely high drawdown (-$21.30)
3. Low win rate (39.34%)
4. Breakout strategy fails in low volatility

### ✅ Potential Improvements

1. **Trade Only Hour 14:**
   - Hour 14: +$15.56 profit, 54.84% win rate
   - But only 31 trades (very few opportunities)

2. **Skip Low Volatility Regime:**
   - Only trade high volatility (mean reversion)
   - High vol: +$8.58, 46.88% win rate
   - Low vol: -$8.88 (all losses)

3. **Adjust Targets/Stops:**
   - Current ATR-based targets may be too tight
   - GBP/JPY's higher volatility needs wider stops
   - Consider fixed targets instead of ATR-based

4. **Different Strategy for GBP/JPY:**
   - Strategy B optimized for EUR/USD
   - GBP/JPY may need different approach
   - Consider trend-following instead of mean reversion

---

## CONCLUSION

### Hypothesis: REJECTED ❌

**GBP/JPY's higher volatility does NOT produce 1.5-2x profits.**

Instead:
- GBP/JPY: **-$0.30 loss**
- EUR/USD: **+$2.11 profit**
- **EUR/USD is 7x better** (in terms of profitability)

### Key Learnings

1. **Strategy B works on EUR/USD but NOT on GBP/JPY**
2. **Higher volatility ≠ Higher profits** (higher risk instead)
3. **Breakout strategy fails on GBP/JPY** (low volatility regime loses money)
4. **Wider spreads hurt performance** (2.5 pips vs 1.0 pip)
5. **Hour 14 shows promise** but needs more testing

### Recommendation

**Stick with EUR/USD for Strategy B.** GBP/JPY requires:
- Different strategy design
- Better risk management
- Possibly different time filters
- More testing on longer dataset

---

## Files Generated

- Signals: `data/gbpjpy_15min_6months_strategy_b_signals.csv`
- Results: `results/backtest_results_strategy_b_gbpjpy.csv`
- Comparison: `results/quant_analysis/gbpjpy_vs_eurusd_comparison.csv`























