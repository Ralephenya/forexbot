"""
Advanced Strategy Design Based on Pattern Discovery
3 Unconventional Strategies with Pattern-Based Filters
"""

import pandas as pd
import numpy as np
import logging
import os
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pattern-based filters (from quant analysis)
OPTIMAL_HOURS = [9, 10, 12, 14]  # Hours with 54%+ win rate
AVOID_HOURS = [13, 16]  # Hours with terrible performance
OPTIMAL_DAYS = ['Tuesday', 'Thursday']  # Best performing days
AVOID_DAYS = ['Friday']  # Worst performing day
HIGH_VOLATILITY_ONLY = True  # Mean reversion works better in high volatility


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


def strategy_a_time_filtered_rsi(df):
    """
    Strategy A: Time-Filtered RSI
    - Only trade RSI signals during optimal hours (9, 10, 12, 14)
    - Only trade in high volatility regime
    - Adaptive targets based on ATR
    """
    logger.info("Calculating Strategy A: Time-Filtered RSI...")
    
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    
    # Calculate indicators
    df = df.set_index('datetime').sort_index()
    df['rsi_14'] = calculate_rsi(df, period=14)
    df['atr'] = calculate_atr(df, period=14)
    df = df.reset_index()
    
    # Calculate volatility regime
    atr_median = df['atr'].median()
    df['is_high_vol'] = df['atr'] > atr_median
    
    # Extract time features
    df['hour'] = df['datetime'].dt.hour
    df['day_of_week'] = df['datetime'].dt.day_name()
    
    # RSI signals
    df['rsi_buy_signal'] = df['rsi_14'] <= 30
    df['rsi_sell_signal'] = df['rsi_14'] >= 70
    
    # Time filters
    df['optimal_hour'] = df['hour'].isin(OPTIMAL_HOURS)
    df['avoid_hour'] = df['hour'].isin(AVOID_HOURS)
    df['optimal_day'] = df['day_of_week'].isin(OPTIMAL_DAYS)
    
    # Combined signals with filters
    df['buy_signal'] = (
        df['rsi_buy_signal'] &
        df['optimal_hour'] &
        ~df['avoid_hour'] &
        df['is_high_vol']
    )
    
    df['sell_signal'] = (
        df['rsi_sell_signal'] &
        df['optimal_hour'] &
        ~df['avoid_hour'] &
        df['is_high_vol']
    )
    
    # Adaptive targets based on ATR (target = 1.5x ATR, stop = 1.0x ATR)
    df['adaptive_target_pips'] = (df['atr'] / df['close'] * 10000 * 1.5).fillna(10)
    df['adaptive_stop_pips'] = (df['atr'] / df['close'] * 10000 * 1.0).fillna(8)
    
    return df


def strategy_b_regime_switching(df):
    """
    Strategy B: Regime-Switching System
    - Mean reversion (RSI) during high volatility
    - Breakout trading during low volatility
    - Automatically switch based on ATR
    """
    logger.info("Calculating Strategy B: Regime-Switching System...")
    
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    
    # Calculate indicators
    df = df.set_index('datetime').sort_index()
    df['rsi_14'] = calculate_rsi(df, period=14)
    df['atr'] = calculate_atr(df, period=14)
    
    # Calculate EMA for breakout detection
    df['ema_20'] = df['close'].ewm(span=20).mean()
    df = df.reset_index()
    
    # Volatility regime
    atr_median = df['atr'].median()
    df['is_high_vol'] = df['atr'] > atr_median
    
    # Time filters
    df['hour'] = df['datetime'].dt.hour
    df['optimal_hour'] = df['hour'].isin(OPTIMAL_HOURS)
    
    # Mean reversion signals (high volatility)
    df['mean_rev_buy'] = (df['rsi_14'] <= 30) & df['is_high_vol']
    df['mean_rev_sell'] = (df['rsi_14'] >= 70) & df['is_high_vol']
    
    # Breakout signals (low volatility)
    df['breakout_buy'] = (df['close'] > df['ema_20']) & ~df['is_high_vol']
    df['breakout_sell'] = (df['close'] < df['ema_20']) & ~df['is_high_vol']
    
    # Combined signals
    df['buy_signal'] = (df['mean_rev_buy'] | df['breakout_buy']) & df['optimal_hour']
    df['sell_signal'] = (df['mean_rev_sell'] | df['breakout_sell']) & df['optimal_hour']
    
    # Adaptive targets
    df['adaptive_target_pips'] = np.where(
        df['is_high_vol'],
        (df['atr'] / df['close'] * 10000 * 1.5).fillna(10),  # Mean reversion: 1.5x ATR
        (df['atr'] / df['close'] * 10000 * 2.0).fillna(12)   # Breakout: 2.0x ATR
    )
    df['adaptive_stop_pips'] = (df['atr'] / df['close'] * 10000 * 1.0).fillna(8)
    
    return df


