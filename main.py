"""
Main script to run the complete backtesting pipeline
"""

import logging
import sys
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run the complete backtesting pipeline"""
    try:
        logger.info("=" * 70)
        logger.info("FOREX BACKTESTING SYSTEM - 6-MONTH RSI STRATEGY TEST")
        logger.info("=" * 70)
        logger.info("")
        
        # Step 1: Calculate indicators
        logger.info("STEP 1: Calculating Indicators")
        logger.info("=" * 70)
        from indicator_calculator import main as calc_indicators
        calc_indicators()
        logger.info("")
        
        # Step 2: Detect signals
        logger.info("STEP 2: Detecting Trading Signals")
        logger.info("=" * 70)
        from signal_detector import main as detect_signals
        detect_signals()
        logger.info("")
        
        # Step 3: Run backtest
        logger.info("STEP 3: Running Backtest")
        logger.info("=" * 70)
        from backtester import main as run_backtest
        run_backtest()
        logger.info("")
        
        # Step 4: Generate report
        logger.info("STEP 4: Generating Performance Report")
        logger.info("=" * 70)
        from report_generator import main as generate_report
        generate_report()
        logger.info("")
        
        logger.info("=" * 70)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)
        logger.info(f"Results saved to: results/backtest_results_6months.csv")
        logger.info(f"Report saved to: results/performance_report_6months.html")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()























