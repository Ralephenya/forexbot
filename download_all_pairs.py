"""
Automatically download all pairs using histdata package
"""

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from histdata import download_hist_data as dl
    from histdata.api import Platform, TimeFrame
    HISTDATA_AVAILABLE = True
except ImportError:
    HISTDATA_AVAILABLE = False
    logger.warning("histdata package not available. Install with: pip install histdata")


def download_pair(symbol, year="2024"):
    """Download data for a currency pair"""
    if not HISTDATA_AVAILABLE:
        logger.error("histdata package not installed. Cannot download automatically.")
        return False
    
    try:
        logger.info(f"Downloading {symbol.upper()} for year {year}...")
        
        # Download entire year
        dl(
            year=year,
            month=None,
            pair=symbol,
            platform=Platform.GENERIC_ASCII,
            time_frame=TimeFrame.ONE_MINUTE
        )
        
        logger.info(f"Downloaded {symbol.upper()}")
        return True
        
    except Exception as e:
        logger.error(f"Error downloading {symbol.upper()}: {str(e)}")
        return False


def main():
    """Download all pairs"""
    logger.info("=" * 70)
    logger.info("AUTOMATIC DATA DOWNLOADER")
    logger.info("=" * 70)
    
    if not HISTDATA_AVAILABLE:
        logger.error("histdata package is not installed.")
        logger.info("Install with: pip install histdata")
        logger.info("\nAlternatively, manually download ZIP files from:")
        logger.info("https://www.histdata.com/download-free-forex-historical-data/")
        return
    
    pairs = ['gbpusd', 'usdjpy']
    
    for pair in pairs:
        logger.info(f"\nProcessing {pair.upper()}...")
        success = download_pair(pair, year="2024")
        if success:
            logger.info(f"✅ {pair.upper()} downloaded successfully")
            logger.info(f"   Look for: DAT_ASCII_{pair.upper()}_M2024.zip")
            logger.info(f"   Then run: python histdata_downloader_multipair.py")
        else:
            logger.warning(f"❌ {pair.upper()} download failed")
    
    logger.info("\n" + "=" * 70)
    logger.info("DOWNLOAD COMPLETE")
    logger.info("=" * 70)
    logger.info("Next steps:")
    logger.info("1. Check for ZIP files in current directory or data/histdata/")
    logger.info("2. Run: python histdata_downloader_multipair.py")
    logger.info("3. Run: python apply_strategy_b_all_pairs.py")
    logger.info("4. Run: python portfolio_backtester.py")


if __name__ == "__main__":
    main()























