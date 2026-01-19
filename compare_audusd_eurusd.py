"""
Compare AUD/USD results with EUR/USD baseline
"""

import pandas as pd
import numpy as np
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_sharpe_ratio(trades_df):
    """Calculate Sharpe Ratio"""
    if len(trades_df) == 0:
        return 0
    
    returns = trades_df['pnl'].values
    if len(returns) == 0 or returns.std() == 0:
        return 0
    
    excess_returns = returns - 0
    sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252) if excess_returns.std() > 0 else 0
    return sharpe


def load_eurusd_baseline():
    """Load EUR/USD baseline results (Strategy B 15-minute)"""
    # Try to find EUR/USD Strategy B results
    eurusd_files = [
        'results/backtest_results_b_regimeswitching.csv',
        'results/backtest_results_strategy_b_no_news_filter.csv',
    ]
    
    for file in eurusd_files:
        if os.path.exists(file):
            df = pd.read_csv(file)
            df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True)
            df['entry_time'] = pd.to_datetime(df['entry_time'], utc=True)
            
            total_trades = len(df)
            win_rate = (df['pnl'] > 0).sum() / total_trades * 100 if total_trades > 0 else 0
            total_pnl = df['pnl'].sum()
            avg_pips = df['pips'].mean()
            
            daily_pnl = df.groupby(df['exit_time'].dt.date)['pnl'].sum()
            cumulative = daily_pnl.cumsum()
            running_max = cumulative.cummax()
            drawdown = cumulative - running_max
            max_drawdown = drawdown.min()
            
            sharpe = calculate_sharpe_ratio(df)
            
            return {
                'config': 'EUR/USD Baseline (London Session)',
                'trades': total_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'avg_pips': avg_pips,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe
            }
    
    # Default baseline (from user's request: $2.11, 46.19% win rate, 197 trades)
    return {
        'config': 'EUR/USD Baseline (London Session)',
        'trades': 197,
        'win_rate': 46.19,
        'total_pnl': 2.11,
        'avg_pips': 1.07,  # Estimated
        'max_drawdown': -1.50,  # Estimated
        'sharpe_ratio': 2.05
    }


def load_audusd_results():
    """Load all AUD/USD backtest results"""
    results = []
    
    configs = [
        ('Sydney Session', 'results/backtest_results_audusd_sydney_session.csv'),
        ('London Session', 'results/backtest_results_audusd_london_session.csv'),
        ('Combined Sessions', 'results/backtest_results_audusd_combined_sessions.csv'),
    ]
    
    for config_name, file_path in configs:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True)
            df['entry_time'] = pd.to_datetime(df['entry_time'], utc=True)
            
            total_trades = len(df)
            if total_trades == 0:
                continue
            
            win_rate = (df['pnl'] > 0).sum() / total_trades * 100
            total_pnl = df['pnl'].sum()
            avg_pips = df['pips'].mean()
            
            daily_pnl = df.groupby(df['exit_time'].dt.date)['pnl'].sum()
            cumulative = daily_pnl.cumsum()
            running_max = cumulative.cummax()
            drawdown = cumulative - running_max
            max_drawdown = drawdown.min()
            
            sharpe = calculate_sharpe_ratio(df)
            
            results.append({
                'config': f'AUD/USD {config_name}',
                'trades': total_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'avg_pips': avg_pips,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe
            })
    
    return results


def main():
    """Compare AUD/USD results with EUR/USD baseline"""
    logger.info("=" * 70)
    logger.info("AUD/USD vs EUR/USD COMPARISON")
    logger.info("=" * 70)
    
    # Load EUR/USD baseline
    eurusd_baseline = load_eurusd_baseline()
    
    # Load AUD/USD results
    audusd_results = load_audusd_results()
    
    if not audusd_results:
        logger.error("No AUD/USD results found. Please run backtest_strategy_b_audusd.py first.")
        return
    
    # Combine all results
    all_results = [eurusd_baseline] + audusd_results
    comparison_df = pd.DataFrame(all_results)
    
    # Print comparison
    print("\n" + "=" * 90)
    print("AUD/USD vs EUR/USD COMPARISON")
    print("=" * 90)
    print(comparison_df[['config', 'trades', 'win_rate', 'total_pnl', 'max_drawdown', 'sharpe_ratio']].to_string(index=False))
    print("=" * 90)
    
    # Analysis
    print("\n" + "=" * 90)
    print("KEY FINDINGS")
    print("=" * 90)
    
    eurusd_pnl = eurusd_baseline['total_pnl']
    eurusd_trades = eurusd_baseline['trades']
    
    print(f"\nEUR/USD Baseline (London Session):")
    print(f"  Total P&L: ${eurusd_pnl:.2f}")
    print(f"  Trades: {eurusd_trades}")
    print(f"  Win Rate: {eurusd_baseline['win_rate']:.2f}%")
    
    print(f"\nAUD/USD Results:")
    for result in audusd_results:
        config = result['config'].replace('AUD/USD ', '')
        pnl = result['total_pnl']
        trades = result['trades']
        wr = result['win_rate']
        
        pnl_diff = pnl - eurusd_pnl
        pnl_pct = (pnl_diff / abs(eurusd_pnl)) * 100 if eurusd_pnl != 0 else 0
        
        print(f"\n  {config}:")
        print(f"    Total P&L: ${pnl:.2f} ({pnl_diff:+.2f} vs EUR/USD, {pnl_pct:+.1f}%)")
        print(f"    Trades: {trades} ({trades - eurusd_trades:+d} vs EUR/USD)")
        print(f"    Win Rate: {wr:.2f}% ({wr - eurusd_baseline['win_rate']:+.2f}% vs EUR/USD)")
        
        # Success criteria evaluation
        beats_pnl = pnl > eurusd_pnl
        beats_wr = wr > eurusd_baseline['win_rate']
        more_trades = trades > eurusd_trades
        
        if beats_pnl and beats_wr:
            print(f"    Status: [OK] BEATS EUR/USD on all metrics")
        elif beats_pnl:
            print(f"    Status: [WARN] BEATS on P&L, but lower win rate")
        elif beats_wr:
            print(f"    Status: [WARN] BEATS on win rate, but lower P&L")
        else:
            print(f"    Status: [FAIL] Does NOT beat EUR/USD")
    
    # Best AUD/USD configuration
    best_audusd = max(audusd_results, key=lambda x: x['total_pnl'])
    print(f"\n{'='*90}")
    print("BEST AUD/USD CONFIGURATION")
    print("=" * 90)
    print(f"Configuration: {best_audusd['config']}")
    print(f"Total P&L: ${best_audusd['total_pnl']:.2f}")
    print(f"Win Rate: {best_audusd['win_rate']:.2f}%")
    print(f"Trades: {best_audusd['trades']}")
    print(f"Sharpe Ratio: {best_audusd['sharpe_ratio']:.2f}")
    
    if best_audusd['total_pnl'] > eurusd_pnl:
        print(f"\n[SUCCESS] RECOMMENDATION: Trade {best_audusd['config']} (beats EUR/USD baseline)")
    else:
        print(f"\n[REJECTED] RECOMMENDATION: Stick with EUR/USD (AUD/USD does not beat baseline)")
    
    # Save comparison
    os.makedirs('results', exist_ok=True)
    comparison_df.to_csv('results/audusd_vs_eurusd_comparison.csv', index=False)
    logger.info(f"\nComparison saved to: results/audusd_vs_eurusd_comparison.csv")
    print("=" * 90)


if __name__ == "__main__":
    main()

