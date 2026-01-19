"""
Backtest Strategy B on AUD/USD with different session configurations
"""

import pandas as pd
import logging
import os
from backtester import Trade

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AUD/USD trading parameters
SPREAD_COST_PIPS = 1.5
LOT_SIZE = 0.01
PIP_VALUE = 0.10
TRADING_END_HOUR = None  # No end hour restriction for extended sessions
PIP_MULTIPLIER = 10000  # AUD/USD: 1 pip = 0.0001


def adaptive_backtest_audusd(df, use_adaptive_targets=True):
    """
    Run backtest with adaptive targets/stops for AUD/USD
    """
    try:
        logger.info(f"Starting adaptive backtest on {len(df)} candles...")
        
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
                    target_pips = 15
                    stop_pips = 10
                
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
        import traceback
        logger.error(traceback.format_exc())
        raise


def backtest_configuration(config_name, signals_file):
    """Backtest a specific configuration"""
    logger.info(f"\n{'='*70}")
    logger.info(f"BACKTESTING: {config_name}")
    logger.info(f"{'='*70}")
    
    # Try yfinance version if main file doesn't exist
    if not os.path.exists(signals_file):
        alt_file = signals_file.replace('6months', 'yfinance')
        if os.path.exists(alt_file):
            signals_file = alt_file
            logger.info(f"Using yfinance signals file: {signals_file}")
        else:
            logger.warning(f"Signals file not found: {signals_file}")
            return None
    
    # Load signals
    df = pd.read_csv(signals_file)
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    logger.info(f"Loaded {len(df)} candles with signals")
    
    # Count signals
    buy_signals = df['buy_signal'].sum()
    sell_signals = df['sell_signal'].sum()
    logger.info(f"Signals: BUY={buy_signals}, SELL={sell_signals}, Total={buy_signals + sell_signals}")
    
    # Run backtest
    trades = adaptive_backtest_audusd(df, use_adaptive_targets=True)
    
    if len(trades) == 0:
        logger.warning("No trades generated!")
        return {
            'config': config_name,
            'trades': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'avg_pips': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0
        }
    
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
    
    # Calculate Sharpe ratio
    if len(trades_df) > 0 and trades_df['pnl'].std() > 0:
        sharpe_ratio = (trades_df['pnl'].mean() / trades_df['pnl'].std()) * (252**0.5)
    else:
        sharpe_ratio = 0
    
    # Save results
    config_safe = config_name.lower().replace(' ', '_')
    results_file = f"results/backtest_results_audusd_{config_safe}.csv"
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    trades_df.to_csv(results_file, index=False)
    
    # Print results
    print("\n" + "=" * 70)
    print(f"{config_name.upper()} - BACKTEST RESULTS")
    print("=" * 70)
    print(f"Total Trades: {len(trades_df)}")
    print(f"Winning Trades: {len(winning_trades)}")
    print(f"Losing Trades: {len(trades_df) - len(winning_trades)}")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Total P&L: ${total_pnl:.2f}")
    print(f"Average Pips per Trade: {avg_pips:.2f}")
    print(f"Max Drawdown: ${max_drawdown:.2f}")
    print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
    print(f"Results saved to: {results_file}")
    print("=" * 70)
    
    return {
        'config': config_name,
        'trades': len(trades_df),
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'avg_pips': avg_pips,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio,
        'results_file': results_file
    }


def main():
    """Main function"""
    logger.info("=" * 70)
    logger.info("BACKTESTING STRATEGY B ON AUD/USD - MULTIPLE CONFIGURATIONS")
    logger.info("=" * 70)
    
    configurations = [
        ('Sydney Session', 'data/audusd_15min_6months_strategy_b_sydney_session_signals.csv'),
        ('London Session', 'data/audusd_15min_6months_strategy_b_london_session_signals.csv'),
        ('Combined Sessions', 'data/audusd_15min_6months_strategy_b_combined_sessions_signals.csv'),
    ]
    
    results = []
    
    for config_name, signals_file in configurations:
        result = backtest_configuration(config_name, signals_file)
        if result:
            results.append(result)
    
    # Summary comparison
    if results:
        print("\n" + "=" * 90)
        print("CONFIGURATION COMPARISON")
        print("=" * 90)
        
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('total_pnl', ascending=False)
        
        print(results_df[['config', 'trades', 'win_rate', 'total_pnl', 'max_drawdown', 'sharpe_ratio']].to_string(index=False))
        print("=" * 90)
        
        # Save comparison
        comparison_file = 'results/audusd_configuration_comparison.csv'
        results_df.to_csv(comparison_file, index=False)
        logger.info(f"\nComparison saved to {comparison_file}")
    
    return results


if __name__ == "__main__":
    main()


