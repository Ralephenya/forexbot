"""
Backtester Module
Simulates trades based on detected signals
"""

import pandas as pd
import logging
import config
from datetime import timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Trade:
    """Represents a single trade"""
    def __init__(self, entry_time, entry_price, direction):
        self.entry_time = entry_time
        self.entry_price = entry_price
        self.direction = direction  # 'BUY' or 'SELL'
        self.exit_time = None
        self.exit_price = None
        self.exit_reason = None
        self.pips = None
        self.pnl = None
    
    def close(self, exit_time, exit_price, exit_reason):
        """Close the trade"""
        self.exit_time = exit_time
        self.exit_price = exit_price
        self.exit_reason = exit_reason
        
        # Calculate pips
        if self.direction == 'BUY':
            self.pips = (exit_price - self.entry_price) * 10000  # Convert to pips
        else:  # SELL
            self.pips = (self.entry_price - exit_price) * 10000
        
        # Calculate P&L in dollars
        self.pnl = self.pips * config.PIP_VALUE
    
    def to_dict(self):
        """Convert trade to dictionary"""
        return {
            'entry_time': self.entry_time,
            'entry_price': self.entry_price,
            'exit_time': self.exit_time,
            'exit_price': self.exit_price,
            'direction': self.direction,
            'pips': self.pips,
            'pnl': self.pnl,
            'exit_reason': self.exit_reason
        }


def backtest(df):
    """
    Run backtest on dataframe with signals
    
    Args:
        df: pandas.DataFrame with signals and price data
    
    Returns:
        List of Trade objects
    """
    try:
        logger.info(f"Starting backtest on {len(df)} data points...")
        
        # Ensure datetime is timezone-aware
        df = df.copy()
        df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
        df = df.sort_values('datetime').reset_index(drop=True)
        
        trades = []
        current_trade = None
        
        for i in range(len(df)):
            row = df.iloc[i]
            dt = row['datetime']
            close_price = row['close']
            high_price = row['high']
            low_price = row['low']
            
            # Check if we have an open position
            if current_trade is not None:
                # Check for end of trading day (close positions at 17:00 UTC = end of London session)
                current_hour = dt.hour
                if current_hour >= config.TRADING_END_HOUR:
                    # Close position at current close price
                    current_trade.close(dt, close_price, 'end_of_day')
                    trades.append(current_trade)
                    current_trade = None
                    continue
                
                # Get VWAP for VWAP return exit
                vwap = row.get('vwap', None)
                
                # Check for exit conditions (target, stop, or VWAP return - whichever happens first)
                if current_trade.direction == 'BUY':
                    # Check target (high price)
                    target_price = current_trade.entry_price + (config.TARGET_PIPS / 10000)
                    target_hit = high_price >= target_price
                    
                    # Check stop loss (low price)
                    stop_price = current_trade.entry_price - (config.STOP_LOSS_PIPS / 10000)
                    stop_hit = low_price <= stop_price
                    
                    # Check VWAP return (price returns to VWAP - low price crosses VWAP from below)
                    vwap_return = False
                    vwap_exit_price = None
                    if vwap is not None and not pd.isna(vwap):
                        # Check if low price touched or crossed VWAP (mean reversion complete)
                        if low_price <= vwap <= high_price:
                            vwap_return = True
                            vwap_exit_price = vwap
                    
                    # Exit on first condition met
                    if target_hit:
                        current_trade.close(dt, target_price, 'target')
                        trades.append(current_trade)
                        current_trade = None
                        continue
                    elif stop_hit:
                        current_trade.close(dt, stop_price, 'stop_loss')
                        trades.append(current_trade)
                        current_trade = None
                        continue
                    elif vwap_return:
                        current_trade.close(dt, vwap_exit_price, 'vwap_return')
                        trades.append(current_trade)
                        current_trade = None
                        continue
                
                else:  # SELL
                    # Check target (low price)
                    target_price = current_trade.entry_price - (config.TARGET_PIPS / 10000)
                    target_hit = low_price <= target_price
                    
                    # Check stop loss (high price)
                    stop_price = current_trade.entry_price + (config.STOP_LOSS_PIPS / 10000)
                    stop_hit = high_price >= stop_price
                    
                    # Check VWAP return (price returns to VWAP - high price crosses VWAP from above)
                    vwap_return = False
                    vwap_exit_price = None
                    if vwap is not None and not pd.isna(vwap):
                        # Check if high price touched or crossed VWAP (mean reversion complete)
                        if low_price <= vwap <= high_price:
                            vwap_return = True
                            vwap_exit_price = vwap
                    
                    # Exit on first condition met
                    if target_hit:
                        current_trade.close(dt, target_price, 'target')
                        trades.append(current_trade)
                        current_trade = None
                        continue
                    elif stop_hit:
                        current_trade.close(dt, stop_price, 'stop_loss')
                        trades.append(current_trade)
                        current_trade = None
                        continue
                    elif vwap_return:
                        current_trade.close(dt, vwap_exit_price, 'vwap_return')
                        trades.append(current_trade)
                        current_trade = None
                        continue
            
            # Check for new entry signals (only if no open position)
            if current_trade is None:
                # Entry logic: enter at next candle open (current close)
                entry_price = close_price
                
                if row['buy_signal']:
                    # Apply spread cost to entry (for BUY, add half spread)
                    entry_price = entry_price + (config.SPREAD_COST_PIPS / 10000 / 2)
                    current_trade = Trade(dt, entry_price, 'BUY')
                
                elif row['sell_signal']:
                    # Apply spread cost to entry (for SELL, subtract half spread)
                    entry_price = entry_price - (config.SPREAD_COST_PIPS / 10000 / 2)
                    current_trade = Trade(dt, entry_price, 'SELL')
        
        # Close any remaining open trade at end of data
        if current_trade is not None:
            last_row = df.iloc[-1]
            current_trade.close(last_row['datetime'], last_row['close'], 'end_of_data')
            trades.append(current_trade)
        
        logger.info(f"Backtest completed. Generated {len(trades)} trades")
        
        return trades
        
    except Exception as e:
        logger.error(f"Error in backtest: {str(e)}")
        raise


