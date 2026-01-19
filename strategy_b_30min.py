"""
Strategy B: Regime-Switching System for EUR/USD 30-Minute
Same logic as 15-minute version
"""

import pandas as pd
import numpy as np
import logging
import os
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pattern-based filters (same as 15-minute)
OPTIMAL_HOURS = [9, 10, 12, 14]
AVOID_HOURS = [13, 16]


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


def strategy_b_regime_switching_30min(df):
    """
    Strategy B: Regime-Switching System (30-Minute Version)
    EXACT SAME LOGIC as 15-minute version
    """
    logger.info("Calculating Strategy B (Regime-Switching) for 30-minute timeframe...")
    
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    
    # Calculate indicators
    df = df.set_index('datetime').sort_index()
    df['rsi_14'] = calculate_rsi(df, period=14)
    df['atr'] = calculate_atr(df, period=14)
    
    # Calculate EMA for breakout detection
    df['ema_20'] = df['close'].ewm(span=20).mean()
    df = df.reset_index()
    
    # Volatility regime (median of last 20 periods)
    df['atr_median'] = df['atr'].rolling(window=20).median()
    df['is_high_vol'] = df['atr'] > df['atr_median']
    
    # Time filters
    df['hour'] = df['datetime'].dt.hour
    df['optimal_hour'] = df['hour'].isin(OPTIMAL_HOURS)
    df['avoid_hour'] = df['hour'].isin(AVOID_HOURS)
    
    # Mean reversion signals (high volatility)
    df['mean_rev_buy'] = (df['rsi_14'] <= 30) & df['is_high_vol']
    df['mean_rev_sell'] = (df['rsi_14'] >= 70) & df['is_high_vol']
    
    # Breakout signals (low volatility)
    df['breakout_buy'] = (df['close'] > df['ema_20']) & ~df['is_high_vol']
    df['breakout_sell'] = (df['close'] < df['ema_20']) & ~df['is_high_vol']
    
    # Combined signals
    df['buy_signal'] = (df['mean_rev_buy'] | df['breakout_buy']) & df['optimal_hour'] & ~df['avoid_hour']
    df['sell_signal'] = (df['mean_rev_sell'] | df['breakout_sell']) & df['optimal_hour'] & ~df['avoid_hour']
    
    # Adaptive targets (EUR/USD: pip multiplier = 10000)
    df['atr_pips'] = (df['atr'] * 10000).fillna(0)
    
    df['adaptive_target_pips'] = np.where(
        df['is_high_vol'],
        df['atr_pips'] * 1.5,  # Mean reversion: 1.5x ATR
        df['atr_pips'] * 2.0   # Breakout: 2.0x ATR
    )
    df['adaptive_stop_pips'] = df['atr_pips'] * 1.0
    
    # Set minimum targets/stops
    df['adaptive_target_pips'] = df['adaptive_target_pips'].clip(lower=10)
    df['adaptive_stop_pips'] = df['adaptive_stop_pips'].clip(lower=8)
    
    return df


def main():
    """Main function"""
    logger.info("=" * 70)
    logger.info("STRATEGY B: REGIME-SWITCHING (30-MINUTE TIMEFRAME)")
    logger.info("=" * 70)
    
    # Load 30-minute data
    data_file = "data/eurusd_30min_6months.csv"
    logger.info(f"Loading 30-minute data from {data_file}...")
    
    if not os.path.exists(data_file):
        logger.error(f"Data file not found: {data_file}")
        logger.info("Please run: python aggregate_to_30min.py first")
        return
    
    df = pd.read_csv(data_file)
    logger.info(f"Loaded {len(df)} 30-minute candles")
    
    # Calculate Strategy B signals
    result_df = strategy_b_regime_switching_30min(df)
    
    # Save signals
    output_file = "data/eurusd_30min_6months_strategy_b_signals.csv"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    result_df.to_csv(output_file, index=False)
    logger.info(f"Saved Strategy B signals to {output_file}")
    
    # Print signal counts
    buy_count = result_df['buy_signal'].sum()
    sell_count = result_df['sell_signal'].sum()
    mean_rev_count = (result_df['mean_rev_buy'] | result_df['mean_rev_sell']).sum()
    breakout_count = (result_df['breakout_buy'] | result_df['breakout_sell']).sum()
    
    logger.info(f"BUY signals: {buy_count}, SELL signals: {sell_count}, Total: {buy_count + sell_count}")
    logger.info(f"Mean Reversion signals: {mean_rev_count}, Breakout signals: {breakout_count}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("STRATEGY B (30-MINUTE) SIGNAL SUMMARY")
    print("=" * 70)
    print(f"Total candles: {len(result_df)}")
    print(f"BUY signals: {buy_count}")
    print(f"SELL signals: {sell_count}")
    print(f"Total signals: {buy_count + sell_count}")
    print(f"Signals per day: {(buy_count + sell_count) / len(result_df) * 48:.2f}")
    print("=" * 70)


if __name__ == "__main__":
    main()























