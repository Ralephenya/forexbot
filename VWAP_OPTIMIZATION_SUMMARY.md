# VWAP Mean Reversion Strategy - Optimization Results

## Optimization Test: Standard Deviation Multiplier

### Test Period: June 2024 - December 2024 (7 months)
### Pair: EUR/USD 15-minute
### Session: London only (8 AM - 5 PM UTC)

---

## Parameter Test Results

| SD Multiplier | Trades | Win Rate | Total P&L | Signals | Avg Pips | Max Drawdown | Status |
|---------------|--------|----------|-----------|---------|----------|--------------|--------|
| **2.0** | **888** | **43.81%** | **+$0.46** ✅ | 3,045 | +0.05 | -$2.94 | **OPTIMAL** |
| 1.5 | 1,035 | 43.77% | -$0.69 ❌ | 3,678 | -0.07 | -$4.00 | Baseline |
| 2.5 | 743 | 42.13% | -$1.36 ❌ | 2,434 | -0.18 | -$3.46 | Too wide |
| 1.0 | 1,144 | 43.97% | -$1.88 ❌ | 4,289 | -0.16 | -$4.12 | Too tight |

---

## Winner: 2.0 SD Multiplier Configuration

### Overall Performance
- **Total Trades**: 888
- **Win Rate**: 43.81%
- **Total P&L**: **+$0.46** ✅ (Only profitable configuration)
- **Average Pips per Trade**: +0.05
- **Max Drawdown**: -$2.94
- **Signals**: 3,045 total (14.4 per day)

### Improvement vs Baseline (1.5 SD)
- **P&L**: -$0.69 → **+$0.46** (+$1.15 improvement)
- **Trades**: 1,035 → 888 (14% fewer, higher quality)
- **Drawdown**: -$4.00 → **-$2.94** (26% better risk management)
- **Avg Pips**: -0.07 → **+0.05** (positive vs negative)

---

## Exit Reason Breakdown (2.0 SD)

| Exit Reason | Count | Total P&L | Avg P&L | Percentage |
|-------------|-------|-----------|---------|------------|
| Target | 321 | +$25.68 | +$0.08 | 36.1% |
| Stop Loss | 463 | -$27.78 | -$0.06 | 52.1% |
| VWAP Return | 27 | +$1.26 | +$0.05 | 3.0% |
| End of Day | 77 | +$1.29 | +$0.02 | 8.7% |

**Key Insight**: Stop losses still hit 52% of the time, but the wider bands (2.0 SD) produce better quality trades when targets hit.

---

## Monthly Performance (2.0 SD)

| Month | Trades | Win Rate | Total P&L | Avg Pips | Status |
|-------|--------|----------|-----------|----------|--------|
| June 2024 | 95 | 44.21% | +$0.13 | +0.14 | Small Win |
| July 2024 | 110 | 51.82% | +$1.08 | +0.98 | **Best** ✅ |
| August 2024 | 132 | 37.88% | -$1.23 | -0.93 | Worst ❌ |
| September 2024 | 130 | 40.00% | -$0.39 | -0.30 | Loss |
| October 2024 | 132 | 37.88% | -$1.10 | -0.83 | Loss |
| November 2024 | 145 | 44.83% | +$0.86 | +0.59 | Win ✅ |
| December 2024 | 144 | 50.69% | +$1.11 | +0.77 | Win ✅ |

**Profitable Months**: 4 out of 7 (57%)
**Best Month**: July 2024 (+$1.08, 51.82% win rate)
**Worst Month**: August 2024 (-$1.23, 37.88% win rate)

---

## Comparison: 1.5 SD vs 2.0 SD

| Metric | 1.5 SD (Baseline) | 2.0 SD (Optimized) | Improvement |
|--------|-------------------|-------------------|-------------|
| Total P&L | -$0.69 ❌ | +$0.46 ✅ | +$1.15 |
| Win Rate | 43.77% | 43.81% | +0.04% |
| Total Trades | 1,035 | 888 | -14% (quality over quantity) |
| Signals | 3,678 | 3,045 | -17% (fewer, better) |
| Avg Pips | -0.07 | +0.05 | +0.12 |
| Max Drawdown | -$4.00 | -$2.94 | +26% (lower risk) |