def main():
    """Main function to run backtest"""
    import os
    
    try:
        logger.info("=" * 70)
        logger.info("BACKTESTER")
        logger.info("=" * 70)
        
        # Load data with signals
        if not os.path.exists(config.SIGNALS_FILE):
            raise FileNotFoundError(f"Signals file not found: {config.SIGNALS_FILE}")
        
        logger.info(f"Loading data from {config.SIGNALS_FILE}...")
        df = pd.read_csv(config.SIGNALS_FILE)
        df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
        
        logger.info(f"Loaded {len(df)} rows from {config.SIGNALS_FILE}")
        
        # Run backtest
        trades = backtest(df)
        
        # Convert trades to DataFrame
        trades_df = pd.DataFrame([t.to_dict() for t in trades])
        
        # Calculate summary statistics
        if len(trades) > 0:
            winning_trades = trades_df[trades_df['pnl'] > 0]
            losing_trades = trades_df[trades_df['pnl'] <= 0]
            
            total_trades = len(trades)
            winning_count = len(winning_trades)
            win_rate = (winning_count / total_trades * 100) if total_trades > 0 else 0
            total_pnl = trades_df['pnl'].sum()
            
            logger.info(f"Total Trades: {total_trades}")
            logger.info(f"Winning Trades: {winning_count}")
            logger.info(f"Win Rate: {win_rate:.2f}%")
            logger.info(f"Total P&L: ${total_pnl:.2f}")
            logger.info("=" * 50)
        
        # Save results
        os.makedirs(os.path.dirname(config.BACKTEST_RESULTS_FILE), exist_ok=True)
        trades_df.to_csv(config.BACKTEST_RESULTS_FILE, index=False)
        logger.info(f"Backtest results saved to {config.BACKTEST_RESULTS_FILE}")
        
        logger.info("Backtest completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise


if __name__ == "__main__":
    main()

