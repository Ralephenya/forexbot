"""
HistData.com Data Downloader for GBP/JPY
Downloads 1-minute data and converts to 15-minute candles
Based on EUR/USD downloader but adapted for GBP/JPY
"""

import pandas as pd
import logging
from datetime import datetime
import os
import time
from pathlib import Path
import zipfile
import glob

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SYMBOL = "gbpjpy"
DATA_DIR = "data/histdata"
OUTPUT_FILE = "data/gbpjpy_15min_6months.csv"

# Define date ranges (months to process)
MONTHS_TO_PROCESS = [
    {"year": "2024", "month": "6", "name": "June 2024"},
    {"year": "2024", "month": "7", "name": "July 2024"},
    {"year": "2024", "month": "8", "name": "August 2024"},
    {"year": "2024", "month": "9", "name": "September 2024"},
    {"year": "2024", "month": "10", "name": "October 2024"},
    {"year": "2024", "month": "11", "name": "November 2024"},
    {"year": "2024", "month": "12", "name": "December 2024"},
]


def find_year_zip_file(year):
    """Find ZIP file for a given year"""
    # Check data directory
    data_dir_abs = os.path.abspath(DATA_DIR)
    pattern = os.path.join(data_dir_abs, f"DAT_ASCII_{SYMBOL.upper()}_M{year}*.zip")
    files = glob.glob(pattern)
    
    # Check current directory
    current_pattern = os.path.join(os.getcwd(), f"DAT_ASCII_{SYMBOL.upper()}_M{year}*.zip")
    files.extend(glob.glob(current_pattern))
    
    # Check data/ directory
    data_pattern = os.path.join(os.getcwd(), "data", f"DAT_ASCII_{SYMBOL.upper()}_M{year}*.zip")
    files.extend(glob.glob(data_pattern))
    
    if files:
        return files[0]  # Return first match
    return None


def load_histdata_zip(zip_path):
    """
    Load and parse HistData.com ZIP file
    Format: YYYYMMDD HHMMSS;BidOpen;BidHigh;BidLow;BidClose;0
    """
    logger.info(f"Loading ZIP file: {zip_path}")
    
    data = []
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            # Find CSV file inside ZIP
            csv_files = [f for f in z.namelist() if f.endswith('.csv') or not f.endswith('/')]
            
            if not csv_files:
                raise ValueError(f"No CSV files found in ZIP: {zip_path}")
            
            csv_file = csv_files[0]
            logger.info(f"Reading CSV file: {csv_file}")
            
            with z.open(csv_file) as f:
                for line in f:
                    try:
                        line_str = line.decode('utf-8', errors='ignore').strip()
                        if not line_str or line_str.startswith('<'):
                            continue
                        
                        # Parse: YYYYMMDD HHMMSS;BidOpen;BidHigh;BidLow;BidClose;0
                        parts = line_str.split(';')
                        if len(parts) >= 5:
                            date_str = parts[0].strip()
                            bid_open = float(parts[1])
                            bid_high = float(parts[2])
                            bid_low = float(parts[3])
                            bid_close = float(parts[4])
                            
                            # Parse datetime: YYYYMMDD HHMMSS
                            dt = pd.to_datetime(date_str, format='%Y%m%d %H%M%S', utc=True)
                            
                            data.append({
                                'datetime': dt,
                                'open': bid_open,
                                'high': bid_high,
                                'low': bid_low,
                                'close': bid_close
                            })
                    except Exception as e:
                        continue  # Skip malformed lines
        
        logger.info(f"Loaded {len(data)} 1-minute candles from {zip_path}")
        return pd.DataFrame(data)
        
    except Exception as e:
        logger.error(f"Error loading ZIP file {zip_path}: {str(e)}")
        raise


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
    
    # Remove NaN rows (incomplete periods)
    df_15min = df_15min.dropna().reset_index(drop=True)
    
    logger.info(f"Aggregated to {len(df_15min)} 15-minute candles")
    return df_15min


def main():
    """Main function - process downloaded ZIP files"""
    logger.info("=" * 70)
    logger.info("GBP/JPY HISTDATA.COM DATA PROCESSOR")
    logger.info("=" * 70)
    
    # Create data directory
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # Find ZIP file for 2024
    zip_file = find_year_zip_file("2024")
    
    if not zip_file:
        logger.error("=" * 70)
        logger.error("ZIP FILE NOT FOUND!")
        logger.error("=" * 70)
        logger.error("Please download GBP/JPY data from HistData.com:")
        logger.error("1. Visit: https://www.histdata.com/download-free-forex-historical-data/")
        logger.error(f"2. Select: Currency Pair = {SYMBOL.upper()}")
        logger.error("3. Timeframe = M1 (1-minute)")
        logger.error("4. Year = 2024")
        logger.error("5. Download ZIP file")
        logger.error(f"6. Save to: {DATA_DIR}/ or data/ directory")
        logger.error(f"   Expected filename: DAT_ASCII_{SYMBOL.upper()}_M2024.zip")
        logger.error("=" * 70)
        return
    
    logger.info(f"Found ZIP file: {zip_file}")
    
    # Load and process data
    try:
        df_1min = load_histdata_zip(zip_file)
        
        # Filter by months
        df_1min['year'] = df_1min['datetime'].dt.year
        df_1min['month'] = df_1min['datetime'].dt.month
        
        # Filter to our target months (June-December 2024)
        target_months = [6, 7, 8, 9, 10, 11, 12]
        df_filtered = df_1min[
            (df_1min['year'] == 2024) & 
            (df_1min['month'].isin(target_months))
        ].copy()
        
        logger.info(f"Filtered to {len(df_filtered)} 1-minute candles (June-December 2024)")
        
        # Aggregate to 15-minute
        df_15min = aggregate_to_15min(df_filtered)
        
        # Save
        df_15min.to_csv(OUTPUT_FILE, index=False)
        logger.info(f"Saved {len(df_15min)} 15-minute candles to {OUTPUT_FILE}")
        
        # Summary
        print("\n" + "=" * 70)
        print("GBP/JPY DATA PROCESSING COMPLETE")
        print("=" * 70)
        print(f"Total 15-minute candles: {len(df_15min)}")
        print(f"Date range: {df_15min['datetime'].min()} to {df_15min['datetime'].max()}")
        print(f"Saved to: {OUTPUT_FILE}")
        print("=" * 70)
        
    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        import traceback
        logger.debug(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()























