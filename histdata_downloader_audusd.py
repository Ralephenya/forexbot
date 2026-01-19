"""
Download AUD/USD 1-minute data from HistData.com and aggregate to 15-minute
"""

import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime
import zipfile
import glob

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATA_DIR = "data/histdata"
SYMBOL = 'AUDUSD'

# Create data directory
os.makedirs(DATA_DIR, exist_ok=True)


def find_year_zip_file(year, symbol):
    """Find ZIP file for a given year and symbol"""
    patterns = [
        f"DAT_ASCII_{symbol.upper()}_M{year}*.zip",  # M2024 format
        f"DAT_ASCII_{symbol.upper()}_M1_{year}*.zip",  # M1_2024 format
    ]
    
    search_dirs = [
        DATA_DIR,
        os.path.join(os.getcwd(), "data"),
        os.getcwd(),  # Current directory
    ]
    
    for search_dir in search_dirs:
        for pattern in patterns:
            pattern_path = os.path.join(search_dir, pattern) if search_dir else pattern
            files = glob.glob(pattern_path)
            if files:
                return files[0]
    
    return None


def load_histdata_zip(zip_path):
    """
    Load 1-minute data from HistData ZIP file
    
    HistData CSV format (5 fields):
    Date;Time;Open;High;Low;Close
    
    Returns DataFrame with datetime index
    """
    logger.info(f"Loading data from {zip_path}...")
    
    data_frames = []
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        file_list = zip_ref.namelist()
        csv_files = [f for f in file_list if f.endswith('.csv')]
        
        logger.info(f"Found {len(csv_files)} CSV files in ZIP")
        
        for csv_file in csv_files:
            try:
                with zip_ref.open(csv_file) as f:
                    # Read CSV - skip header, use semicolon separator
                    df = pd.read_csv(f, sep=';', header=None, 
                                    names=['Date', 'Time', 'Open', 'High', 'Low', 'Close'],
                                    skiprows=1)
                    
                    # Combine Date and Time into datetime
                    df['datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], 
                                                    format='%Y%m%d %H%M%S', 
                                                    utc=True)
                    
                    # Drop original Date and Time columns
                    df = df.drop(['Date', 'Time'], axis=1)
                    
                    # Select OHLC columns
                    df = df[['datetime', 'Open', 'High', 'Low', 'Close']]
                    
                    # Convert to numeric
                    for col in ['Open', 'High', 'Low', 'Close']:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    # Drop rows with NaN
                    df = df.dropna()
                    
                    data_frames.append(df)
                    
            except Exception as e:
                logger.warning(f"Error reading {csv_file}: {str(e)}")
                continue
    
    if not data_frames:
        logger.error("No data loaded from ZIP file")
        return None
    
    # Combine all DataFrames
    combined_df = pd.concat(data_frames, ignore_index=True)
    
    # Sort by datetime
    combined_df = combined_df.sort_values('datetime').reset_index(drop=True)
    
    # Filter by date range if specified
    if start_date:
        combined_df = combined_df[combined_df['datetime'] >= start_date]
    if end_date:
        combined_df = combined_df[combined_df['datetime'] <= end_date]
    
    logger.info(f"Loaded {len(combined_df)} 1-minute candles")
    logger.info(f"Date range: {combined_df['datetime'].min()} to {combined_df['datetime'].max()}")
    
    return combined_df


def aggregate_to_15min(df):
    """
    Aggregate 1-minute data to 15-minute candles
    """
    logger.info("Aggregating to 15-minute candles...")
    
    # Set datetime as index for resampling
    df = df.set_index('datetime').sort_index()
    
    # Resample to 15 minutes
    df_15min = pd.DataFrame()
    df_15min['open'] = df['Open'].resample('15T').first()
    df_15min['high'] = df['High'].resample('15T').max()
    df_15min['low'] = df['Low'].resample('15T').min()
    df_15min['close'] = df['Close'].resample('15T').last()
    
    # Add volume (use tick count - number of 1-min candles in 15-min period)
    df_15min['volume'] = df['Open'].resample('15T').count()
    
    # Reset index
    df_15min = df_15min.reset_index()
    df_15min.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
    
    # Drop rows with missing data
    df_15min = df_15min.dropna()
    
    logger.info(f"Aggregated to {len(df_15min)} 15-minute candles")
    
    return df_15min


def aggregate_to_15min(df_1min):
    """Aggregate 1-minute data to 15-minute candles"""
    logger.info(f"Aggregating {len(df_1min)} 1-minute candles to 15-minute...")
    
    df = df_1min.copy()
    df = df.set_index('datetime').sort_index()
    
    # Resample to 15-minute
    df_15min = df.resample('15min').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last'
    }).reset_index()
    
    # Remove NaN rows
    df_15min = df_15min.dropna().reset_index(drop=True)
    
    logger.info(f"Aggregated to {len(df_15min)} 15-minute candles")
    return df_15min


def main():
    """Main function to download and process AUD/USD data"""
    logger.info("=" * 70)
    logger.info("PROCESSING AUD/USD DATA FROM HistData.com")
    logger.info("=" * 70)
    
    # Find and process ZIP file
    year = 2024
    zip_file = find_year_zip_file(year, SYMBOL)
    
    if not zip_file:
        logger.warning(f"ZIP file not found for {SYMBOL.upper()}")
        logger.info(f"Please download {SYMBOL.upper()} data from HistData.com:")
        logger.info("1. Visit: https://www.histdata.com/download-free-forex-historical-data/")
        logger.info(f"2. Select: Currency Pair = {SYMBOL.upper()}")
        logger.info("3. Timeframe = M1 (1-minute)")
        logger.info("4. Year = 2024")
        logger.info(f"5. Save ZIP to: {DATA_DIR}/ or data/ directory")
        logger.info(f"   Expected: DAT_ASCII_{SYMBOL.upper()}_M2024.zip")
        return
    
    logger.info(f"Found ZIP file: {zip_file}")
    
    # Load 1-minute data
    df_1min = load_histdata_zip(zip_file)
    
    if df_1min is None or len(df_1min) == 0:
        logger.error("No data loaded")
        return
    
    # Filter to June-December 2024
    start_date = pd.to_datetime('2024-06-01', utc=True)
    end_date = pd.to_datetime('2024-12-31 23:59:59', utc=True)
    df_1min = df_1min[(df_1min['datetime'] >= start_date) & (df_1min['datetime'] <= end_date)]
    
    logger.info(f"Filtered to {len(df_1min)} 1-minute candles (June-December 2024)")
    
    # Aggregate to 15-minute
    df_15min = aggregate_to_15min(df_1min)
    
    # Save to CSV
    output_file = 'data/audusd_15min_6months.csv'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df_15min.to_csv(output_file, index=False)
    
    logger.info(f"Data saved to {output_file}")
    logger.info(f"Total 15-minute candles: {len(df_15min)}")
    logger.info(f"Date range: {df_15min['datetime'].min()} to {df_15min['datetime'].max()}")
    
    print("\n" + "=" * 70)
    print("AUD/USD DATA PROCESSING COMPLETE")
    print("=" * 70)
    print(f"File: {output_file}")
    print(f"Candles: {len(df_15min)}")
    print(f"Date Range: {df_15min['datetime'].min()} to {df_15min['datetime'].max()}")
    print("=" * 70)


if __name__ == "__main__":
    main()

