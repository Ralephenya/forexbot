"""
Phase 1: Hour-by-hour performance analysis for AUD/USD
Test Strategy B signals across ALL hours to find optimal trading times
"""

import pandas as pd
import numpy as np
import logging
import os
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


def generate_strategy_b_signals_no_time_filter(df):
    """
    Generate Strategy B signals WITHOUT time filtering
    This allows us to analyze performance by hour
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
    
    # Mean reversion signals (high volatility)
    df['mean_rev_buy'] = (df['rsi_14'] <= 30) & df['is_high_vol']
    df['mean_rev_sell'] = (df['rsi_14'] >= 70) & df['is_high_vol']
    
    # Breakout signals (low volatility)
    df['breakout_buy'] = (df['close'] > df['ema_20']) & ~df['is_high_vol']
    df['breakout_sell'] = (df['close'] < df['ema_20']) & ~df['is_high_vol']
    
    # Combined signals (NO time filtering here - we'll analyze by hour)
    df['buy_signal'] = df['mean_rev_buy'] | df['breakout_buy']
    df['sell_signal'] = df['mean_rev_sell'] | df['breakout_sell']
    
    # Adaptive targets
    pip_multiplier = 10000  # AUD/USD: 1 pip = 0.0001
    df['adaptive_target_pips'] = np.where(
        df['is_high_vol'],
        df['atr'] * pip_multiplier * 1.5,  # Mean reversion: 1.5x ATR
        df['atr'] * pip_multiplier * 2.0   # Breakout: 2.0x ATR
    )
    df['adaptive_stop_pips'] = df['atr'] * pip_multiplier * 1.0
    
    # Add hour column for analysis
    df['hour'] = df['datetime'].dt.hour
    
    return df


def simulate_trades_by_hour(df, spread_pips=1.5):
    """
    Simulate trades for each hour to measure performance
    Simplified simulation - just counts signals and estimates win rate based on volatility
    """
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    
    # Generate signals
    df = generate_strategy_b_signals_no_time_filter(df)
    
    # Group by hour
    hour_stats = []
    
    for hour in range(24):
        hour_data = df[df['hour'] == hour].copy()
        
        if len(hour_data) == 0:
            continue
        
        # Count signals
        buy_signals = hour_data['buy_signal'].sum()
        sell_signals = hour_data['sell_signal'].sum()
        total_signals = buy_signals + sell_signals
        
        if total_signals == 0:
            continue
        
        # Calculate average volatility and targets for this hour
        avg_atr = hour_data['atr'].mean()
        avg_target_pips = hour_data['adaptive_target_pips'].mean()
        avg_stop_pips = hour_data['adaptive_stop_pips'].mean()
        
        # Estimate potential edge (simplified)
        # Higher ATR = more opportunities for mean reversion
        avg_volatility = hour_data['atr'].mean()
        
        # Session labels
        session = get_session_label(hour)
        
        hour_stats.append({
            'hour': hour,
            'session': session,
            'total_signals': total_signals,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'avg_atr': avg_atr,
            'avg_target_pips': avg_target_pips,
            'avg_stop_pips': avg_stop_pips,
            'avg_volatility': avg_volatility,
            'candles': len(hour_data)
        })
    
    return pd.DataFrame(hour_stats)


def get_session_label(hour_utc):
    """Get trading session label for UTC hour"""
    # Sydney: 22:00-07:00 UTC (AEST = UTC+10, but DST can vary)
    # Tokyo: 00:00-09:00 UTC
    # London: 08:00-17:00 UTC
    # New York: 13:00-22:00 UTC
    
    if 22 <= hour_utc or hour_utc < 7:
        return 'Sydney'
    elif 7 <= hour_utc < 9:
        return 'Sydney/Tokyo Overlap'
    elif 9 <= hour_utc < 13:
        return 'Tokyo'
    elif 13 <= hour_utc < 17:
        return 'London/New York Overlap'
    elif 17 <= hour_utc < 22:
        return 'New York'
    else:
        return 'Low Liquidity'


def main():
    """Main function"""
    logger.info("=" * 70)
    logger.info("PHASE 1: AUD/USD HOUR-BY-HOUR ANALYSIS")
    logger.info("=" * 70)
    
    # Load data (try both full data and yfinance data)
    data_file = 'data/audusd_15min_6months.csv'
    if not os.path.exists(data_file):
        data_file = 'data/audusd_15min_yfinance.csv'
        if not os.path.exists(data_file):
            logger.error(f"Data file not found. Please run histdata_downloader_audusd.py or quick_audusd_test.py")
            return
        else:
            logger.info("Using yfinance data (60-day limit) for quick test")
    else:
        logger.info("Using full 7-month HistData.com data")
    
    logger.info(f"Loading data from {data_file}...")
    df = pd.read_csv(data_file)
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    logger.info(f"Loaded {len(df)} candles")
    
    # Generate signals (no time filter)
    logger.info("Generating Strategy B signals (no time filter)...")
    df = generate_strategy_b_signals_no_time_filter(df)
    
    # Analyze by hour
    logger.info("Analyzing performance by hour...")
    hour_stats = simulate_trades_by_hour(df, spread_pips=1.5)
    
    # Sort by total signals (most active hours first)
    hour_stats = hour_stats.sort_values('total_signals', ascending=False)
    
    # Save results
    output_file = 'results/audusd_hour_analysis.csv'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    hour_stats.to_csv(output_file, index=False)
    
    # Print results
    print("\n" + "=" * 90)
    print("AUD/USD HOUR-BY-HOUR SIGNAL ANALYSIS")
    print("=" * 90)
    print(hour_stats.to_string(index=False))
    print("=" * 90)
    
    # Summary by session
    print("\n" + "=" * 90)
    print("SUMMARY BY SESSION")
    print("=" * 90)
    session_summary = hour_stats.groupby('session').agg({
        'total_signals': 'sum',
        'avg_volatility': 'mean',
        'avg_target_pips': 'mean'
    }).sort_values('total_signals', ascending=False)
    print(session_summary.to_string())
    print("=" * 90)
    
    # Top hours by signal count
    print("\n" + "=" * 90)
    print("TOP 10 HOURS BY SIGNAL COUNT")
    print("=" * 90)
    top_hours = hour_stats.head(10)[['hour', 'session', 'total_signals', 'buy_signals', 'sell_signals', 'avg_volatility']]
    print(top_hours.to_string(index=False))
    print("=" * 90)
    
    logger.info(f"Results saved to {output_file}")
    
    return hour_stats


if __name__ == "__main__":
    main()


