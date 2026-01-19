# GBP/JPY Strategy B Implementation Guide

## Objective
Test Strategy B (Regime-Switching) on GBP/JPY to compare performance against EUR/USD baseline (+$2.11).

## Data Requirements

### Download GBP/JPY Data

1. **Visit HistData.com:**
   - URL: https://www.histdata.com/download-free-forex-historical-data/
   
2. **Select Parameters:**
   - Currency Pair: **GBP/JPY**
   - Timeframe: **M1** (1-minute)
   - Year: **2024**
   
3. **Download ZIP File:**
   - Download the ZIP file (should be named `DAT_ASCII_GBPJPY_M2024.zip`)
   - Save to: `data/` directory or `data/histdata/` directory
   
4. **Process Data:**
   ```bash
   python histdata_downloader_gbpjpy.py
   ```
   This will:
   - Extract 1-minute data from ZIP
   - Filter to June-December 2024
   - Aggregate to 15-minute candles
   - Save to: `data/gbpjpy_15min_6months.csv`

## Strategy B Configuration

### Volatility Regime Detection
- Calculate ATR(14) for each candle
- Median ATR = median of last 20 periods
- **High Vol:** ATR > Median ATR
- **Low Vol:** ATR ≤ Median ATR

### HIGH VOLATILITY MODE (Mean Reversion)
- **BUY Signal:** RSI(14) ≤ 30
- **SELL Signal:** RSI(14) ≥ 70
- **Target:** +1.5x ATR (in pips)
- **Stop Loss:** -1.0x ATR (in pips)

### LOW VOLATILITY MODE (Breakout)
- **BUY Signal:** Price closes above EMA(20)
- **SELL Signal:** Price closes below EMA(20)
- **Target:** +2.0x ATR (in pips)
- **Stop Loss:** -1.0x ATR (in pips)

### TIME FILTERING
- **ONLY trade during hours:** 9, 10, 12, 14 (UTC)
- **AVOID hours:** 13, 16 (proven low win rate)

### TRADE MANAGEMENT
- **Spread:** 2.5 pips (typical GBP/JPY)
- **Position:** 0.01 lots ($0.10 per pip)
- **One trade at a time**

## Running the Strategy

### Step 1: Download and Process Data
```bash
# After downloading ZIP file from HistData.com
python histdata_downloader_gbpjpy.py
```

### Step 2: Calculate Strategy Signals
```bash
python strategy_b_gbpjpy.py
```
Output: `data/gbpjpy_15min_6months_strategy_b_signals.csv`

### Step 3: Run Backtest
```bash
python backtest_strategy_b_gbpjpy.py
```
Output: `results/backtest_results_strategy_b_gbpjpy.csv`

### Step 4: Compare to EUR/USD
```bash
python compare_gbpjpy_eurusd.py
```

## Success Criteria

- **Total P&L:** >$2.11 (beat EUR/USD baseline)
- **Win Rate:** >46%
- **Max Drawdown:** <$2.00

## Hypothesis

**GBP/JPY's higher volatility produces 1.5-2x the profits of EUR/USD.**

Expected: GBP/JPY should generate $3.17-$4.22 (1.5-2x EUR/USD's $2.11)

## Expected Deliverables

1. Total trades executed
2. Win rate percentage
3. Total P&L comparison to EUR/USD
4. Monthly breakdown
5. Max drawdown
6. Which volatility regime performed better
7. Best/worst hours for GBP/JPY

## Files Generated

- Data: `data/gbpjpy_15min_6months.csv`
- Signals: `data/gbpjpy_15min_6months_strategy_b_signals.csv`
- Results: `results/backtest_results_strategy_b_gbpjpy.csv`
- Comparison: `results/quant_analysis/gbpjpy_vs_eurusd_comparison.csv`

## Notes

- **Pip Value:** GBP/JPY uses 0.01 per pip (e.g., 150.00 → 150.01 = 1 pip)
- **Spread:** GBP/JPY typically has wider spreads (2.5 pips vs 1.0 pip for EUR/USD)
- **Volatility:** GBP/JPY is more volatile than EUR/USD, which may provide more trading opportunities
- **Time Zones:** All times in UTC (London session = 8 AM - 5 PM UTC)























