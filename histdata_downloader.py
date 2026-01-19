"""
HistData.com Data Downloader for EUR/USD
Downloads 1-minute data using histdata package and converts to 15-minute candles
"""

import pandas as pd
import logging
from datetime import datetime
import os
import time
from pathlib import Path

try:
    from histdata import download_hist_data as dl
    from histdata.api import Platform, TimeFrame
    HISTDATA_AVAILABLE = True
except ImportError:
    HISTDATA_AVAILABLE = False
    logging.warning("histdata package not available. Install with: pip install histdata")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SYMBOL = "eurusd"
DATA_DIR = "data/histdata"
OUTPUT_FILE = "data/eurusd_15min_6months.csv"

# Define date ranges (months to download)
MONTHS_TO_DOWNLOAD = [
    {"year": "2024", "month": "6", "name": "June 2024"},
    {"year": "2024", "month": "7", "name": "July 2024"},
    {"year": "2024", "month": "8", "name": "August 2024"},
    {"year": "2024", "month": "9", "name": "September 2024"},
    {"year": "2024", "month": "10", "name": "October 2024"},
    {"year": "2024", "month": "11", "name": "November 2024"},
    {"year": "2024", "month": "12", "name": "December 2024"},
    {"year": "2025", "month": "1", "name": "January 2025"},
]


def create_data_directory():
    """Create data directory if it doesn't exist"""
    os.makedirs(DATA_DIR, exist_ok=True)
    logger.info(f"Data directory: {DATA_DIR}")


def download_year_histdata(year, symbol):
    """
    Download entire year of 1-minute data using histdata package
    For past years, download all months at once
    
    Args:
        year: Year as string (e.g., '2024')
        symbol: Currency pair (e.g., 'eurusd')
    
    Returns:
        List of file paths downloaded, or empty list if failed
    """
    try:
        logger.info(f"Downloading year {year} (all months)...")
        
        # For past years, download entire year
        dl(
            year=year,
            month=None,  # Download entire year for past years
            pair=symbol,
            platform=Platform.GENERIC_ASCII,
            time_frame=TimeFrame.ONE_MINUTE
        )
        
        # Find all downloaded files for this year
        # Format: DAT_ASCII_{SYMBOL}_M{YYYY}{MM}.zip
        pattern = f"DAT_ASCII_{symbol.upper()}_M{year}*.zip"
        import glob
        downloaded_files = glob.glob(pattern)
        
        # Also check data directory (using absolute path)
        data_dir_abs = os.path.abspath(DATA_DIR)
        data_pattern = os.path.join(data_dir_abs, pattern)
        downloaded_files.extend(glob.glob(data_pattern))
        
        # Also check current directory (where downloads might go)
        current_dir_pattern = os.path.join(os.getcwd(), pattern)
        downloaded_files.extend(glob.glob(current_dir_pattern))
        
        # Remove duplicates and sort
        downloaded_files = sorted(list(set([os.path.abspath(f) for f in downloaded_files])))
        
        logger.info(f"Found {len(downloaded_files)} downloaded files for year {year}")
        
        # Move files to data directory
        import shutil
        moved_files = []
        data_dir_abs = os.path.abspath(DATA_DIR)
        for file_path in downloaded_files:
            file_path_abs = os.path.abspath(file_path)
            if not file_path_abs.startswith(data_dir_abs):
                dest_path = os.path.join(data_dir_abs, os.path.basename(file_path))
                if os.path.exists(file_path_abs):
                    shutil.move(file_path_abs, dest_path)
                    moved_files.append(dest_path)
            else:
                moved_files.append(file_path_abs)
        
        return moved_files
        
    except Exception as e:
        logger.error(f"Error downloading year {year}: {str(e)}")
        import traceback
        logger.debug(traceback.format_exc())
        return []


