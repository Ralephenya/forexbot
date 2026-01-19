# AUD/USD Extended Trading Hours Test

## Objective
Test if AUD/USD with Sydney session (extended trading hours) provides more opportunities and better performance than EUR/USD with only London session.

## Hypothesis
**AUD/USD + Sydney session = Extended trading hours = More opportunities = Higher profits**

---

## Test Period
- **Data:** June-December 2024 (7 months)
- **Timeframe:** 15-minute candles
- **Pair:** AUD/USD
- **Baseline:** EUR/USD 15-minute with London session (+$2.11, 46.19% win rate, 197 trades)

---

## Strategy Configuration

### Strategy B (Regime-Switching System)
- **Mean Reversion (High Volatility):** RSI ≤30/≥70, 1.5x ATR target
- **Breakout (Low Volatility):** Price vs EMA(20), 2.0x ATR target
- **Adaptive Targets:** Based on ATR
- **Spread:** 1.5 pips (AUD/USD typical)
- **Position Size:** 0.01 lots

### Session Configurations

1. **Sydney Session Only**
   - Hours: 22:00-07:00 UTC
   - Hypothesis: AUD/USD is most active during Sydney session

2. **London Session Only**
   - Hours: 08:00-17:00 UTC
   - Hypothesis: Compare directly with EUR/USD baseline

3. **Combined Sessions**
   - Hours: Sydney + London (22:00-07:00 + 08:00-17:00 UTC)
   - Hypothesis: Extended hours = more opportunities

---

## Test Phases

### Phase 1: Hour-by-Hour Analysis
**Goal:** Find optimal trading hours for AUD/USD

- Generate Strategy B signals WITHOUT time filtering
- Analyze signal frequency by hour (0-23 UTC)
- Identify hours with:
  - High signal count
  - High volatility (ATR)
  - Potential edge

**Deliverable:** `results/audusd_hour_analysis.csv`

### Phase 2: Generate Strategy B Signals
**Goal:** Generate signals for each session configuration

- Apply Strategy B logic to AUD/USD data
- Generate signals for:
  - Sydney session only
  - London session only
  - Combined sessions

**Deliverables:**
- `data/audusd_15min_6months_strategy_b_sydney_session_signals.csv`
- `data/audusd_15min_6months_strategy_b_london_session_signals.csv`
- `data/audusd_15min_6months_strategy_b_combined_sessions_signals.csv`

### Phase 3: Backtest All Configurations
**Goal:** Evaluate performance of each session

- Backtest Sydney session
- Backtest London session
- Backtest Combined sessions
- Calculate metrics:
  - Total P&L
  - Win rate
  - Max drawdown
  - Sharpe ratio
  - Trade count

**Deliverables:**
- `results/backtest_results_audusd_sydney_session.csv`
- `results/backtest_results_audusd_london_session.csv`
- `results/backtest_results_audusd_combined_sessions.csv`
- `results/audusd_configuration_comparison.csv`

### Phase 4: Compare with EUR/USD Baseline
**Goal:** Determine if AUD/USD beats EUR/USD baseline

- Load EUR/USD baseline results
- Compare all AUD/USD configurations
- Identify best configuration
- Provide recommendation

**Deliverable:** `results/audusd_vs_eurusd_comparison.csv`

---

## Success Criteria

1. **Profitability:** Total P&L > $2.11 (beat EUR/USD baseline)
2. **Win Rate:** > 46% (beat or match EUR/USD baseline)
3. **Extended Hours:** More trading opportunities (more trades)
4. **Risk-Adjusted:** Sharpe ratio > 2.0 (or similar to EUR/USD)

---

## Running the Test

### Step 1: Download Data
```bash
# Option 1: Manual download from HistData.com
# 1. Visit: https://www.histdata.com/download-free-forex-historical-data/
# 2. Select: AUD/USD, M1 (1-minute), Year 2024
# 3. Save ZIP to: data/histdata/DAT_ASCII_AUDUSD_M2024.zip

# Option 2: Run downloader (requires manual download first)
python histdata_downloader_audusd.py
```

### Step 2: Run Full Test
```bash
python run_audusd_test.py
```

### Step 3: Run Individual Phases (Optional)

**Phase 1: Hour Analysis**
```bash
python audusd_hour_analysis.py
```

**Phase 2: Generate Signals**
```bash
python strategy_b_audusd.py
```

**Phase 3: Backtest**
```bash
python backtest_strategy_b_audusd.py
```

**Phase 4: Compare**
```bash
python compare_audusd_eurusd.py
```

---

## Expected Outcomes

### Best Case Scenario
- **Sydney Session:** High profitability, good win rate
- **Combined Sessions:** Even higher profitability (more opportunities)
- **Recommendation:** Trade AUD/USD with Sydney/Combined sessions

### Worst Case Scenario
- **All Configurations:** Lower profitability than EUR/USD
- **Recommendation:** Stick with EUR/USD

### Mixed Scenario
- **Sydney Session:** Higher profitability but lower win rate
- **London Session:** Similar to EUR/USD
- **Combined Sessions:** Best overall
- **Recommendation:** Trade Combined sessions if it beats EUR/USD

---

## Files Structure

```
C:\Development\Agent\
├── histdata_downloader_audusd.py      # Download AUD/USD data
├── audusd_hour_analysis.py            # Phase 1: Hour-by-hour analysis
├── strategy_b_audusd.py               # Phase 2: Generate signals
├── backtest_strategy_b_audusd.py      # Phase 3: Backtest all configs
├── compare_audusd_eurusd.py           # Phase 4: Compare with EUR/USD
├── run_audusd_test.py                 # Full test runner
├── data/
│   ├── audusd_15min_6months.csv                           # Processed data
│   ├── audusd_15min_6months_strategy_b_*_signals.csv     # Signals
│   └── histdata/
│       └── DAT_ASCII_AUDUSD_M2024.zip                     # Raw data
└── results/
    ├── audusd_hour_analysis.csv                           # Phase 1 results
    ├── backtest_results_audusd_*.csv                      # Phase 3 results
    ├── audusd_configuration_comparison.csv                # Phase 3 summary
    └── audusd_vs_eurusd_comparison.csv                    # Phase 4 comparison
```

---

## Notes

1. **Data Source:** HistData.com (free historical forex data)
2. **Time Zones:** All times in UTC
3. **Sydney Session:** 22:00-07:00 UTC (AEST = UTC+10, but varies with DST)
4. **London Session:** 08:00-17:00 UTC (GMT = UTC+0)
5. **Spread:** 1.5 pips for AUD/USD (typical broker spread)

---

## Hypothesis Evaluation

**If AUD/USD beats EUR/USD:**
- ✅ Hypothesis ACCEPTED
- Extended trading hours provide more opportunities
- AUD/USD + Sydney session is superior

**If AUD/USD does NOT beat EUR/USD:**
- ❌ Hypothesis REJECTED
- Extended hours do not necessarily mean better performance
- EUR/USD remains the better choice

---

**Status:** Ready to run (requires AUD/USD data download)





















