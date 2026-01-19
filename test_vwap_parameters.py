"""
Test VWAP Mean Reversion Strategy with Different SD Multipliers
Tests: 1.0, 1.5, 2.0, 2.5 SD multipliers
"""

import pandas as pd
import logging
import config
import os
import sys

# Import modules
from indicator_calculator import calculate_daily_vwap, add_indicators
from signal_detector import filter_trading_hours, detect_buy_signals, detect_sell_signals, add_signals
from backtester import backtest, Trade

logging.basicConfig(level=logging.WARNING)  # Reduce noise
logger = logging.getLogger(__name__)

# Test configurations
TEST_CONFIGS = [
    {"sd_multiplier": 1.0, "name": "VWAP 1.0 SD (Tight Bands)"},
    {"sd_multiplier": 1.5, "name": "VWAP 1.5 SD (Current)"},
    {"sd_multiplier": 2.0, "name": "VWAP 2.0 SD (Wide Bands)"},
    {"sd_multiplier": 2.5, "name": "VWAP 2.5 SD (Very Wide Bands)"},
]


def run_single_test(sd_multiplier):
    """Run a single VWAP test with given SD multiplier"""
    try:
        # Load data
        df = pd.read_csv(config.DATA_FILE)
        df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
        
        # Calculate indicators with custom SD multiplier
        df_indicators = calculate_daily_vwap(df.copy(), std_multiplier=sd_multiplier)
        
        # Detect signals
        df_signals = df_indicators.copy()
        df_signals = filter_trading_hours(df_signals)
        
        # Detect buy/sell signals
        buy_signals = detect_buy_signals(df_signals)
        sell_signals = detect_sell_signals(df_signals)
        
        # Add signals to original dataframe
        df_indicators['buy_signal'] = False
        df_indicators['sell_signal'] = False
        df_indicators.loc[df_signals.index, 'buy_signal'] = buy_signals
        df_indicators.loc[df_signals.index, 'sell_signal'] = sell_signals
        
        # Run backtest
        trades = backtest(df_indicators)
        
        # Calculate metrics
        if len(trades) == 0:
            return {
                'sd_multiplier': sd_multiplier,
                'total_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'buy_signals': buy_signals.sum(),
                'sell_signals': sell_signals.sum(),
                'avg_pips': 0,
                'max_drawdown': 0
            }
        
        trades_df = pd.DataFrame([t.to_dict() for t in trades])
        trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'], utc=True)
        
        winning_trades = trades_df[trades_df['pnl'] > 0]
        win_rate = (len(winning_trades) / len(trades_df) * 100) if len(trades_df) > 0 else 0
        total_pnl = trades_df['pnl'].sum()
        avg_pips = trades_df['pips'].mean()
        
        # Calculate drawdown
        daily_pnl = trades_df.groupby(trades_df['exit_time'].dt.date)['pnl'].sum().reset_index()
        daily_pnl['cumulative_pnl'] = daily_pnl['pnl'].cumsum()
        daily_pnl['running_max'] = daily_pnl['cumulative_pnl'].cummax()
        daily_pnl['drawdown'] = daily_pnl['cumulative_pnl'] - daily_pnl['running_max']
        max_drawdown = daily_pnl['drawdown'].min()
        
        return {
            'sd_multiplier': sd_multiplier,
            'total_trades': len(trades_df),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'buy_signals': buy_signals.sum(),
            'sell_signals': sell_signals.sum(),
            'total_signals': buy_signals.sum() + sell_signals.sum(),
            'avg_pips': avg_pips,
            'max_drawdown': max_drawdown,
            'winning_trades': len(winning_trades),
            'losing_trades': len(trades_df) - len(winning_trades)
        }
        
    except Exception as e:
        logger.error(f"Error in test with SD {sd_multiplier}: {str(e)}")
        return None


def main():
    """Run all VWAP parameter tests"""
    print("=" * 70)
    print("VWAP PARAMETER OPTIMIZATION TEST")
    print("=" * 70)
    print(f"Testing SD multipliers: {[c['sd_multiplier'] for c in TEST_CONFIGS]}")
    print(f"Dataset: {config.DATA_FILE}")
    print("=" * 70)
    print()
    
    results = []
    
    for config_test in TEST_CONFIGS:
        sd_mult = config_test['sd_multiplier']
        name = config_test['name']
        
        print(f"Testing {name}...")
        
        # Temporarily update config
        original_sd = config.VWAP_STD_MULTIPLIER
        config.VWAP_STD_MULTIPLIER = sd_mult
        
        try:
            result = run_single_test(sd_mult)
            if result:
                result['name'] = name
                results.append(result)
                
                print(f"  ✓ Completed: {result['total_trades']} trades, "
                      f"Win Rate: {result['win_rate']:.2f}%, "
                      f"P&L: ${result['total_pnl']:.2f}")
            else:
                print(f"  ✗ Failed")
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
        finally:
            # Restore original config
            config.VWAP_STD_MULTIPLIER = original_sd
        
        print()
    
    # Display comparison
    if results:
        print("=" * 70)
        print("RESULTS COMPARISON")
        print("=" * 70)
        print()
        
        # Create comparison DataFrame
        comparison_df = pd.DataFrame(results)
        comparison_df = comparison_df.sort_values('total_pnl', ascending=False)
        
        # Display table
        print(f"{'SD':<6} {'Trades':<8} {'Win Rate':<10} {'Total P&L':<12} {'Signals':<10} {'Avg Pips':<10} {'Drawdown':<12}")
        print("-" * 70)
        for _, row in comparison_df.iterrows():
            pnl_str = f"${row['total_pnl']:.2f}"
            pnl_color = "✓" if row['total_pnl'] > 0 else "✗"
            print(f"{row['sd_multiplier']:<6.1f} {int(row['total_trades']):<8} "
                  f"{row['win_rate']:<10.2f}% {pnl_color} {pnl_str:<10} "
                  f"{int(row['total_signals']):<10} {row['avg_pips']:<10.2f} "
                  f"${row['max_drawdown']:.2f}")
        
        print()
        print("=" * 70)
        
        # Find best configuration
        best = comparison_df.iloc[0]
        print(f"\nBEST CONFIGURATION: {best['name']}")
        print(f"  SD Multiplier: {best['sd_multiplier']}")
        print(f"  Total Trades: {int(best['total_trades'])}")
        print(f"  Win Rate: {best['win_rate']:.2f}%")
        print(f"  Total P&L: ${best['total_pnl']:.2f}")
        print(f"  Max Drawdown: ${best['max_drawdown']:.2f}")
        print(f"  Signals: {int(best['total_signals'])} ({int(best['total_signals']/211):.2f} per day)")
        print()
        
        # Save results
        output_file = "results/vwap_parameter_test_results.csv"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        comparison_df.to_csv(output_file, index=False)
        print(f"Results saved to: {output_file}")
        
    print("=" * 70)


if __name__ == "__main__":
    main()























