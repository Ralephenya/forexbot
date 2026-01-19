"""
Apply Strategy B to all pairs (EUR/USD, GBP/USD, USD/JPY)
"""

import pandas as pd
import numpy as np
import logging
import os
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pattern-based filters
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


def strategy_b_regime_switching(df):
    """
    Strategy B: Regime-Switching System
    Same logic for all pairs
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
    
    # Adaptive targets
    # For JPY pairs, pip value is 0.01, for others it's 0.0001
    # We'll calculate in pips based on pair type (detected by price range)
    avg_price = df['close'].mean()
    if avg_price > 100:  # JPY pair (USD/JPY typically 150-160)
        pip_multiplier = 100  # 1 pip = 0.01
    else:  # EUR/USD, GBP/USD (typically 1.0-1.3)
        pip_multiplier = 10000  # 1 pip = 0.0001
    
    df['atr_pips'] = (df['atr'] * pip_multiplier).fillna(0)
    
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


def process_pair(pair_name, data_file):
    """Process a single pair"""
    logger.info(f"\n{'='*70}")
    logger.info(f"Processing {pair_name.upper()}")
    logger.info(f"{'='*70}")
    
    if not os.path.exists(data_file):
        logger.error(f"Data file not found: {data_file}")
        return None
    
    # Load data
    logger.info(f"Loading data from {data_file}...")
    df = pd.read_csv(data_file)
    logger.info(f"Loaded {len(df)} candles")
    
    # Calculate Strategy B signals
    result_df = strategy_b_regime_switching(df)
    
    # Save signals
    output_file = f"data/{pair_name}_15min_6months_strategy_b_signals.csv"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    result_df.to_csv(output_file, index=False)
    logger.info(f"Saved signals to {output_file}")
    
    # Print signal counts
    buy_count = result_df['buy_signal'].sum()
    sell_count = result_df['sell_signal'].sum()
    logger.info(f"BUY signals: {buy_count}, SELL signals: {sell_count}, Total: {buy_count + sell_count}")
    
    return output_file


def main():
    """Process all pairs"""
    logger.info("=" * 70)
    logger.info("APPLYING STRATEGY B TO ALL PAIRS")
    logger.info("=" * 70)
    
    # Define pairs and their data files
    pairs = {
        'eurusd': 'data/eurusd_15min_6months.csv',
        'gbpusd': 'data/gbpusd_15min_6months.csv',
        'usdjpy': 'data/usdjpy_15min_6months.csv'
    }
    
    results = {}
    for pair_name, data_file in pairs.items():
        signal_file = process_pair(pair_name, data_file)
        if signal_file:
            results[pair_name] = signal_file
    
    # Summary
    print("\n" + "=" * 70)
    print("STRATEGY B SIGNAL GENERATION COMPLETE")
    print("=" * 70)
    for pair, file in results.items():
        if file and os.path.exists(file):
            print(f"{pair.upper()}: {file}")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    main()























