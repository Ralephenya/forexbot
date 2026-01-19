"""
Multi-Pair Portfolio Backtester
Handles multiple currency pairs simultaneously with Strategy B
Maximum 2 positions open at once across all pairs
"""

import pandas as pd
import numpy as np
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pair-specific parameters
PAIR_CONFIGS = {
    'eurusd': {
        'spread': 1.0,
        'pip_multiplier': 10000,  # 1 pip = 0.0001
        'pip_value': 0.10  # $0.10 per pip for 0.01 lots
    },
    'gbpusd': {
        'spread': 1.5,
        'pip_multiplier': 10000,  # 1 pip = 0.0001
        'pip_value': 0.10
    },
    'usdjpy': {
        'spread': 1.5,
        'pip_multiplier': 100,  # 1 pip = 0.01 (JPY pairs)
        'pip_value': 0.10
    }
}

TRADING_END_HOUR = 17  # 5 PM UTC


class PortfolioTrade:
    """Trade class for portfolio backtester"""
    def __init__(self, entry_time, entry_price, direction, pair):
        self.entry_time = entry_time
        self.entry_price = entry_price
        self.direction = direction  # 'BUY' or 'SELL'
        self.pair = pair
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
        
        # Get pair config
        config = PAIR_CONFIGS[self.pair]
        pip_mult = config['pip_multiplier']
        
        # Calculate pips
        if self.direction == 'BUY':
            self.pips = (exit_price - self.entry_price) * pip_mult
        else:  # SELL
            self.pips = (self.entry_price - exit_price) * pip_mult
        
        # Calculate P&L
        self.pnl = self.pips * config['pip_value']
    
    def to_dict(self):
        """Convert trade to dictionary"""
        return {
            'pair': self.pair,
            'entry_time': self.entry_time,
            'entry_price': self.entry_price,
            'exit_time': self.exit_time,
            'exit_price': self.exit_price,
            'direction': self.direction,
            'pips': self.pips,
            'pnl': self.pnl,
            'exit_reason': self.exit_reason
        }


def portfolio_backtest(signals_dict, max_positions=2):
    """
    Run portfolio backtest across multiple pairs
    
    Args:
        signals_dict: Dictionary of {pair_name: signals_dataframe}
        max_positions: Maximum number of positions open simultaneously
    
    Returns:
        List of PortfolioTrade objects
    """
    logger.info("=" * 70)
    logger.info("PORTFOLIO BACKTESTER")
    logger.info("=" * 70)
    logger.info(f"Pairs: {list(signals_dict.keys())}")
    logger.info(f"Max positions: {max_positions}")
    
    # Combine all signals into one timeline
    all_candles = []
    for pair, df in signals_dict.items():
        df = df.copy()
        df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
        df['pair'] = pair
        all_candles.append(df)
    
    # Combine and sort by datetime
    combined = pd.concat(all_candles, ignore_index=True)
    combined = combined.sort_values('datetime').reset_index(drop=True)
    
    logger.info(f"Total candles across all pairs: {len(combined)}")
    
    # Track open positions
    open_positions = {}  # {pair: PortfolioTrade}
    trades = []
    
    # Process each candle
    for i in range(len(combined)):
        row = combined.iloc[i]
        dt = row['datetime']
        pair = row['pair']
        close_price = row['close']
        high_price = row['high']
        low_price = row['low']
        
        # Check if we have an open position for this pair
        if pair in open_positions:
            trade = open_positions[pair]
            
            # Get adaptive targets
            target_pips = row.get('adaptive_target_pips', 10)
            stop_pips = row.get('adaptive_stop_pips', 8)
            
            # Get pair config
            config = PAIR_CONFIGS[pair]
            pip_mult = config['pip_multiplier']
            
            # Check for end of trading day
            current_hour = dt.hour
            if current_hour >= TRADING_END_HOUR:
                trade.close(dt, close_price, 'end_of_day')
                trades.append(trade)
                del open_positions[pair]
                continue
            
            # Check for exit conditions
            if trade.direction == 'BUY':
                target_price = trade.entry_price + (target_pips / pip_mult)
                stop_price = trade.entry_price - (stop_pips / pip_mult)
                
                if high_price >= target_price:
                    trade.close(dt, target_price, 'target')
                    trades.append(trade)
                    del open_positions[pair]
                    continue
                elif low_price <= stop_price:
                    trade.close(dt, stop_price, 'stop_loss')
                    trades.append(trade)
                    del open_positions[pair]
                    continue
            
            else:  # SELL
                target_price = trade.entry_price - (target_pips / pip_mult)
                stop_price = trade.entry_price + (stop_pips / pip_mult)
                
                if low_price <= target_price:
                    trade.close(dt, target_price, 'target')
                    trades.append(trade)
                    del open_positions[pair]
                    continue
                elif high_price >= stop_price:
                    trade.close(dt, stop_price, 'stop_loss')
                    trades.append(trade)
                    del open_positions[pair]
                    continue
        
        # Check for new entry signals (only if we have capacity)
        if len(open_positions) < max_positions:
            if pair not in open_positions:  # Don't add second position in same pair
                config = PAIR_CONFIGS[pair]
                spread_pips = config['spread']
                pip_mult = config['pip_multiplier']
                
                entry_price = close_price
                
                if row['buy_signal']:
                    entry_price = entry_price + (spread_pips / pip_mult / 2)
                    trade = PortfolioTrade(dt, entry_price, 'BUY', pair)
                    open_positions[pair] = trade
                
                elif row['sell_signal']:
                    entry_price = entry_price - (spread_pips / pip_mult / 2)
                    trade = PortfolioTrade(dt, entry_price, 'SELL', pair)
                    open_positions[pair] = trade
    
    # Close any remaining positions
    for pair, trade in list(open_positions.items()):
        # Find last price for this pair
        pair_data = combined[combined['pair'] == pair]
        if len(pair_data) > 0:
            last_price = pair_data.iloc[-1]['close']
            last_time = pair_data.iloc[-1]['datetime']
            trade.close(last_time, last_price, 'end_of_data')
            trades.append(trade)
    
    logger.info(f"Portfolio backtest completed. Generated {len(trades)} trades")
    
    return trades


