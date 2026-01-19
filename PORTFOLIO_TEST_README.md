# Multi-Pair Portfolio Test - Strategy B

## Objective
Test if diversifying across 3 pairs (EUR/USD, GBP/USD, USD/JPY) beats single-pair approach using Strategy B.

## Data Requirements

### Download from HistData.com

1. **Visit:** https://www.histdata.com/download-free-forex-historical-data/

2. **Download for each pair:**
   - **GBP/USD:** Select GBP/USD, M1 timeframe, Year 2024
   - **USD/JPY:** Select USD/JPY, M1 timeframe, Year 2024
   
3. **Save ZIP files to:** `data/` or `data/histdata/` directory
   - Expected: `DAT_ASCII_GBPUSD_M2024.zip`
   - Expected: `DAT_ASCII_USDJPY_M2024.zip`

4. **EUR/USD:** Already available (`data/eurusd_15min_6months.csv`)

## Running the Portfolio Test

### Step 1: Process Data
```bash
python histdata_downloader_multipair.py
```
This will:
- Extract 1-minute data from ZIP files
- Filter to June-December 2024
- Aggregate to 15-minute candles
- Save to: `data/{pair}_15min_6months.csv`

### Step 2: Generate Strategy B Signals
```bash
python apply_strategy_b_all_pairs.py
```
This applies Strategy B logic to all 3 pairs and saves signals to:
- `data/eurusd_15min_6months_strategy_b_signals.csv`
- `data/gbpusd_15min_6months_strategy_b_signals.csv`
- `data/usdjpy_15min_6months_strategy_b_signals.csv`

### Step 3: Run Portfolio Backtest
```bash
python portfolio_backtester.py
```
This runs the portfolio backtest with:
- Maximum 2 positions open simultaneously
- Pair-specific spreads and pip calculations
- Portfolio-wide P&L tracking

## Strategy Configuration

### Strategy B Logic (Same for All Pairs)
- **Volatility Regime:** ATR > Median (High) vs ≤ Median (Low)
- **High Vol:** RSI mean reversion (≤30/≥70)
- **Low Vol:** EMA(20) breakout
- **Time Filter:** Hours 9, 10, 12, 14 (UTC)
- **Adaptive Targets:** 1.5x ATR (high vol) or 2.0x ATR (low vol)

### Pair-Specific Parameters

| Pair | Spread | Pip Multiplier | Pip Value |
|------|--------|----------------|-----------|
| EUR/USD | 1.0 pip | 10000 (0.0001) | $0.10 |
| GBP/USD | 1.5 pips | 10000 (0.0001) | $0.10 |
| USD/JPY | 1.5 pips | 100 (0.01) | $0.10 |

### Portfolio Rules
- **Maximum 2 positions** open simultaneously across all pairs
- If 2 signals trigger at same time, take both
- Equal position sizing (0.01 lots per trade)
- Track individual pair performance AND total portfolio P&L

## Success Criteria

- **Portfolio P&L:** >$4 (significantly better than EUR/USD alone at $2.11)
- **Win Rate:** >45% across portfolio
- **Diversification benefit visible**

## Expected Deliverables

1. **Individual pair results:**
   - EUR/USD: P&L, win rate, trades
   - GBP/USD: P&L, win rate, trades
   - USD/JPY: P&L, win rate, trades

2. **Total Portfolio P&L**

3. **Monthly portfolio performance**

4. **Correlation between pairs** (do they trade at same times?)

5. **Maximum portfolio drawdown**

6. **Comparison:** Portfolio vs EUR/USD single-pair

## Hypothesis

**Diversification across 3 pairs provides:**
- More trading opportunities
- Risk spreading
- Higher total returns (>$4 vs $2.11)

## Files Generated

- Data files: `data/{pair}_15min_6months.csv`
- Signal files: `data/{pair}_15min_6months_strategy_b_signals.csv`
- Portfolio results: `results/backtest_results_portfolio_strategy_b.csv`























