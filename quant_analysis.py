"""
Quantitative Market Analysis - Pattern Discovery
Analyzes EUR/USD 15-minute data for hidden inefficiencies
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load data
DATA_FILE = "data/eurusd_15min_6months.csv"
RSI_TRADES_FILE = "results/backtest_results_6months.csv"


def load_data():
    """Load price data and trade results"""
    logger.info("Loading data...")
    
    # Load price data
    df = pd.read_csv(DATA_FILE)
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    df = df.sort_values('datetime').reset_index(drop=True)
    
    # Load RSI trade results
    trades_df = pd.read_csv(RSI_TRADES_FILE)
    trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'], utc=True)
    trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'], utc=True)
    
    logger.info(f"Loaded {len(df)} price candles and {len(trades_df)} trades")
    
    return df, trades_df


def calculate_atr(df, period=14):
    """Calculate Average True Range (ATR)"""
    df = df.copy()
    df['prev_close'] = df['close'].shift(1)
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = abs(df['high'] - df['prev_close'])
    df['tr3'] = abs(df['low'] - df['prev_close'])
    df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
    df['atr'] = df['tr'].rolling(window=period).mean()
    return df['atr']


def analyze_time_of_day(df, trades_df):
    """Analyze performance by hour of day"""
    logger.info("Analyzing time-of-day patterns...")
    
    # Merge trades with price data to get entry hour
    trades_with_hour = trades_df.copy()
    trades_with_hour['entry_hour'] = trades_with_hour['entry_time'].dt.hour
    
    # Group by hour
    hourly_stats = trades_with_hour.groupby('entry_hour').agg({
        'pnl': ['count', 'sum', 'mean'],
        'pips': 'mean'
    }).reset_index()
    hourly_stats.columns = ['hour', 'trades', 'total_pnl', 'avg_pnl', 'avg_pips']
    
    # Calculate win rate by hour
    hourly_stats['win_rate'] = trades_with_hour.groupby('entry_hour').apply(
        lambda x: (x['pnl'] > 0).sum() / len(x) * 100
    ).values
    
    # Sort by total P&L
    hourly_stats = hourly_stats.sort_values('total_pnl', ascending=False)
    
    return hourly_stats


def analyze_volatility_regimes(df, trades_df):
    """Analyze performance by volatility regime"""
    logger.info("Analyzing volatility regimes...")
    
    # Calculate ATR
    df['atr'] = calculate_atr(df, period=14)
    df['atr_pct'] = (df['atr'] / df['close']) * 10000  # ATR in pips
    
    # Categorize volatility regimes
    atr_median = df['atr_pct'].median()
    atr_25th = df['atr_pct'].quantile(0.25)
    atr_75th = df['atr_pct'].quantile(0.75)
    
    def categorize_volatility(atr_val):
        if pd.isna(atr_val):
            return 'Unknown'
        elif atr_val < atr_25th:
            return 'Low'
        elif atr_val < atr_75th:
            return 'Medium'
        else:
            return 'High'
    
    df['volatility_regime'] = df['atr_pct'].apply(categorize_volatility)
    
    # Merge trades with volatility data
    trades_with_vol = trades_df.copy()
    # Get volatility at entry time
    entry_vol = []
    for idx, trade in trades_df.iterrows():
        entry_time = trade['entry_time']
        # Find closest candle
        closest_idx = df['datetime'].sub(entry_time).abs().idxmin()
        vol_regime = df.loc[closest_idx, 'volatility_regime']
        entry_vol.append(vol_regime)
    
    trades_with_vol['volatility_regime'] = entry_vol
    
    # Group by volatility regime
    vol_stats = trades_with_vol.groupby('volatility_regime').agg({
        'pnl': ['count', 'sum', 'mean'],
        'pips': 'mean'
    }).reset_index()
    vol_stats.columns = ['regime', 'trades', 'total_pnl', 'avg_pnl', 'avg_pips']
    
    # Calculate win rate by regime
    vol_stats['win_rate'] = trades_with_vol.groupby('volatility_regime').apply(
        lambda x: (x['pnl'] > 0).sum() / len(x) * 100
    ).values
    
    return vol_stats, df


def analyze_day_of_week(df, trades_df):
    """Analyze performance by day of week"""
    logger.info("Analyzing day-of-week patterns...")
    
    trades_with_dow = trades_df.copy()
    trades_with_dow['day_of_week'] = trades_with_dow['entry_time'].dt.day_name()
    
    # Group by day of week
    dow_stats = trades_with_dow.groupby('day_of_week').agg({
        'pnl': ['count', 'sum', 'mean'],
        'pips': 'mean'
    }).reset_index()
    dow_stats.columns = ['day', 'trades', 'total_pnl', 'avg_pnl', 'avg_pips']
    
    # Calculate win rate
    dow_stats['win_rate'] = trades_with_dow.groupby('day_of_week').apply(
        lambda x: (x['pnl'] > 0).sum() / len(x) * 100
    ).values
    
    # Order by day of week
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    dow_stats['day_order'] = dow_stats['day'].apply(lambda x: day_order.index(x) if x in day_order else 99)
    dow_stats = dow_stats.sort_values('day_order').drop('day_order', axis=1)
    
    return dow_stats


def analyze_price_action(df, trades_df):
    """Analyze price action patterns before trades"""
    logger.info("Analyzing price action patterns...")
    
    # For each trade, look at candles before entry
    patterns = []
    
    for idx, trade in trades_df.iterrows():
        entry_time = trade['entry_time']
        direction = trade['direction']
        pnl = trade['pnl']
        
        # Find entry candle
        entry_idx = df[df['datetime'] <= entry_time].index[-1] if len(df[df['datetime'] <= entry_time]) > 0 else None
        
        if entry_idx is None or entry_idx < 3:
            continue
        
        # Get previous 3 candles
        prev_candles = df.iloc[entry_idx-3:entry_idx+1]
        
        # Calculate patterns
        pattern = {
            'direction': direction,
            'pnl': pnl,
            'is_winner': pnl > 0,
            'prev_3_direction': (prev_candles.iloc[-2]['close'] > prev_candles.iloc[-3]['close']),
            'prev_2_direction': (prev_candles.iloc[-1]['close'] > prev_candles.iloc[-2]['close']),
            'prev_3_body_size': abs(prev_candles.iloc[-2]['close'] - prev_candles.iloc[-2]['open']),
            'prev_2_body_size': abs(prev_candles.iloc[-1]['close'] - prev_candles.iloc[-1]['open']),
            'prev_3_wick_ratio': (prev_candles.iloc[-2]['high'] - prev_candles.iloc[-2]['low']) / abs(prev_candles.iloc[-2]['close'] - prev_candles.iloc[-2]['open']) if abs(prev_candles.iloc[-2]['close'] - prev_candles.iloc[-2]['open']) > 0 else 0,
        }
        
        patterns.append(pattern)
    
    patterns_df = pd.DataFrame(patterns)
    
    # Analyze winning vs losing patterns
    winning = patterns_df[patterns_df['is_winner']]
    losing = patterns_df[~patterns_df['is_winner']]
    
    return patterns_df, winning, losing


def analyze_correlations(df, trades_df):
    """Find predictive correlations"""
    logger.info("Analyzing correlations...")
    
    # Calculate features
    df = df.copy()
    df['hour'] = df['datetime'].dt.hour
    df['day_of_week'] = df['datetime'].dt.dayofweek
    df['prev_hour_move'] = df['close'].shift(4) - df['close'].shift(8)  # 4 candles = 1 hour
    df['distance_from_open'] = df['close'] - df.groupby(df['datetime'].dt.date)['open'].transform('first')
    df['daily_range'] = df.groupby(df['datetime'].dt.date)['high'].transform('max') - df.groupby(df['datetime'].dt.date)['low'].transform('min')
    df['atr'] = calculate_atr(df, period=14)
    
    # Merge with trades
    correlations = []
    
    for idx, trade in trades_df.iterrows():
        entry_time = trade['entry_time']
        closest_idx = df['datetime'].sub(entry_time).abs().idxmin()
        
        if closest_idx < 10:  # Need history
            continue
        
        row = df.iloc[closest_idx]
        correlations.append({
            'pnl': trade['pnl'],
            'hour': row['hour'],
            'day_of_week': row['day_of_week'],
            'prev_hour_move': row['prev_hour_move'],
            'distance_from_open': row['distance_from_open'],
            'daily_range': row['daily_range'],
            'atr': row['atr']
        })
    
    corr_df = pd.DataFrame(correlations)
    
    return corr_df


def analyze_drawdowns(trades_df):
    """Analyze losing streak patterns"""
    logger.info("Analyzing drawdown patterns...")
    
    trades_df = trades_df.sort_values('exit_time').reset_index(drop=True)
    trades_df['cumulative_pnl'] = trades_df['pnl'].cumsum()
    trades_df['running_max'] = trades_df['cumulative_pnl'].cummax()
    trades_df['drawdown'] = trades_df['cumulative_pnl'] - trades_df['running_max']
    
    # Find losing streaks
    trades_df['is_loss'] = trades_df['pnl'] < 0
    trades_df['streak_id'] = (trades_df['is_loss'] != trades_df['is_loss'].shift()).cumsum()
    
    losing_streaks = trades_df[trades_df['is_loss']].groupby('streak_id').agg({
        'pnl': ['count', 'sum'],
        'exit_time': ['min', 'max']
    })
    
    return trades_df, losing_streaks


def main():
    """Run all quantitative analyses"""
    logger.info("=" * 70)
    logger.info("QUANTITATIVE MARKET ANALYSIS - PATTERN DISCOVERY")
    logger.info("=" * 70)
    
    # Load data
    df, trades_df = load_data()
    
    # Run analyses
    results = {}
    
    # 1. Time of day
    logger.info("\n" + "=" * 70)
    logger.info("PHASE 1: PATTERN DISCOVERY")
    logger.info("=" * 70)
    
    hourly_stats = analyze_time_of_day(df, trades_df)
    results['hourly'] = hourly_stats
    
    # 2. Volatility regimes
    vol_stats, df_with_vol = analyze_volatility_regimes(df, trades_df)
    results['volatility'] = vol_stats
    
    # 3. Day of week
    dow_stats = analyze_day_of_week(df, trades_df)
    results['day_of_week'] = dow_stats
    
    # 4. Price action
    patterns_df, winning_patterns, losing_patterns = analyze_price_action(df, trades_df)
    results['price_action'] = {
        'all': patterns_df,
        'winning': winning_patterns,
        'losing': losing_patterns
    }
    
    # 5. Correlations
    corr_df = analyze_correlations(df, trades_df)
    results['correlations'] = corr_df
    
    # 6. Drawdowns
    trades_with_dd, losing_streaks = analyze_drawdowns(trades_df)
    results['drawdowns'] = {
        'trades': trades_with_dd,
        'streaks': losing_streaks
    }
    
    # Save results
    os.makedirs("results/quant_analysis", exist_ok=True)
    
    hourly_stats.to_csv("results/quant_analysis/hourly_performance.csv", index=False)
    vol_stats.to_csv("results/quant_analysis/volatility_regimes.csv", index=False)
    dow_stats.to_csv("results/quant_analysis/day_of_week_performance.csv", index=False)
    patterns_df.to_csv("results/quant_analysis/price_action_patterns.csv", index=False)
    corr_df.to_csv("results/quant_analysis/correlations.csv", index=False)
    trades_with_dd.to_csv("results/quant_analysis/trades_with_drawdown.csv", index=False)
    
    logger.info("\n" + "=" * 70)
    logger.info("ANALYSIS COMPLETE")
    logger.info("=" * 70)
    logger.info("Results saved to results/quant_analysis/")
    
    # Print key findings
    print("\n" + "=" * 70)
    print("KEY FINDINGS")
    print("=" * 70)
    
    print("\n1. BEST TRADING HOURS (by Total P&L):")
    print(hourly_stats.head(5).to_string(index=False))
    
    print("\n2. VOLATILITY REGIME PERFORMANCE:")
    print(vol_stats.to_string(index=False))
    
    print("\n3. DAY-OF-WEEK PERFORMANCE:")
    print(dow_stats.to_string(index=False))
    
    return results


if __name__ == "__main__":
    main()























