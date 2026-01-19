# VWAP Mean Reversion Strategy - Parameter Optimization Results

## Test Period: June 2024 - December 2024 (7 months)
## Pair: EUR/USD 15-minute
## Session: London only (8 AM - 5 PM UTC)

---

## Tested Configurations

| SD Multiplier | Band Width | Description |
|---------------|------------|-------------|
| 1.0 | Tight | Price must be very close to VWAP extremes |
| 1.5 | Medium | Current configuration (baseline) |
| 2.0 | Wide | Price must be further from VWAP |
| 2.5 | Very Wide | Price must be significantly extended from VWAP |

---

## Results Summary

| SD | Trades | Win Rate | Total P&L | Signals | Avg Pips | Max Drawdown | Status |
|----|--------|----------|-----------|---------|----------|--------------|--------|
| **2.0** | **888** | **43.81%** | **+$0.46** ✅ | 3,045 | +0.05 | -$2.94 | **BEST** |
| 1.5 | 1,035 | 43.77% | -$0.69 ❌ | 3,678 | -0.07 | -$4.00 | Baseline |
| 2.5 | 743 | 42.13% | -$1.36 ❌ | 2,434 | -0.18 | -$3.46 | Too wide |
| 1.0 | 1,144 | 43.97% | -$1.88 ❌ | 4,289 | -0.16 | -$4.12 | Too tight |

---

## Key Findings

### Winner: 2.0 SD Multiplier

**Configuration:**
- SD Multiplier: 2.0 (wider bands)
- Total Trades: 888
- Win Rate: 43.81%
- **Total P&L: +$0.46** ✅ (Only profitable configuration)
- Max Drawdown: -$2.94
- Signals: 3,045 (14.4 per day)

**Why 2.0 SD Works Better:**
1. **Fewer but higher quality signals**: 888 trades vs 1,035 (1.5 SD)
2. **Better signal quality**: Wider bands = more extreme deviations = stronger mean reversion
3. **Reduced overtrading**: 14.4 signals/day vs 17.4 signals/day (1.5 SD)
4. **Lower drawdown**: -$2.94 vs -$4.00 (1.5 SD)
5. **Positive average pips**: +0.05 vs -0.07 (1.5 SD)

### Analysis by SD Multiplier

#### 1.0 SD (Too Tight)
- **Problem**: Too many false signals (4,289 total)
- **Result**: Highest number of trades (1,144) but worst P&L (-$1.88)
- **Issue**: Price frequently touches bands but doesn't mean revert

#### 1.5 SD (Baseline - Too Narrow)
- **Problem**: Still too many signals (3,678 total)
- **Result**: 1,035 trades, -$0.69 P&L
- **Issue**: Bands not wide enough to filter noise

#### 2.0 SD (Optimal) ✅
- **Advantage**: Balanced signal quality and quantity
- **Result**: 888 trades, +$0.46 P&L (only profitable)
- **Success**: Wider bands filter noise, capture true mean reversion

#### 2.5 SD (Too Wide)
- **Problem**: Too few signals (2,434 total)
- **Result**: 743 trades, -$1.36 P&L
- **Issue**: Misses many valid mean reversion opportunities

---

## Comparison with Success Criteria

### 2.0 SD Configuration vs Criteria
- ❌ Win rate: 43.81% (target: >48%)
- ❌ Total P&L: +$0.46 (target: >$5)
- ✅ Max drawdown: -$2.94 (target: <$15)
- ❌ Signals: 14.4/day (target: 1-3/day)

**Overall**: Meets 1/4 criteria (barely profitable, but better than baseline)

---

## Signal Quality Analysis

| SD | Total Signals | Trades Executed | Conversion Rate | Signals/Day |
|----|---------------|-----------------|-----------------|-------------|
| 1.0 | 4,289 | 1,144 | 26.7% | 20.3 |
| 1.5 | 3,678 | 1,035 | 28.1% | 17.4 |
| **2.0** | **3,045** | **888** | **29.2%** | **14.4** |
| 2.5 | 2,434 | 743 | 30.5% | 11.5 |

**Insight**: Wider bands (2.0 SD) have better conversion rate (29.2%) - signals are more actionable.

---

## Risk/Reward Analysis

| SD | Avg Pips | Win Rate | Risk/Reward Ratio |
|----|----------|----------|-------------------|
| 1.0 | -0.16 | 43.97% | Negative |
| 1.5 | -0.07 | 43.77% | Negative |
| **2.0** | **+0.05** | **43.81%** | **Slightly Positive** |
| 2.5 | -0.18 | 42.13% | Negative |

**Key**: Only 2.0 SD has positive average pips per trade.

---

## Drawdown Comparison

| SD | Max Drawdown | Risk Level |
|----|--------------|------------|
| 1.0 | -$4.12 | High |
| 1.5 | -$4.00 | High |
| **2.0** | **-$2.94** | **Medium** |
| 2.5 | -$3.46 | Medium-High |

**2.0 SD has the lowest drawdown risk.**

---

## Recommendations

### Optimal Configuration: 2.0 SD Multiplier

**Why:**
1. ✅ Only profitable configuration (+$0.46)
2. ✅ Best risk-adjusted returns (lowest drawdown)
3. ✅ Better signal quality (higher conversion rate)
4. ✅ Positive average pips per trade

**However:**
- Still doesn't meet all success criteria
- Win rate below 48% target
- P&L far below $5 target
- Too many signals per day (14.4 vs target 1-3)

### Next Steps for Further Optimization

1. **Combine with additional filters:**
   - Add RSI confirmation (only trade VWAP signals when RSI also extreme)
   - Add volume/volatility filters
   - Add time-of-day filters (avoid low liquidity periods)

2. **Adjust risk/reward:**
   - Test different target/stop ratios (e.g., +10/-5, +12/-6)
   - Test trailing stops
   - Test partial profit taking

3. **Test on different timeframes:**
   - 30-minute or 1-hour candles (less noise)
   - Different currency pairs

4. **Consider hybrid approach:**
   - Use 2.0 SD for signal generation
   - Add RSI confirmation for entry
   - Combine best aspects of both strategies

---

## Conclusion

**2.0 SD Multiplier is the optimal VWAP configuration**, showing:
- Small profit (+$0.46) vs losses in other configurations
- Better risk management (lower drawdown)
- Improved signal quality

**However**, the strategy still needs significant improvement to meet success criteria. The VWAP mean reversion approach may not be suitable for 15-minute EUR/USD without additional filters or confirmations.

**Recommendation**: Use 2.0 SD as baseline, but add RSI or other confirmations to improve win rate and reduce signal frequency.























