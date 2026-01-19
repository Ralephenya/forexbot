"""
Configuration file for Forex Backtesting System
RSI Mean Reversion Strategy on 15-minute EUR/USD
"""

# Trading Pair
SYMBOL = "EURUSD"
FROM_SYMBOL = "EUR"
TO_SYMBOL = "USD"

# Data Configuration (7-month dataset from HistData.com)
TIMEFRAME = "15m"
DATA_FILE = "data/eurusd_15min_6months.csv"
INDICATORS_FILE = "data/eurusd_15min_6months_hybrid_indicators.csv"
SIGNALS_FILE = "data/eurusd_15min_6months_hybrid_signals.csv"

# Indicator Parameters (VWAP + RSI Hybrid Strategy)
VWAP_STD_MULTIPLIER = 2.0  # Standard deviation multiplier for bands (OPTIMIZED: 2.0 is best)
RSI_PERIOD = 14  # RSI period
# VWAP resets daily at 00:00 UTC

# Strategy Parameters (VWAP + RSI Hybrid Mean Reversion)
# BUY: Price below VWAP - 2.0 SD AND RSI ≤ 30 (both must agree)
# SELL: Price above VWAP + 2.0 SD AND RSI ≥ 70 (both must agree)
RSI_BUY_THRESHOLD = 30  # RSI buy confirmation
RSI_SELL_THRESHOLD = 70  # RSI sell confirmation

# Trading Hours (London session: 3 AM - 12 PM Eastern Time = 8 AM - 5 PM UTC)
TRADING_START_HOUR = 8  # UTC
TRADING_END_HOUR = 17  # UTC (5 PM UTC = 12 PM ET)

# Position and Risk Management
POSITION_SIZE_LOTS = 0.01  # Micro lot
PIP_VALUE_PER_LOT = 1.0  # For EUR/USD, 1 pip = $1 per standard lot
PIP_VALUE = PIP_VALUE_PER_LOT * POSITION_SIZE_LOTS  # $0.01 per pip for 0.01 lots

TARGET_PIPS = 8  # Target: +8 pips
STOP_LOSS_PIPS = 6  # Stop Loss: -6 pips
SPREAD_COST_PIPS = 1.0  # Total spread cost per trade (EUR/USD typically tighter)
# Exit also occurs when price returns to VWAP (mean reversion complete)

# Results Paths
RESULTS_DIR = "results"
BACKTEST_RESULTS_FILE = "results/backtest_results_6months_hybrid.csv"
PERFORMANCE_REPORT_FILE = "results/performance_report_6months_hybrid.html"
CHARTS_DIR = "results/charts"

