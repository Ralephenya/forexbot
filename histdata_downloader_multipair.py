"""
HistData.com Data Downloader for Multiple Pairs
Downloads 1-minute data and converts to 15-minute candles
Supports: GBP/USD and USD/JPY
"""

import pandas as pd
import logging
from datetime import datetime
import os
import zipfile
import glob

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DATA_DIR = "data/histdata"
MONTHS_TO_PROCESS = [6, 7, 8, 9, 10, 11, 12]  # June-December 2024


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
                            
                            # Parse datetime
                            dt = pd.to_datetime(date_str, format='%Y%m%d %H%M%S', utc=True)
                            
                            data.append({
                                'datetime': dt,
                                'open': bid_open,
                                'high': bid_high,
                                'low': bid_low,
                                'close': bid_close
                            })
                    except Exception as e:
                        continue
        
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
    
    # Remove NaN rows
    df_15min = df_15min.dropna().reset_index(drop=True)
    
    logger.info(f"Aggregated to {len(df_15min)} 15-minute candles")
    return df_15min


def process_pair(symbol):
    """Process a currency pair"""
    logger.info("=" * 70)
    logger.info(f"Processing {symbol.upper()}")
    logger.info("=" * 70)
    
    # Find ZIP file
    zip_file = find_year_zip_file("2024", symbol)
    
    if not zip_file:
        logger.warning(f"ZIP file not found for {symbol.upper()}")
        logger.info(f"Please download {symbol.upper()} data from HistData.com:")
        logger.info("1. Visit: https://www.histdata.com/download-free-forex-historical-data/")
        logger.info(f"2. Select: Currency Pair = {symbol.upper()}")
        logger.info("3. Timeframe = M1 (1-minute)")
        logger.info("4. Year = 2024")
        logger.info(f"5. Save ZIP to: {DATA_DIR}/ or data/ directory")
        logger.info(f"   Expected: DAT_ASCII_{symbol.upper()}_M2024.zip")
        return None
    
    logger.info(f"Found ZIP file: {zip_file}")
    
    # Load and process
    df_1min = load_histdata_zip(zip_file)
    
    # Filter by months (June-December 2024)
    df_1min['year'] = df_1min['datetime'].dt.year
    df_1min['month'] = df_1min['datetime'].dt.month
    
    df_filtered = df_1min[
        (df_1min['year'] == 2024) & 
        (df_1min['month'].isin(MONTHS_TO_PROCESS))
    ].copy()
    
    logger.info(f"Filtered to {len(df_filtered)} 1-minute candles (June-December 2024)")
    
    # Aggregate to 15-minute
    df_15min = aggregate_to_15min(df_filtered)
    
    # Save
    output_file = f"data/{symbol}_15min_6months.csv"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df_15min.to_csv(output_file, index=False)
    logger.info(f"Saved {len(df_15min)} 15-minute candles to {output_file}")
    
    return output_file


def main():
    """Process all pairs"""
    logger.info("=" * 70)
    logger.info("HISTDATA.COM MULTI-PAIR DATA PROCESSOR")
    logger.info("=" * 70)
    
    # Create data directory
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Process pairs
    pairs = ['gbpusd', 'usdjpy']
    results = {}
    
    for pair in pairs:
        output_file = process_pair(pair)
        if output_file:
            results[pair] = output_file
    
    # EUR/USD already exists
    eurusd_file = "data/eurusd_15min_6months.csv"
    if os.path.exists(eurusd_file):
        logger.info(f"EUR/USD data already exists: {eurusd_file}")
        results['eurusd'] = eurusd_file
    
    # Summary
    print("\n" + "=" * 70)
    print("DATA PROCESSING SUMMARY")
    print("=" * 70)
    for pair, file in results.items():
        if file and os.path.exists(file):
            df = pd.read_csv(file)
            print(f"{pair.upper()}: {len(df)} candles - {file}")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    main()