def find_month_file(year, month, symbol, data_dir):
    """
    Find the ZIP file for a specific month
    
    Args:
        year: Year as string (e.g., '2024')
        month: Month as string (e.g., '6')
        symbol: Currency pair (e.g., 'eurusd')
        data_dir: Directory to search in
    
    Returns:
        Path to file, or None if not found
    """
    filename = f"DAT_ASCII_{symbol.upper()}_M{year}{month.zfill(2)}.zip"
    filepath = os.path.join(data_dir, filename)
    
    if os.path.exists(filepath):
        return filepath
    
        return None


def find_year_zip_file(year, symbol, data_dir):
    """
    Find the year ZIP file
    
    Args:
        year: Year as string (e.g., '2024')
        symbol: Currency pair (e.g., 'eurusd')
        data_dir: Directory to search in
    
    Returns:
        Path to file, or None if not found
    """
    # Try different filename patterns
    patterns = [
        f"DAT_ASCII_{symbol.upper()}_M1_{year}.zip",
        f"DAT_ASCII_{symbol.upper()}_M{year}.zip",
        f"{symbol.upper()}_M1_{year}.zip",
    ]
    
    # Check in data_dir first
    for pattern in patterns:
        filepath = os.path.join(data_dir, pattern)
        if os.path.exists(filepath):
            return filepath
    
    # Also check current directory (where downloads might go)
    import glob
    current_dir = os.getcwd()
    for pattern in patterns:
        files = glob.glob(os.path.join(current_dir, pattern))
        if files:
            # Move to data directory
            import shutil
            dest_path = os.path.join(data_dir, os.path.basename(files[0]))
            shutil.move(files[0], dest_path)
            return dest_path
    
    return None


def load_histdata_zip(zip_path):
    """
    Load and parse HistData.com ZIP file
    
    HistData.com format (DAT_ASCII format):
    - Each line: YYYYMMDD HHMMSS;BidOpen;BidHigh;BidLow;BidClose;AskOpen;AskHigh;AskLow;AskClose
    
    Args:
        zip_path: Path to ZIP file
    
    Returns:
        pandas.DataFrame with parsed data
    """
    import zipfile
    
    try:
        logger.info(f"Loading ZIP file: {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Get the CSV file inside (usually same name without .zip)
            file_list = zip_ref.namelist()
            csv_files = [f for f in file_list if f.endswith('.csv') or (not f.endswith('/') and not f.endswith('.zip'))]
            
            if not csv_files:
                logger.error(f"No CSV file found in ZIP: {zip_path}")
                return None
            
            csv_file = csv_files[0]
            
            # Read the CSV content
            with zip_ref.open(csv_file) as f:
                # HistData format: YYYYMMDD HHMMSS;BidOpen;BidHigh;BidLow;BidClose;AskOpen;AskHigh;AskLow;AskClose
                data = []
                for line_num, line in enumerate(f, 1):
                    try:
                        line = line.decode('utf-8', errors='ignore').strip()
                        if not line or line.startswith('#') or line.startswith(' '):
                            continue
                        
                        parts = line.split(';')
                        # HistData format: YYYYMMDD HHMMSS;BidOpen;BidHigh;BidLow;BidClose;0
                        # Sometimes has ask prices, sometimes only bid
                        if len(parts) >= 5:
                            date_str = parts[0].strip()
                            bid_open = float(parts[1])
                            bid_high = float(parts[2])
                            bid_low = float(parts[3])
                            bid_close = float(parts[4])
                            
                            # Check if ask prices are present (9 parts) or only bid (5-6 parts)
                            if len(parts) >= 9:
                                # Has ask prices
                                ask_open = float(parts[5])
                                ask_high = float(parts[6])
                                ask_low = float(parts[7])
                                ask_close = float(parts[8])
                                # Use mid-price
                                open_price = (bid_open + ask_open) / 2
                                high_price = (bid_high + ask_high) / 2
                                low_price = (bid_low + ask_low) / 2
                                close_price = (bid_close + ask_close) / 2
                            else:
                                # Only bid prices - use bid as mid (add small spread assumption)
                                # For backtesting, using bid prices directly is common
                                open_price = bid_open
                                high_price = bid_high
                                low_price = bid_low
                                close_price = bid_close
                            
                            # Parse datetime: YYYYMMDD HHMMSS
                            if len(date_str) >= 15:
                                dt_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]} {date_str[9:11]}:{date_str[11:13]}:{date_str[13:15]}"
                                dt = pd.to_datetime(dt_str, format='%Y-%m-%d %H:%M:%S', utc=True)
                            else:
                                continue
                            
                            data.append({
                                'datetime': dt,
                                'open': open_price,
                                'high': high_price,
                                'low': low_price,
                                'close': close_price
                            })
                    except Exception as e:
                        if line_num <= 5:  # Only log first few errors
                            logger.debug(f"Error parsing line {line_num}: {str(e)}")
                        continue
        
        if not data:
            logger.error(f"No data parsed from {zip_path}")
            return None
        
        df = pd.DataFrame(data)
        logger.info(f"Loaded {len(df)} rows from {zip_path}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error loading ZIP file {zip_path}: {str(e)}")
        import traceback
        logger.debug(traceback.format_exc())
        return None


