"""
Download GBP/JPY 15-minute data using yfinance (quick method)
If yfinance fails, fall back to manual HistData.com instructions
"""

import pandas as pd
import yfinance as yf
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_gbpjpy_yfinance():
    """Attempt to download GBP/JPY data from yfinance"""
    logger.info("Attempting to download GBP/JPY from yfinance...")
    
    try:
        # GBP/JPY ticker on yfinance
        ticker = "GBPJPY=X"
        
        # Download maximum available intraday data (60 days)
        logger.info("Downloading GBP/JPY 15-minute data (max 60 days from yfinance)...")
        data = yf.download(ticker, interval="15m", period="60d", progress=False)
        
        if data.empty:
            raise ValueError("No data returned from yfinance")
        
        # Reset index to get datetime as column
        data = data.reset_index()
        
        # Rename columns
        data.columns = [col.lower().replace(' ', '_') for col in data.columns]
        
        # Ensure datetime column exists
        if 'datetime' not in data.columns and 'date' in data.columns:
            data['datetime'] = pd.to_datetime(data['date'])
        elif 'datetime' not in data.columns and data.index.name == 'Datetime':
            data['datetime'] = pd.to_datetime(data.index)
        
        # Select required columns
        required_cols = ['datetime', 'open', 'high', 'low', 'close']
        if all(col in data.columns for col in required_cols):
            df = data[required_cols].copy()
        else:
            # Try to find columns with similar names
            logger.warning(f"Expected columns not found. Available: {data.columns.tolist()}")
            raise ValueError("Required columns not found")
        
        # Ensure datetime is timezone-aware
        if df['datetime'].dtype == 'object':
            df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
        
        # Sort by datetime
        df = df.sort_values('datetime').reset_index(drop=True)
        
        logger.info(f"Downloaded {len(df)} GBP/JPY 15-minute candles")
        logger.info(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error downloading from yfinance: {str(e)}")
        raise


def main():
    """Main function"""
    logger.info("=" * 70)
    logger.info("GBP/JPY DATA DOWNLOAD")
    logger.info("=" * 70)
    
    try:
        # Try yfinance first
        df = download_gbpjpy_yfinance()
        
        # Save to CSV
        output_file = "data/gbpjpy_15min.csv"
        df.to_csv(output_file, index=False)
        logger.info(f"Saved GBP/JPY data to {output_file}")
        
        print("\n" + "=" * 70)
        print("GBP/JPY DATA DOWNLOAD SUMMARY")
        print("=" * 70)
        print(f"Total candles: {len(df)}")
        print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")
        print(f"Saved to: {output_file}")
        print("\nNOTE: yfinance only provides ~60 days of intraday data.")
        print("For 6-7 months, you may need to use HistData.com (similar to EUR/USD)")
        print("=" * 70)
        
        return df
        
    except Exception as e:
        logger.error(f"Failed to download GBP/JPY data: {str(e)}")
        logger.info("\n" + "=" * 70)
        logger.info("ALTERNATIVE: Use HistData.com (like we did for EUR/USD)")
        logger.info("=" * 70)
        logger.info("1. Visit: https://www.histdata.com/download-free-forex-historical-data/")
        logger.info("2. Select: Currency Pair = GBP/JPY")
        logger.info("3. Timeframe = M1 (1-minute)")
        logger.info("4. Download months: June 2024 - December 2024")
        logger.info("5. Save ZIP files to data/ directory")
        logger.info("6. Use histdata_downloader.py with GBP/JPY symbol")
        raise


if __name__ == "__main__":
    main()























