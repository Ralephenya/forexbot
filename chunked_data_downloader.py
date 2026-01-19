"""
Chunked Data Downloader for EUR/USD 15-minute data
Attempts to download 6 months of data in 60-day chunks and combines them
Note: yfinance only provides the last 60 days of intraday data, so older chunks will fail
"""

import yfinance as yf
import pandas as pd
import logging
from datetime import datetime, timedelta
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SYMBOL = "EURUSD=X"
TIMEFRAME = "15m"
DATA_DIR = "data"
OUTPUT_FILE = "data/eurusd_15min_6months.csv"

# Define chunk periods (60 days each)
# NOTE: yfinance only provides the last 60 days of intraday data
# We'll try to download what's available (most recent 60 days)
# and split it into logical chunks for analysis

def get_available_chunks():
    """
    Generate chunks based on what's actually available (last 60 days)
    Since yfinance limits intraday data to 60 days, we can only get recent data
    """
    today = datetime.now()
    start_date = today - timedelta(days=60)
    
    # Try to download the full 60-day period
    # Then we can split it into logical chunks for analysis
    return [
        {
            "name": "Most Recent 60 Days",
            "start": start_date,
            "end": today
        }
    ]

CHUNKS = get_available_chunks()


def download_chunk(symbol, interval, start_date, end_date, chunk_name):
    """
    Download a chunk of historical data
    
    Args:
        symbol: Trading pair symbol (e.g., 'EURUSD=X')
        interval: Data interval (e.g., '15m')
        start_date: Start datetime
        end_date: End datetime
        chunk_name: Name for logging
    
    Returns:
        pandas.DataFrame with downloaded data, or None if failed
    """
    try:
        logger.info(f"Downloading {chunk_name}: {start_date.date()} to {end_date.date()}")
        
        ticker = yf.Ticker(symbol)
        data = ticker.history(start=start_date, end=end_date, interval=interval)
        
        if data.empty:
            logger.warning(f"{chunk_name}: No data returned (likely beyond 60-day limit)")
            return None
        
        # Clean and prepare data
        data = data.reset_index()
        data.columns = [col.lower() for col in data.columns]
        
        # Select only OHLC columns (drop volume if present, or handle if not)
        required_cols = ['datetime', 'open', 'high', 'low', 'close']
        if 'datetime' not in data.columns and 'date' in data.columns:
            data = data.rename(columns={'date': 'datetime'})
        
        data = data[required_cols]
        
        # Ensure datetime is timezone-aware
        if data['datetime'].dt.tz is None:
            data['datetime'] = pd.to_datetime(data['datetime'], utc=True)
        
        logger.info(f"{chunk_name}: Successfully downloaded {len(data)} rows")
        logger.info(f"{chunk_name}: Date range: {data['datetime'].min()} to {data['datetime'].max()}")
        
        return data
        
    except Exception as e:
        logger.error(f"{chunk_name}: Error downloading data: {str(e)}")
        return None


def combine_chunks(chunks_data):
    """
    Combine multiple data chunks, removing duplicates and sorting
    
    Args:
        chunks_data: List of pandas.DataFrames
    
    Returns:
        Combined pandas.DataFrame
    """
    if not chunks_data:
        logger.warning("No chunks to combine")
        return pd.DataFrame()
    
    # Filter out None values
    valid_chunks = [chunk for chunk in chunks_data if chunk is not None and not chunk.empty]
    
    if not valid_chunks:
        logger.warning("No valid chunks to combine")
        return pd.DataFrame()
    
    logger.info(f"Combining {len(valid_chunks)} chunks...")
    
    # Combine all chunks
    combined = pd.concat(valid_chunks, ignore_index=True)
    
    # Remove duplicates based on datetime
    initial_count = len(combined)
    combined = combined.drop_duplicates(subset=['datetime'], keep='first')
    duplicates_removed = initial_count - len(combined)
    
    if duplicates_removed > 0:
        logger.info(f"Removed {duplicates_removed} duplicate rows")
    
    # Sort by datetime
    combined = combined.sort_values('datetime').reset_index(drop=True)
    
    logger.info(f"Combined dataset: {len(combined)} rows")
    logger.info(f"Date range: {combined['datetime'].min()} to {combined['datetime'].max()}")
    
    return combined


def save_data(df, output_path):
    """
    Save DataFrame to CSV
    
    Args:
        df: pandas.DataFrame
        output_path: Path to save CSV file
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Data saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Error saving data: {str(e)}")
        raise


def main():
    """
    Main function to download data in chunks and combine
    """
    logger.info("=" * 70)
    logger.info("CHUNKED DATA DOWNLOADER - EUR/USD 15-minute")
    logger.info("=" * 70)
    logger.info(f"Symbol: {SYMBOL}")
    logger.info(f"Timeframe: {TIMEFRAME}")
    logger.info(f"Attempting to download {len(CHUNKS)} chunks...")
    logger.info("")
    
    # Download each chunk
    chunks_data = []
    successful_chunks = []
    failed_chunks = []
    
    for chunk in CHUNKS:
        data = download_chunk(
            symbol=SYMBOL,
            interval=TIMEFRAME,
            start_date=chunk["start"],
            end_date=chunk["end"],
            chunk_name=chunk["name"]
        )
        
        if data is not None and not data.empty:
            chunks_data.append(data)
            successful_chunks.append(chunk["name"])
        else:
            failed_chunks.append(chunk["name"])
        
        logger.info("")  # Blank line between chunks
    
    # Report results
    logger.info("=" * 70)
    logger.info("DOWNLOAD SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Successful chunks: {len(successful_chunks)}/{len(CHUNKS)}")
    if successful_chunks:
        logger.info(f"  - {', '.join(successful_chunks)}")
    if failed_chunks:
        logger.info(f"Failed chunks: {len(failed_chunks)}/{len(CHUNKS)}")
        logger.info(f"  - {', '.join(failed_chunks)}")
        logger.info("Note: yfinance only provides the last 60 days of intraday data")
    logger.info("")
    
    # Combine chunks
    if chunks_data:
        combined_data = combine_chunks(chunks_data)
        
        if not combined_data.empty:
            # Save combined data
            save_data(combined_data, OUTPUT_FILE)
            
            # Print summary statistics
            logger.info("")
            logger.info("=" * 70)
            logger.info("FINAL DATASET SUMMARY")
            logger.info("=" * 70)
            logger.info(f"Total rows: {len(combined_data):,}")
            logger.info(f"Date range: {combined_data['datetime'].min()} to {combined_data['datetime'].max()}")
            
            # Calculate number of days
            date_range = combined_data['datetime'].max() - combined_data['datetime'].min()
            logger.info(f"Time span: {date_range.days} days")
            
            # Calculate number of candles per day (should be ~96 for 15-minute data)
            total_days = date_range.total_seconds() / (24 * 3600)
            candles_per_day = len(combined_data) / total_days if total_days > 0 else 0
            logger.info(f"Average candles per day: {candles_per_day:.1f}")
            logger.info("")
            logger.info(f"Data saved to: {OUTPUT_FILE}")
        else:
            logger.error("Failed to combine chunks - resulting dataset is empty")
    else:
        logger.error("No data was successfully downloaded from any chunk")
    
    logger.info("=" * 70)


if __name__ == "__main__":
    main()