def aggregate_to_15min(df):
    """
    Aggregate 1-minute data to 15-minute candles
    
    Args:
        df: pandas.DataFrame with 1-minute data (columns: datetime, open, high, low, close)
    
    Returns:
        pandas.DataFrame with 15-minute candles
    """
    try:
        if df.empty:
            return df
        
        # Set datetime as index
        df = df.set_index('datetime').sort_index()
        
        # Resample to 15-minute bars
        # OHLC aggregation: first open, max high, min low, last close
        df_15min = df.resample('15T').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last'
        }).dropna()
        
        # Reset index
        df_15min = df_15min.reset_index()
        
        logger.info(f"Aggregated {len(df)} 1-minute rows to {len(df_15min)} 15-minute candles")
        
        return df_15min
        
    except Exception as e:
        logger.error(f"Error aggregating to 15-minute: {str(e)}")
        import traceback
        logger.debug(traceback.format_exc())
        return pd.DataFrame()


def combine_months(all_dataframes):
    """
    Combine multiple monthly dataframes
    
    Args:
        all_dataframes: List of pandas.DataFrames
    
    Returns:
        Combined pandas.DataFrame
    """
    valid_dfs = [df for df in all_dataframes if df is not None and not df.empty]
    
    if not valid_dfs:
        return pd.DataFrame()
    
    combined = pd.concat(valid_dfs, ignore_index=True)
    combined = combined.sort_values('datetime').reset_index(drop=True)
    
    # Remove duplicates
    initial_len = len(combined)
    combined = combined.drop_duplicates(subset=['datetime'], keep='first')
    duplicates = initial_len - len(combined)
    
    if duplicates > 0:
        logger.info(f"Removed {duplicates} duplicate rows")
    
    return combined


def save_combined_data(df, output_path):
    """Save combined dataframe to CSV"""
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(df)} rows to {output_path}")
    except Exception as e:
        logger.error(f"Error saving data: {str(e)}")
        raise


