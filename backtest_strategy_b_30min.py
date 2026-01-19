"""
Backtest Strategy B on 30-minute timeframe
"""

import pandas as pd
import logging
import os
from backtester import Trade

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Trading parameters (same as 15-minute)
SPREAD_COST_PIPS = 1.0
LOT_SIZE = 0.01
PIP_VALUE = 0.10
TRADING_END_HOUR = 17  # 5 PM UTC
PIP_MULTIPLIER = 10000  # EUR/USD: 1 pip = 0.0001


def adaptive_backtest_30min(df, use_adaptive_targets=True):
    """
    Run backtest with adaptive targets/stops on 30-minute data
    
    Args:
        df: pandas.DataFrame with signals and price data
        use_adaptive_targets: If True, use adaptive_target_pips/adaptive_stop_pips columns
    
    Returns:
        List of Trade objects
    """
    try:
        logger.info(f"Starting adaptive backtest on {len(df)} 30-minute candles...")
        
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
                # Get adaptive targets if available
                if use_adaptive_targets and 'adaptive_target_pips' in row and 'adaptive_stop_pips' in row:
                    target_pips = row['adaptive_target_pips']
                    stop_pips = row['adaptive_stop_pips']
                else:
                    # Default targets
                    target_pips = 12
                    stop_pips = 8
                
                # Check for end of trading day
                current_hour = dt.hour
                if current_hour >= TRADING_END_HOUR:
                    current_trade.close(dt, close_price, 'end_of_day')
                    trades.append(current_trade)
                    current_trade = None
                    continue
                
                # Check for exit conditions
                if current_trade.direction == 'BUY':
                    target_price = current_trade.entry_price + (target_pips / PIP_MULTIPLIER)
                    stop_price = current_trade.entry_price - (stop_pips / PIP_MULTIPLIER)
                    
                    if high_price >= target_price:
                        current_trade.close(dt, target_price, 'target')
                        trades.append(current_trade)
                        current_trade = None
                        continue
                    elif low_price <= stop_price:
                        current_trade.close(dt, stop_price, 'stop_loss')
                        trades.append(current_trade)
                        current_trade = None
                        continue
                
                else:  # SELL
                    target_price = current_trade.entry_price - (target_pips / PIP_MULTIPLIER)
                    stop_price = current_trade.entry_price + (stop_pips / PIP_MULTIPLIER)
                    
                    if low_price <= target_price:
                        current_trade.close(dt, target_price, 'target')
                        trades.append(current_trade)
                        current_trade = None
                        continue
                    elif high_price >= stop_price:
                        current_trade.close(dt, stop_price, 'stop_loss')
                        trades.append(current_trade)
                        current_trade = None
                        continue
            
            # Check for new entry signals
            if current_trade is None:
                entry_price = close_price
                
                if row['buy_signal']:
                    entry_price = entry_price + (SPREAD_COST_PIPS / PIP_MULTIPLIER / 2)
                    current_trade = Trade(dt, entry_price, 'BUY')
                
                elif row['sell_signal']:
                    entry_price = entry_price - (SPREAD_COST_PIPS / PIP_MULTIPLIER / 2)
                    current_trade = Trade(dt, entry_price, 'SELL')
        
        # Close any remaining trade
        if current_trade is not None:
            last_row = df.iloc[-1]
            current_trade.close(last_row['datetime'], last_row['close'], 'end_of_data')
            trades.append(current_trade)
        
        logger.info(f"Adaptive backtest completed. Generated {len(trades)} trades")
        
        return trades
        
    except Exception as e:
        logger.error(f"Error in adaptive backtest: {str(e)}")
        raise


def main():
    """Main function"""
    logger.info("=" * 70)
    logger.info("BACKTESTING STRATEGY B ON 30-MINUTE TIMEFRAME")
    logger.info("=" * 70)
    
    # Load signals
    signals_file = "data/eurusd_30min_6months_strategy_b_signals.csv"
    logger.info(f"Loading signals from {signals_file}...")
    
    if not os.path.exists(signals_file):
        raise FileNotFoundError(f"Signals file not found: {signals_file}")
    
    df = pd.read_csv(signals_file)
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    logger.info(f"Loaded {len(df)} 30-minute candles with signals")
    
    # Run backtest
    trades = adaptive_backtest_30min(df, use_adaptive_targets=True)
    
    if len(trades) == 0:
        logger.warning("No trades generated!")
        return
    
    # Convert to DataFrame
    trades_df = pd.DataFrame([t.to_dict() for t in trades])
    trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'], utc=True)
    trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'], utc=True)
    
    # Calculate metrics
    winning_trades = trades_df[trades_df['pnl'] > 0]
    win_rate = (len(winning_trades) / len(trades_df) * 100) if len(trades_df) > 0 else 0
    total_pnl = trades_df['pnl'].sum()
    avg_pips = trades_df['pips'].mean()
    
    # Calculate drawdown
    daily_pnl = trades_df.groupby(trades_df['exit_time'].dt.date)['pnl'].sum()
    cumulative = daily_pnl.cumsum()
    running_max = cumulative.cummax()
    drawdown = cumulative - running_max
    max_drawdown = drawdown.min()
    
    # Save results
    results_file = "results/backtest_results_strategy_b_30min.csv"
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    trades_df.to_csv(results_file, index=False)
    
    # Print results
    print("\n" + "=" * 70)
    print("STRATEGY B (30-MINUTE) BACKTEST RESULTS")
    print("=" * 70)
    print(f"Total Trades: {len(trades_df)}")
    print(f"Winning Trades: {len(winning_trades)}")
    print(f"Losing Trades: {len(trades_df) - len(winning_trades)}")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Total P&L: ${total_pnl:.2f}")
    print(f"Average Pips per Trade: {avg_pips:.2f}")
    print(f"Max Drawdown: ${max_drawdown:.2f}")
    print(f"Results saved to: {results_file}")
    print("=" * 70)
    
    return trades_df


if __name__ == "__main__":
    main()























