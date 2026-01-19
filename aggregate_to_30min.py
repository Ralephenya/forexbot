"""
Aggregate 15-minute EUR/USD data to 30-minute candles
"""

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def aggregate_to_30min(df_15min):
    """
    Aggregate 15-minute data to 30-minute candles
    
    Args:
        df_15min: DataFrame with 15-minute OHLCV data
    
    Returns:
        DataFrame with 30-minute OHLCV data
    """
    logger.info(f"Aggregating {len(df_15min)} 15-minute candles to 30-minute candles...")
    
    df = df_15min.copy()
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    df = df.sort_values('datetime').reset_index(drop=True)
    
    # Set datetime as index for resampling
    df_indexed = df.set_index('datetime')
    
    # Resample to 30-minute candles
    hourly_df = df_indexed.resample('30min').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last'
    }).reset_index()
    
    # Remove any rows with NaN (incomplete periods)
    hourly_df = hourly_df.dropna().reset_index(drop=True)
    
    logger.info(f"Aggregated to {len(hourly_df)} 30-minute candles")
    logger.info(f"Date range: {hourly_df['datetime'].min()} to {hourly_df['datetime'].max()}")
    
    return hourly_df


def main():
    """Main function"""
    logger.info("=" * 70)
    logger.info("AGGREGATING 15-MINUTE DATA TO 30-MINUTE")
    logger.info("=" * 70)
    
    # Load 15-minute data
    data_file = "data/eurusd_15min_6months.csv"
    logger.info(f"Loading 15-minute data from {data_file}...")
    
    df_15min = pd.read_csv(data_file)
    logger.info(f"Loaded {len(df_15min)} 15-minute candles")
    
    # Aggregate to 30-minute
    df_30min = aggregate_to_30min(df_15min)
    
    # Save 30-minute data
    output_file = "data/eurusd_30min_6months.csv"
    df_30min.to_csv(output_file, index=False)
    logger.info(f"Saved 30-minute data to {output_file}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("AGGREGATION SUMMARY")
    print("=" * 70)
    print(f"15-minute candles: {len(df_15min)}")
    print(f"30-minute candles: {len(df_30min)}")
    print(f"Compression ratio: {len(df_15min) / len(df_30min):.2f}x")
    print(f"Date range: {df_30min['datetime'].min()} to {df_30min['datetime'].max()}")
    print("=" * 70)


if __name__ == "__main__":
    main()