---

## Success Criteria Evaluation (2.0 SD)

| Criteria | Target | Actual | Status |
|----------|--------|--------|--------|
| Win Rate | >48% | 43.81% | ❌ (4.2% below target) |
| Total P&L | >$5 | +$0.46 | ❌ (far below target) |
| Max Drawdown | <$15 | -$2.94 | ✅ (well below limit) |
| Signals/Day | 1-3 | 14.4 | ❌ (too many signals) |

**Overall**: Meets 1/4 criteria (better than 1.5 SD which met 1/4, but still unprofitable overall)

---

## Key Findings

### Why 2.0 SD Works Better

1. **Wider bands = Better signal quality**
   - Price must deviate further from VWAP to trigger signal
   - More extreme deviations = stronger mean reversion potential
   - Filters out noise and weak signals

2. **Fewer trades = Better execution**
   - 888 trades vs 1,035 (14% reduction)
   - Lower overtrading risk
   - More selective entry points

3. **Improved risk management**
   - Lower drawdown (-$2.94 vs -$4.00)
   - Better capital preservation
   - More consistent performance

4. **Positive average pips**
   - +0.05 pips per trade vs -0.07
   - Slight edge per trade accumulates over time

### Why Strategy Still Struggles

1. **Win rate below 50%**
   - 43.81% win rate means losses outnumber wins
   - Need >50% or better risk/reward to be profitable

2. **Stop loss frequency**
   - 52% of trades hit stop loss
   - Suggests mean reversion not always reliable on 15-min timeframe

3. **Too many signals**
   - 14.4 signals per day vs target of 1-3
   - Still overtrading despite improvement

4. **Inconsistent monthly performance**
   - 4 winning months, 3 losing months
   - Strategy sensitive to market conditions

---

## Recommendations

### Optimal Configuration: 2.0 SD Multiplier ✅

**Use this configuration for:**
- Further optimization testing
- Combining with other filters
- Baseline for hybrid strategies

### Next Optimization Steps

1. **Add RSI Confirmation**
   - Only trade VWAP signals when RSI also extreme
   - Could improve win rate and reduce signals

2. **Adjust Risk/Reward**
   - Test wider stops (e.g., -8 pips) with same target
   - Or test asymmetric targets (e.g., +10/-5)

3. **Add Time Filters**
   - Avoid first/last hour of London session
   - Focus on peak liquidity hours

4. **Test Different Timeframes**
   - 30-minute or 1-hour candles (less noise)
   - VWAP may work better on longer timeframes

5. **Hybrid Strategy**
   - Combine VWAP 2.0 SD with RSI strategy
   - Use VWAP for entry, RSI for confirmation
   - Best of both approaches

---

## Files Generated

- Parameter test results: `results/vwap_parameter_test_results.csv`
- Optimized backtest: `results/backtest_results_6months_vwap_2sd.csv`
- Performance report: `results/performance_report_6months_vwap_2sd.html`
- Charts: `results/charts/cumulative_pnl_6months_vwap.png`, `daily_pnl_6months_vwap.png`

---

## Conclusion

**2.0 SD Multiplier is the optimal VWAP configuration**, showing:
- ✅ Small profit (+$0.46) vs losses in other configurations
- ✅ Better risk management (lower drawdown)
- ✅ Improved signal quality (fewer, better trades)
- ✅ Positive average pips per trade

**However**, the strategy still needs significant improvement:
- ❌ Win rate below 48% target
- ❌ P&L far below $5 target  
- ❌ Too many signals per day

**Recommendation**: Use 2.0 SD as baseline, but add RSI or other confirmations to improve win rate and reduce signal frequency. Consider testing on longer timeframes (30-min or 1-hour) where VWAP mean reversion may be more reliable.























