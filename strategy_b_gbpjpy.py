"""
Strategy B: Regime-Switching System for GBP/JPY
Same logic as EUR/USD but with GBP/JPY-specific parameters
"""

import pandas as pd
import numpy as np
import logging
import os
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pattern-based filters (optimal hours from EUR/USD analysis)
OPTIMAL_HOURS = [9, 10, 12, 14]  # Hours with 54%+ win rate
AVOID_HOURS = [13, 16]  # Hours to avoid


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


def strategy_b_regime_switching_gbpjpy(df):
    """
    Strategy B: Regime-Switching System for GBP/JPY
    
    HIGH VOLATILITY MODE (Mean Reversion):
    - BUY Signal: RSI(14) ≤ 30
    - SELL Signal: RSI(14) ≥ 70
    - Target: +1.5x ATR (in pips)
    - Stop Loss: -1.0x ATR (in pips)
    
    LOW VOLATILITY MODE (Breakout):
    - BUY Signal: Price closes above EMA(20)
    - SELL Signal: Price closes below EMA(20)
    - Target: +2.0x ATR (in pips)
    - Stop Loss: -1.0x ATR (in pips)
    
    TIME FILTERING:
    - Only trade during hours: 9, 10, 12, 14 (UTC)
    - Avoid hours: 13, 16
    """
    logger.info("Calculating Strategy B (Regime-Switching) for GBP/JPY...")
    
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    
    # Calculate indicators
    df = df.set_index('datetime').sort_index()
    df['rsi_14'] = calculate_rsi(df, period=14)
    df['atr'] = calculate_atr(df, period=14)
    
    # Calculate EMA for breakout detection
    df['ema_20'] = df['close'].ewm(span=20).mean()
    df = df.reset_index()
    
    # Volatility regime (using median ATR of last 20 periods as specified)
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
    
    # Combined signals with time filtering
    df['buy_signal'] = (df['mean_rev_buy'] | df['breakout_buy']) & df['optimal_hour'] & ~df['avoid_hour']
    df['sell_signal'] = (df['mean_rev_sell'] | df['breakout_sell']) & df['optimal_hour'] & ~df['avoid_hour']
    
    # Adaptive targets based on ATR
    # For GBP/JPY, pip value is different (0.01 instead of 0.0001 for JPY pairs)
    # But we'll calculate in pips: ATR in price * 100 (since GBP/JPY is typically 150-200 range)
    df['atr_pips'] = (df['atr'] * 100).fillna(0)  # Convert ATR to pips approximation
    
    df['adaptive_target_pips'] = np.where(
        df['is_high_vol'],
        df['atr_pips'] * 1.5,  # Mean reversion: 1.5x ATR
        df['atr_pips'] * 2.0   # Breakout: 2.0x ATR
    )
    df['adaptive_stop_pips'] = df['atr_pips'] * 1.0  # Stop: 1.0x ATR
    
    # Set minimum targets/stops
    df['adaptive_target_pips'] = df['adaptive_target_pips'].clip(lower=10)
    df['adaptive_stop_pips'] = df['adaptive_stop_pips'].clip(lower=8)
    
    return df


def main():
    """Main function"""
    logger.info("=" * 70)
    logger.info("STRATEGY B: REGIME-SWITCHING FOR GBP/JPY")
    logger.info("=" * 70)
    
    # Load data (try different file locations)
    data_files = [
        "data/gbpjpy_15min_6months.csv",
        "data/gbpjpy_15min.csv",
    ]
    
    df = None
    for data_file in data_files:
        if os.path.exists(data_file):
            logger.info(f"Loading GBP/JPY data from {data_file}...")
            df = pd.read_csv(data_file)
            logger.info(f"Loaded {len(df)} 15-minute candles")
            break
    
    if df is None:
        logger.error("GBP/JPY data file not found!")
        logger.error("Please ensure data file exists at one of:")
        for f in data_files:
            logger.error(f"  - {f}")
        logger.error("\nTo download data, run: python histdata_downloader_gbpjpy.py")
        return
    
    # Calculate Strategy B signals
    result_df = strategy_b_regime_switching_gbpjpy(df)
    
    # Save signals
    output_file = "data/gbpjpy_15min_6months_strategy_b_signals.csv"
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
    print("STRATEGY B (GBP/JPY) SIGNAL SUMMARY")
    print("=" * 70)
    print(f"Total candles: {len(result_df)}")
    print(f"BUY signals: {buy_count}")
    print(f"SELL signals: {sell_count}")
    print(f"Total signals: {buy_count + sell_count}")
    print(f"Mean Reversion: {mean_rev_count}")
    print(f"Breakout: {breakout_count}")
    print("=" * 70)


if __name__ == "__main__":
    main()























