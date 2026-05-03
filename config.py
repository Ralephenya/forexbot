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
RSI_BUY_THRESHOLD = 28   # RSI buy confirmation  — walk-forward optimized (was 30)
RSI_SELL_THRESHOLD = 72  # RSI sell confirmation — walk-forward optimized (was 70)

# Confluence Engine (7-layer hedge-fund scoring gate)
MIN_SCORE_TO_TRADE = 7   # Minimum score out of 10 to take a trade (A or A+)

# v3 HYBRID trade management — walk-forward optimized
# A grade  (score 7-8): fixed target, clean R:R
# A+ grade (score 9-10): bigger target + trailing stop + partial profit
TARGET_ATR_MULT   = 1.2  # A-grade target = ATR × 1.2 (fixed exit)
APLUS_TARGET_MULT = 3.0  # A+-grade target = ATR × 3.0 (let winners run)
STOP_ATR_MULT     = 1.2  # Stop = ATR × 1.2 (both grades)
TRAIL_TRIGGER_ATR = 1.0  # A+ only: activate trailing stop after +1.0× ATR
TRAIL_DISTANCE_ATR = 0.8 # A+ only: trail stop 0.8× ATR behind price
PARTIAL_AT_ATR    = 1.0  # A+ only: take 50% profit at +1.0× ATR
PARTIAL_PCT       = 0.5  # A+ only: close 50% of position at partial

# Trading Hours (London session: 3 AM - 12 PM Eastern Time = 8 AM - 5 PM UTC)
TRADING_START_HOUR = 8  # UTC
TRADING_END_HOUR = 17   # UTC (5 PM UTC = 12 PM ET)

# Position and Risk Management
POSITION_SIZE_LOTS = 0.01  # Micro lot
PIP_VALUE_PER_LOT = 1.0  # For EUR/USD, 1 pip = $1 per standard lot
PIP_VALUE = PIP_VALUE_PER_LOT * POSITION_SIZE_LOTS  # $0.01 per pip for 0.01 lots

TARGET_PIPS = 8  # Fallback fixed target (ATR-adaptive used when ATR available)
STOP_LOSS_PIPS = 6  # Fallback fixed stop
SPREAD_COST_PIPS = 1.2  # EUR/USD realistic spread
# Exit also occurs when price returns to VWAP (mean reversion complete)

# Results Paths
RESULTS_DIR = "results"
BACKTEST_RESULTS_FILE = "results/backtest_results_6months_hybrid.csv"
PERFORMANCE_REPORT_FILE = "results/performance_report_6months_hybrid.html"
CHARTS_DIR = "results/charts"