def main():
    """Main function"""
    logger.info("=" * 70)
    logger.info("MULTI-PAIR PORTFOLIO BACKTESTER")
    logger.info("=" * 70)
    
    # Load signals for each pair
    signals_files = {
        'eurusd': 'data/eurusd_15min_6months_strategy_b_signals.csv',
        'gbpusd': 'data/gbpusd_15min_6months_strategy_b_signals.csv',
        'usdjpy': 'data/usdjpy_15min_6months_strategy_b_signals.csv'
    }
    
    signals_dict = {}
    for pair, file_path in signals_files.items():
        if os.path.exists(file_path):
            logger.info(f"Loading {pair.upper()} signals from {file_path}...")
            df = pd.read_csv(file_path)
            signals_dict[pair] = df
            logger.info(f"  Loaded {len(df)} candles")
        else:
            logger.warning(f"Signals file not found: {file_path}")
    
    if len(signals_dict) == 0:
        logger.error("No signals files found! Please run apply_strategy_b_all_pairs.py first")
        return
    
    logger.info(f"\nLoaded signals for {len(signals_dict)} pair(s): {list(signals_dict.keys())}")
    
    # Run portfolio backtest
    trades = portfolio_backtest(signals_dict, max_positions=2)
    
    if len(trades) == 0:
        logger.warning("No trades generated!")
        return
    
    # Convert to DataFrame
    trades_df = pd.DataFrame([t.to_dict() for t in trades])
    trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'], utc=True)
    trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'], utc=True)
    
    # Calculate metrics
    print("\n" + "=" * 70)
    print("PORTFOLIO BACKTEST RESULTS")
    print("=" * 70)
    
    # Overall portfolio metrics
    total_trades = len(trades_df)
    winning_trades = trades_df[trades_df['pnl'] > 0]
    win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
    total_pnl = trades_df['pnl'].sum()
    avg_pips = trades_df['pips'].mean()
    
    print(f"\nOVERALL PORTFOLIO:")
    print(f"  Total Trades: {total_trades}")
    print(f"  Win Rate: {win_rate:.2f}%")
    print(f"  Total P&L: ${total_pnl:.2f}")
    print(f"  Average Pips: {avg_pips:.2f}")
    
    # Per-pair breakdown
    print(f"\nPER-PAIR PERFORMANCE:")
    for pair in trades_df['pair'].unique():
        pair_trades = trades_df[trades_df['pair'] == pair]
        pair_wins = pair_trades[pair_trades['pnl'] > 0]
        pair_pnl = pair_trades['pnl'].sum()
        pair_wr = (len(pair_wins) / len(pair_trades) * 100) if len(pair_trades) > 0 else 0
        
        print(f"  {pair.upper()}:")
        print(f"    Trades: {len(pair_trades)}")
        print(f"    Win Rate: {pair_wr:.2f}%")
        print(f"    Total P&L: ${pair_pnl:.2f}")
    
    # Calculate drawdown
    trades_df_sorted = trades_df.sort_values('exit_time')
    daily_pnl = trades_df_sorted.groupby(trades_df_sorted['exit_time'].dt.date)['pnl'].sum()
    cumulative = daily_pnl.cumsum()
    running_max = cumulative.cummax()
    drawdown = cumulative - running_max
    max_drawdown = drawdown.min()
    
    print(f"\n  Max Drawdown: ${max_drawdown:.2f}")
    
    # Save results
    results_file = "results/backtest_results_portfolio_strategy_b.csv"
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    trades_df.to_csv(results_file, index=False)
    print(f"\nResults saved to: {results_file}")
    print("=" * 70)
    
    return trades_df


if __name__ == "__main__":
    main()

