"""
Aggregate 15-minute EUR/USD data to 1-hour candles
"""

import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def aggregate_to_hourly(df_15min):
    """
    Aggregate 15-minute data to 1-hour candles
    
    Args:
        df_15min: DataFrame with 15-minute OHLCV data
    
    Returns:
        DataFrame with 1-hour OHLCV data
    """
    logger.info(f"Aggregating {len(df_15min)} 15-minute candles to 1-hour candles...")
    
    df = df_15min.copy()
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    df = df.sort_values('datetime').reset_index(drop=True)
    
    # Set datetime as index for resampling
    df_indexed = df.set_index('datetime')
    
    # Resample to 1-hour candles
    agg_dict = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last'
    }
    
    # Add volume if it exists
    if 'volume' in df.columns:
        agg_dict['volume'] = 'sum'
    
    hourly_df = df_indexed.resample('1h').agg(agg_dict).reset_index()
    
    # Remove any rows with NaN (incomplete hours)
    hourly_df = hourly_df.dropna().reset_index(drop=True)
    
    logger.info(f"Aggregated to {len(hourly_df)} 1-hour candles")
    logger.info(f"Date range: {hourly_df['datetime'].min()} to {hourly_df['datetime'].max()}")
    
    return hourly_df


def main():
    """Main function"""
    logger.info("=" * 70)
    logger.info("AGGREGATING 15-MINUTE DATA TO 1-HOUR")
    logger.info("=" * 70)
    
    # Load 15-minute data
    data_file = "data/eurusd_15min_6months.csv"
    logger.info(f"Loading 15-minute data from {data_file}...")
    
    df_15min = pd.read_csv(data_file)
    logger.info(f"Loaded {len(df_15min)} 15-minute candles")
    
    # Aggregate to hourly
    hourly_df = aggregate_to_hourly(df_15min)
    
    # Save hourly data
    output_file = "data/eurusd_1hour_6months.csv"
    hourly_df.to_csv(output_file, index=False)
    logger.info(f"Saved 1-hour data to {output_file}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("AGGREGATION SUMMARY")
    print("=" * 70)
    print(f"15-minute candles: {len(df_15min)}")
    print(f"1-hour candles: {len(hourly_df)}")
    print(f"Compression ratio: {len(df_15min) / len(hourly_df):.2f}x")
    print(f"Date range: {hourly_df['datetime'].min()} to {hourly_df['datetime'].max()}")
    print("=" * 70)


if __name__ == "__main__":
    main()

