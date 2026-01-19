"""
Quick AUD/USD test using yfinance (60-day limit)
This is a temporary test to validate scripts work
For full 7-month test, use HistData.com data
"""

import pandas as pd
import yfinance as yf
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_audusd_yfinance():
    """Download AUD/USD data using yfinance (60-day limit)"""
    logger.info("Downloading AUD/USD data from yfinance (60-day limit)...")
    
    try:
        # AUD/USD ticker
        ticker = yf.Ticker("AUDUSD=X")
        
        # Download 1-minute data (max 60 days)
        df = ticker.history(interval="15m", period="60d")
        
        if df.empty:
            logger.error("No data downloaded")
            return None
        
        # Reset index and rename columns
        df = df.reset_index()
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        
        # Rename to match our format
        df = df.rename(columns={
            'datetime': 'datetime',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume'
        })
        
        # Ensure datetime is timezone-aware
        if df['datetime'].dtype == 'object':
            df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
        else:
            df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
        
        logger.info(f"Downloaded {len(df)} 15-minute candles")
        logger.info(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")
        
        # Save
        output_file = 'data/audusd_15min_yfinance.csv'
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        df.to_csv(output_file, index=False)
        logger.info(f"Saved to {output_file}")
        
        logger.warning("NOTE: This is only 60 days of data (yfinance limit)")
        logger.warning("For full 7-month test, download from HistData.com")
        
        return output_file
        
    except Exception as e:
        logger.error(f"Error downloading data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None


if __name__ == "__main__":
    download_audusd_yfinance()





