def main():
    """Main function"""
    logger.info("=" * 70)
    logger.info("HISTDATA.COM DATA DOWNLOADER - EUR/USD")
    logger.info("=" * 70)
    logger.info(f"Symbol: {SYMBOL}")
    logger.info(f"Months to download: {len(MONTHS_TO_DOWNLOAD)}")
    
    if not HISTDATA_AVAILABLE:
        logger.error("histdata package is not available. Install with: pip install histdata")
        return
    
    logger.info("")
    
    create_data_directory()
    
    # Change to data directory for downloads
    original_dir = os.getcwd()
    os.chdir(DATA_DIR)
    
    try:
        # Group months by year (for past years, download entire year at once)
        years_to_download = {}
        for month_info in MONTHS_TO_DOWNLOAD:
            year = month_info["year"]
            if year not in years_to_download:
                years_to_download[year] = []
            years_to_download[year].append(month_info)
        
        # Download each year
        for year, months in years_to_download.items():
            logger.info(f"Downloading year {year} ({len(months)} months)...")
            downloaded_files = download_year_histdata(year, SYMBOL)
            
            if downloaded_files:
                logger.info(f"✓ Year {year}: Downloaded {len(downloaded_files)} files")
            else:
                logger.warning(f"✗ Year {year}: Download failed or no files found")
            logger.info("")
            time.sleep(2)  # Delay between years
        
        # Change back to original directory for processing
        os.chdir(original_dir)
        
        # Process each month from downloaded files
        all_data = []
        downloaded_months = []
        failed_months = []
        
        # Group months by year for processing
        years_to_process = {}
        for month_info in MONTHS_TO_DOWNLOAD:
            year = month_info["year"]
            if year not in years_to_process:
                years_to_process[year] = []
            years_to_process[year].append(month_info)
        
        # Process each year
        for year, months in years_to_process.items():
            # Find the year ZIP file
            year_zip = find_year_zip_file(year, SYMBOL, DATA_DIR)
            
            if year_zip and os.path.exists(year_zip):
                logger.info(f"Processing year {year} ZIP file: {os.path.basename(year_zip)}")
                
                # Load entire year data (year ZIP contains all months in one CSV)
                df_year = load_histdata_zip(year_zip)
                
                if df_year is not None and not df_year.empty:
                    # Filter and process each month
                    for month_info in months:
                        month = month_info["month"]
                        name = month_info["name"]
                        
                        logger.info(f"Processing {name}...")
                        
                        # Filter data for this month
                        month_int = int(month)
                        df_month = df_year[df_year['datetime'].dt.month == month_int].copy()
                        
                        if not df_month.empty:
                            # Aggregate to 15-minute
                            df_15min = aggregate_to_15min(df_month)
                            if not df_15min.empty:
                                all_data.append(df_15min)
                                downloaded_months.append(name)
                                logger.info(f"✓ {name}: {len(df_15min)} 15-minute candles (from {len(df_month)} 1-min rows)")
                            else:
                                failed_months.append(name)
                                logger.warning(f"✗ {name}: Failed to aggregate data")
                        else:
                            failed_months.append(name)
                            logger.warning(f"✗ {name}: No data for this month")
                        
                        logger.info("")
                else:
                    logger.warning(f"Failed to load year {year} data")
                    for month_info in months:
                        failed_months.append(month_info["name"])
                    logger.info("")
            else:
                logger.warning(f"Year {year} ZIP file not found")
                for month_info in months:
                    failed_months.append(month_info["name"])
                logger.info("")
        
        # Change back to original directory
        os.chdir(original_dir)
        
        # Report summary
        logger.info("=" * 70)
        logger.info("DOWNLOAD SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Successfully downloaded: {len(downloaded_months)}/{len(MONTHS_TO_DOWNLOAD)} months")
        if downloaded_months:
            logger.info(f"  - {', '.join(downloaded_months)}")
        if failed_months:
            logger.info(f"Failed months: {len(failed_months)}/{len(MONTHS_TO_DOWNLOAD)}")
            logger.info(f"  - {', '.join(failed_months)}")
        
        # Combine all data
        if all_data:
            logger.info("")
            logger.info("Combining all months...")
            combined = combine_months(all_data)
            
            if not combined.empty:
                save_combined_data(combined, os.path.join(original_dir, OUTPUT_FILE))
                
                logger.info("")
                logger.info("=" * 70)
                logger.info("FINAL DATASET SUMMARY")
                logger.info("=" * 70)
                logger.info(f"Total rows: {len(combined):,}")
                logger.info(f"Date range: {combined['datetime'].min()} to {combined['datetime'].max()}")
                date_range = combined['datetime'].max() - combined['datetime'].min()
                logger.info(f"Time span: {date_range.days} days")
                logger.info(f"Output file: {OUTPUT_FILE}")
            else:
                logger.error("Failed to combine data - resulting dataset is empty")
        else:
            logger.error("No data was successfully downloaded")
    
    except Exception as e:
        os.chdir(original_dir)
        logger.error(f"Error in main: {str(e)}")
        import traceback
        logger.debug(traceback.format_exc())
        raise
    
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