def strategy_c_multi_factor(df):
    """
    Strategy C: Multi-Factor Model
    Combines best patterns:
    - Time of day (optimal hours)
    - Day of week (avoid Friday)
    - Volatility regime (high volatility)
    - RSI confirmation
    - Price action (trend alignment)
    """
    logger.info("Calculating Strategy C: Multi-Factor Model...")
    
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    
    # Calculate indicators
    df = df.set_index('datetime').sort_index()
    df['rsi_14'] = calculate_rsi(df, period=14)
    df['atr'] = calculate_atr(df, period=14)
    df['ema_9'] = df['close'].ewm(span=9).mean()
    df['ema_21'] = df['close'].ewm(span=21).mean()
    df = df.reset_index()
    
    # Volatility regime
    atr_median = df['atr'].median()
    df['is_high_vol'] = df['atr'] > atr_median
    
    # Time features
    df['hour'] = df['datetime'].dt.hour
    df['day_of_week'] = df['datetime'].dt.day_name()
    df['optimal_hour'] = df['hour'].isin(OPTIMAL_HOURS)
    df['avoid_day'] = df['day_of_week'].isin(AVOID_DAYS)
    
    # Price action: trend alignment
    df['uptrend'] = df['ema_9'] > df['ema_21']
    df['downtrend'] = df['ema_9'] < df['ema_21']
    
    # Previous candle direction
    df['prev_candle_up'] = df['close'] > df['close'].shift(1)
    df['prev_candle_down'] = df['close'] < df['close'].shift(1)
    
    # RSI signals
    df['rsi_oversold'] = df['rsi_14'] <= 30
    df['rsi_overbought'] = df['rsi_14'] >= 70
    
    # Multi-factor BUY signal (relaxed - most factors must align)
    df['buy_signal'] = (
        df['rsi_oversold'] &           # RSI confirmation (required)
        df['optimal_hour'] &            # Optimal time (required)
        ~df['avoid_day'] &              # Avoid bad days (required)
        df['is_high_vol'] &             # High volatility (required)
        (df['uptrend'] | df['prev_candle_down'])  # Trend OR mean reversion setup (either)
    )
    
    # Multi-factor SELL signal
    df['sell_signal'] = (
        df['rsi_overbought'] &         # RSI confirmation (required)
        df['optimal_hour'] &            # Optimal time (required)
        ~df['avoid_day'] &              # Avoid bad days (required)
        df['is_high_vol'] &             # High volatility (required)
        (df['downtrend'] | df['prev_candle_up'])  # Trend OR mean reversion setup (either)
    )
    
    # Adaptive targets
    df['adaptive_target_pips'] = (df['atr'] / df['close'] * 10000 * 1.5).fillna(10)
    df['adaptive_stop_pips'] = (df['atr'] / df['close'] * 10000 * 1.0).fillna(8)
    
    return df


def main():
    """Run all advanced strategies"""
    logger.info("=" * 70)
    logger.info("ADVANCED STRATEGY DESIGN - PATTERN-BASED")
    logger.info("=" * 70)
    
    # Load data
    df = pd.read_csv(config.DATA_FILE)
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    
    logger.info(f"Loaded {len(df)} price candles")
    
    # Calculate strategies
    strategies = {
        'A_TimeFilteredRSI': strategy_a_time_filtered_rsi,
        'B_RegimeSwitching': strategy_b_regime_switching,
        'C_MultiFactor': strategy_c_multi_factor
    }
    
    results = {}
    for name, func in strategies.items():
        logger.info(f"\nProcessing {name}...")
        try:
            result_df = func(df.copy())
            results[name] = result_df
            
            # Save signals
            output_file = f"data/eurusd_15min_6months_{name.lower()}_signals.csv"
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            result_df.to_csv(output_file, index=False)
            logger.info(f"Saved {name} signals to {output_file}")
            
            # Print signal counts
            buy_count = result_df['buy_signal'].sum()
            sell_count = result_df['sell_signal'].sum()
            logger.info(f"  BUY signals: {buy_count}, SELL signals: {sell_count}, Total: {buy_count + sell_count}")
            
        except Exception as e:
            logger.error(f"Error processing {name}: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
    
    logger.info("\n" + "=" * 70)
    logger.info("ADVANCED STRATEGY CALCULATION COMPLETE")
    logger.info("=" * 70)
    
    return results


if __name__ == "__main__":
    main()

