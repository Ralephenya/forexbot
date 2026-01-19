"""
Main test runner for AUD/USD Extended Hours Test
Runs all phases of the analysis
"""

import os
import logging
import subprocess
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_data_file():
    """Check if AUD/USD data file exists"""
    data_file = 'data/audusd_15min_6months.csv'
    if os.path.exists(data_file):
        logger.info(f"✓ Full data file found: {data_file}")
        return True
    else:
        data_file = 'data/audusd_15min_yfinance.csv'
        if os.path.exists(data_file):
            logger.info(f"✓ yfinance data file found: {data_file} (60-day limit - quick test)")
            logger.warning("NOTE: This is a quick test with 60 days of data")
            logger.warning("For full 7-month test, download from HistData.com")
            return True
        else:
            logger.warning(f"✗ Data file not found")
            logger.info("Please run: python quick_audusd_test.py (for quick test)")
            logger.info("Or: python histdata_downloader_audusd.py (for full 7-month test)")
            return False


def run_script(script_name, description):
    """Run a Python script and check for errors"""
    logger.info(f"\n{'='*70}")
    logger.info(f"PHASE: {description}")
    logger.info(f"Running: {script_name}")
    logger.info(f"{'='*70}")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running {script_name}: {e}")
        logger.error(e.stderr)
        return False
    except FileNotFoundError:
        logger.error(f"Script not found: {script_name}")
        return False


def main():
    """Main test runner"""
    logger.info("=" * 70)
    logger.info("AUD/USD EXTENDED HOURS TEST - FULL ANALYSIS")
    logger.info("=" * 70)
    
    # Check if data exists
    if not check_data_file():
        logger.error("\nData file not found. Cannot proceed.")
        logger.info("\nPlease:")
        logger.info("1. Download AUD/USD data from HistData.com")
        logger.info("2. Save to: data/histdata/DAT_ASCII_AUDUSD_M2024.zip")
        logger.info("3. Run: python histdata_downloader_audusd.py")
        return False
    
    # Phase 1: Hour-by-hour analysis
    logger.info("\n" + "=" * 70)
    logger.info("PHASE 1: HOUR-BY-HOUR ANALYSIS")
    logger.info("=" * 70)
    if not run_script('audusd_hour_analysis.py', 'Hour-by-hour signal analysis'):
        logger.warning("Phase 1 failed, but continuing...")
    
    # Phase 2: Generate Strategy B signals for different sessions
    logger.info("\n" + "=" * 70)
    logger.info("PHASE 2: GENERATE STRATEGY B SIGNALS")
    logger.info("=" * 70)
    if not run_script('strategy_b_audusd.py', 'Generate signals for Sydney, London, and Combined sessions'):
        logger.error("Phase 2 failed. Cannot proceed to backtesting.")
        return False
    
    # Phase 3: Backtest all configurations
    logger.info("\n" + "=" * 70)
    logger.info("PHASE 3: BACKTEST ALL CONFIGURATIONS")
    logger.info("=" * 70)
    if not run_script('backtest_strategy_b_audusd.py', 'Backtest Sydney, London, and Combined sessions'):
        logger.error("Phase 3 failed.")
        return False
    
    # Phase 4: Compare with EUR/USD baseline
    logger.info("\n" + "=" * 70)
    logger.info("PHASE 4: COMPARE WITH EUR/USD BASELINE")
    logger.info("=" * 70)
    if not run_script('compare_audusd_eurusd.py', 'Compare AUD/USD results vs EUR/USD baseline'):
        logger.warning("Phase 4 failed, but analysis complete.")
    
    logger.info("\n" + "=" * 70)
    logger.info("ALL PHASES COMPLETE")
    logger.info("=" * 70)
    logger.info("\nCheck results in:")
    logger.info("  - results/audusd_hour_analysis.csv (Phase 1)")
    logger.info("  - results/backtest_results_audusd_*.csv (Phase 3)")
    logger.info("  - results/audusd_vs_eurusd_comparison.csv (Phase 4)")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

