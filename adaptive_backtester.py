"""
Adaptive Backtester - Supports dynamic targets/stops based on ATR
"""

import pandas as pd
import logging
import config
from backtester import Trade

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def adaptive_backtest(df, use_adaptive_targets=True):
    """
    Run backtest with adaptive targets/stops based on ATR
    
    Args:
        df: pandas.DataFrame with signals and price data
        use_adaptive_targets: If True, use adaptive_target_pips/adaptive_stop_pips columns
    
    Returns:
        List of Trade objects
    """
    try:
        logger.info(f"Starting adaptive backtest on {len(df)} data points...")
        
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
                    target_pips = config.TARGET_PIPS
                    stop_pips = config.STOP_LOSS_PIPS
                
                # Check for end of trading day
                current_hour = dt.hour
                if current_hour >= config.TRADING_END_HOUR:
                    current_trade.close(dt, close_price, 'end_of_day')
                    trades.append(current_trade)
                    current_trade = None
                    continue
                
                # Check for exit conditions
                if current_trade.direction == 'BUY':
                    target_price = current_trade.entry_price + (target_pips / 10000)
                    stop_price = current_trade.entry_price - (stop_pips / 10000)
                    
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
                    target_price = current_trade.entry_price - (target_pips / 10000)
                    stop_price = current_trade.entry_price + (stop_pips / 10000)
                    
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
                    entry_price = entry_price + (config.SPREAD_COST_PIPS / 10000 / 2)
                    current_trade = Trade(dt, entry_price, 'BUY')
                    # Store adaptive targets in trade object
                    if use_adaptive_targets and 'adaptive_target_pips' in row:
                        current_trade.adaptive_target = row['adaptive_target_pips']
                        current_trade.adaptive_stop = row['adaptive_stop_pips']
                
                elif row['sell_signal']:
                    entry_price = entry_price - (config.SPREAD_COST_PIPS / 10000 / 2)
                    current_trade = Trade(dt, entry_price, 'SELL')
                    if use_adaptive_targets and 'adaptive_target_pips' in row:
                        current_trade.adaptive_target = row['adaptive_target_pips']
                        current_trade.adaptive_stop = row['adaptive_stop_pips']
        
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


def backtest_strategy(signals_file, strategy_name, use_adaptive=True):
    """Backtest a strategy from signals file"""
    import os
    
    try:
        logger.info(f"Backtesting {strategy_name}...")
        
        if not os.path.exists(signals_file):
            raise FileNotFoundError(f"Signals file not found: {signals_file}")
        
        df = pd.read_csv(signals_file)
        df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
        
        # Run backtest
        trades = adaptive_backtest(df, use_adaptive_targets=use_adaptive)
        
        if len(trades) == 0:
            return {
                'strategy': strategy_name,
                'total_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_pips': 0,
                'max_drawdown': 0
            }
        
        # Convert to DataFrame
        trades_df = pd.DataFrame([t.to_dict() for t in trades])
        trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'], utc=True)
        
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
        results_file = f"results/backtest_results_{strategy_name.lower()}.csv"
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        trades_df.to_csv(results_file, index=False)
        
        return {
            'strategy': strategy_name,
            'total_trades': len(trades_df),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_pips': avg_pips,
            'max_drawdown': max_drawdown,
            'results_file': results_file
        }
        
    except Exception as e:
        logger.error(f"Error backtesting {strategy_name}: {str(e)}")
        raise


def main():
    """Backtest all advanced strategies"""
    logger.info("=" * 70)
    logger.info("ADAPTIVE BACKTESTER - ADVANCED STRATEGIES")
    logger.info("=" * 70)
    
    strategies = [
        ('A_TimeFilteredRSI', 'data/eurusd_15min_6months_a_timefilteredrsi_signals.csv', True),
        ('B_RegimeSwitching', 'data/eurusd_15min_6months_b_regimeswitching_signals.csv', True),
        ('C_MultiFactor', 'data/eurusd_15min_6months_c_multifactor_signals.csv', True),
    ]
    
    results = []
    for name, signals_file, use_adaptive in strategies:
        try:
            result = backtest_strategy(signals_file, name, use_adaptive)
            results.append(result)
            
            logger.info(f"{name}: {result['total_trades']} trades, "
                       f"Win Rate: {result['win_rate']:.2f}%, "
                       f"P&L: ${result['total_pnl']:.2f}")
        except Exception as e:
            logger.error(f"Failed to backtest {name}: {str(e)}")
    
    # Print comparison
    logger.info("\n" + "=" * 70)
    logger.info("ADVANCED STRATEGIES COMPARISON")
    logger.info("=" * 70)
    
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('total_pnl', ascending=False)
    
    print("\n" + results_df.to_string(index=False))
    
    return results


if __name__ == "__main__":
    main()























