"""
Apply Strategy B to AUD/USD with configurable time filtering
"""

import pandas as pd
import numpy as np
import logging
import os
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AUD/USD parameters
SPREAD_COST_PIPS = 1.5
PIP_MULTIPLIER = 10000  # AUD/USD: 1 pip = 0.0001


def calculate_atr(df, period=14):
    """Calculate ATR"""
    df = df.copy()
    was_indexed = False
    
    if 'datetime' in df.columns:
        df = df.set_index('datetime')
        was_indexed = True
    
    atr_indicator = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=period)
    atr_series = atr_indicator.average_true_range()
    
    if was_indexed:
        df = df.reset_index()
        atr_series = atr_series.reset_index(drop=True)
    
    return atr_series


def calculate_rsi(df, period=14):
    """Calculate RSI"""
    df = df.copy()
    was_indexed = False
    
    if 'datetime' in df.columns:
        df = df.set_index('datetime')
        was_indexed = True
    
    rsi_indicator = RSIIndicator(close=df['close'], window=period)
    rsi_series = rsi_indicator.rsi()
    
    if was_indexed:
        df = df.reset_index()
        rsi_series = rsi_series.reset_index(drop=True)
    
    return rsi_series


def strategy_b_audusd(df, optimal_hours=None, avoid_hours=None):
    """
    Strategy B: Regime-Switching System for AUD/USD
    
    Args:
        df: DataFrame with OHLC data
        optimal_hours: List of UTC hours to trade (if None, trades all hours)
        avoid_hours: List of UTC hours to avoid (if None, avoids none)
    
    Returns:
        DataFrame with signals
    """
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    
    # Calculate indicators
    df = df.set_index('datetime').sort_index()
    df['rsi_14'] = calculate_rsi(df, period=14)
    df['atr'] = calculate_atr(df, period=14)
    df['ema_20'] = df['close'].ewm(span=20).mean()
    df = df.reset_index()
    
    # Volatility regime (median of last 20 periods)
    df['atr_median'] = df['atr'].rolling(window=20).median()
    df['is_high_vol'] = df['atr'] > df['atr_median']
    
    # Time filters
    df['hour'] = df['datetime'].dt.hour
    
    if optimal_hours is not None:
        df['optimal_hour'] = df['hour'].isin(optimal_hours)
    else:
        df['optimal_hour'] = True  # Trade all hours
    
    if avoid_hours is not None:
        df['avoid_hour'] = df['hour'].isin(avoid_hours)
    else:
        df['avoid_hour'] = False  # Avoid none
    
    # Mean reversion signals (high volatility)
    df['mean_rev_buy'] = (df['rsi_14'] <= 30) & df['is_high_vol']
    df['mean_rev_sell'] = (df['rsi_14'] >= 70) & df['is_high_vol']
    
    # Breakout signals (low volatility)
    df['breakout_buy'] = (df['close'] > df['ema_20']) & ~df['is_high_vol']
    df['breakout_sell'] = (df['close'] < df['ema_20']) & ~df['is_high_vol']
    
    # Combined signals with time filtering
    df['buy_signal'] = (df['mean_rev_buy'] | df['breakout_buy']) & df['optimal_hour'] & ~df['avoid_hour']
    df['sell_signal'] = (df['mean_rev_sell'] | df['breakout_sell']) & df['optimal_hour'] & ~df['avoid_hour']
    
    # Adaptive targets
    df['adaptive_target_pips'] = np.where(
        df['is_high_vol'],
        df['atr'] * PIP_MULTIPLIER * 1.5,  # Mean reversion: 1.5x ATR
        df['atr'] * PIP_MULTIPLIER * 2.0   # Breakout: 2.0x ATR
    )
    df['adaptive_stop_pips'] = df['atr'] * PIP_MULTIPLIER * 1.0
    
    return df


def main():
    """Generate signals for different session configurations"""
    logger.info("=" * 70)
    logger.info("GENERATING STRATEGY B SIGNALS FOR AUD/USD")
    logger.info("=" * 70)
    
    # Load data (try both full data and yfinance data)
    data_file = 'data/audusd_15min_6months.csv'
    use_yfinance = False
    if not os.path.exists(data_file):
        data_file = 'data/audusd_15min_yfinance.csv'
        use_yfinance = True
        if not os.path.exists(data_file):
            logger.error(f"Data file not found. Please run histdata_downloader_audusd.py or quick_audusd_test.py")
            return
        else:
            logger.info("Using yfinance data (60-day limit) for quick test")
    else:
        logger.info("Using full 7-month HistData.com data")
    
    logger.info(f"Loading data from {data_file}...")
    df = pd.read_csv(data_file)
    logger.info(f"Loaded {len(df)} candles")
    
    # Define session hours (UTC)
    sydney_hours = list(range(22, 24)) + list(range(0, 7))  # 22:00-07:00 UTC
    london_hours = list(range(8, 17))  # 08:00-17:00 UTC
    combined_hours = sorted(set(sydney_hours + london_hours))
    
    # Test configurations
    configurations = [
        ('Sydney Session', sydney_hours, None),
        ('London Session', london_hours, None),
        ('Combined Sessions', combined_hours, None),
    ]
    
    for config_name, optimal_hours, avoid_hours in configurations:
        logger.info(f"\nGenerating signals for: {config_name}")
        logger.info(f"Optimal hours: {optimal_hours}")
        
        df_signals = strategy_b_audusd(df.copy(), optimal_hours=optimal_hours, avoid_hours=avoid_hours)
        
        # Count signals
        buy_signals = df_signals['buy_signal'].sum()
        sell_signals = df_signals['sell_signal'].sum()
        logger.info(f"Signals: BUY={buy_signals}, SELL={sell_signals}, Total={buy_signals + sell_signals}")
        
        # Save signals
        config_safe = config_name.lower().replace(' ', '_')
        if use_yfinance:
            output_file = f'data/audusd_15min_yfinance_strategy_b_{config_safe}_signals.csv'
        else:
            output_file = f'data/audusd_15min_6months_strategy_b_{config_safe}_signals.csv'
        df_signals.to_csv(output_file, index=False)
        logger.info(f"Signals saved to {output_file}")


if __name__ == "__main__":
    main()


