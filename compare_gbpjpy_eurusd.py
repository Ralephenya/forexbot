"""
Compare Strategy B performance: GBP/JPY vs EUR/USD
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


def analyze_by_hour(trades_df, pair_name):
    """Analyze performance by hour"""
    trades_df['entry_hour'] = trades_df['entry_time'].dt.hour
    
    hourly_stats = trades_df.groupby('entry_hour').agg({
        'pnl': ['count', 'sum', 'mean']
    }).reset_index()
    hourly_stats.columns = ['hour', 'trades', 'total_pnl', 'avg_pnl']
    
    hourly_stats['win_rate'] = trades_df.groupby('entry_hour').apply(
        lambda x: (x['pnl'] > 0).sum() / len(x) * 100 if len(x) > 0 else 0
    ).values
    
    hourly_stats = hourly_stats.sort_values('total_pnl', ascending=False)
    
    return hourly_stats


def analyze_volatility_regime(trades_df, signals_df):
    """Analyze performance by volatility regime"""
    # Merge with signals to get volatility regime
    trades_with_regime = trades_df.merge(
        signals_df[['datetime', 'is_high_vol']],
        left_on='entry_time',
        right_on='datetime',
        how='left'
    )
    
    trades_with_regime['regime'] = trades_with_regime['is_high_vol'].map({True: 'High', False: 'Low'})
    
    regime_stats = trades_with_regime.groupby('regime').agg({
        'pnl': ['count', 'sum', 'mean']
    }).reset_index()
    regime_stats.columns = ['regime', 'trades', 'total_pnl', 'avg_pnl']
    
    regime_stats['win_rate'] = trades_with_regime.groupby('regime').apply(
        lambda x: (x['pnl'] > 0).sum() / len(x) * 100 if len(x) > 0 else 0
    ).values
    
    return regime_stats


def main():
    """Main comparison function"""
    logger.info("=" * 70)
    logger.info("STRATEGY B COMPARISON: GBP/JPY vs EUR/USD")
    logger.info("=" * 70)
    
    # Load results
    eurusd_results = pd.read_csv('results/backtest_results_b_regimeswitching.csv')
    gbpjpy_results_file = 'results/backtest_results_strategy_b_gbpjpy.csv'
    
    if not os.path.exists(gbpjpy_results_file):
        logger.error(f"GBP/JPY results file not found: {gbpjpy_results_file}")
        logger.error("Please run the GBP/JPY backtest first:")
        logger.error("  1. Download GBP/JPY data")
        logger.error("  2. Run: python strategy_b_gbpjpy.py")
        logger.error("  3. Run: python backtest_strategy_b_gbpjpy.py")
        return
    
    gbpjpy_results = pd.read_csv(gbpjpy_results_file)
    
    # Convert datetime columns
    eurusd_results['exit_time'] = pd.to_datetime(eurusd_results['exit_time'], utc=True)
    eurusd_results['entry_time'] = pd.to_datetime(eurusd_results['entry_time'], utc=True)
    gbpjpy_results['exit_time'] = pd.to_datetime(gbpjpy_results['exit_time'], utc=True)
    gbpjpy_results['entry_time'] = pd.to_datetime(gbpjpy_results['entry_time'], utc=True)
    
    # Calculate metrics for both
    comparison_data = []
    
    for name, df in [('EUR/USD', eurusd_results), ('GBP/JPY', gbpjpy_results)]:
        total_trades = len(df)
        win_rate = (df['pnl'] > 0).sum() / total_trades * 100 if total_trades > 0 else 0
        total_pnl = df['pnl'].sum()
        avg_pips = df['pips'].mean()
        
        # Sharpe ratio
        sharpe = calculate_sharpe_ratio(df)
        
        # Drawdown
        daily_pnl = df.groupby(df['exit_time'].dt.date)['pnl'].sum()
        cumulative = daily_pnl.cumsum()
        running_max = cumulative.cummax()
        drawdown = cumulative - running_max
        max_drawdown = drawdown.min()
        
        # Profit factor
        winning_pnl = df[df['pnl'] > 0]['pnl'].sum()
        losing_pnl = abs(df[df['pnl'] < 0]['pnl'].sum())
        profit_factor = winning_pnl / losing_pnl if losing_pnl > 0 else 0
        
        comparison_data.append({
            'Pair': name,
            'Trades': total_trades,
            'Win Rate %': win_rate,
            'Total P&L': total_pnl,
            'Avg Pips': avg_pips,
            'Max Drawdown': max_drawdown,
            'Sharpe Ratio': sharpe,
            'Profit Factor': profit_factor
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # Print comparison
    print("\n" + "=" * 90)
    print("STRATEGY B: GBP/JPY vs EUR/USD COMPARISON")
    print("=" * 90)
    print(comparison_df.to_string(index=False))
    
    # Calculate improvement
    eurusd_pnl = comparison_df[comparison_df['Pair'] == 'EUR/USD']['Total P&L'].values[0]
    gbpjpy_pnl = comparison_df[comparison_df['Pair'] == 'GBP/JPY']['Total P&L'].values[0]
    
    improvement = gbpjpy_pnl - eurusd_pnl
    improvement_pct = (improvement / abs(eurusd_pnl)) * 100 if eurusd_pnl != 0 else 0
    multiplier = gbpjpy_pnl / eurusd_pnl if eurusd_pnl != 0 else 0
    
    print("\n" + "=" * 90)
    print("KEY FINDINGS")
    print("=" * 90)
    print(f"\n1. PROFITABILITY COMPARISON:")
    print(f"   EUR/USD: ${eurusd_pnl:.2f}")
    print(f"   GBP/JPY: ${gbpjpy_pnl:.2f}")
    print(f"   Difference: ${improvement:.2f} ({improvement_pct:+.1f}%)")
    print(f"   Multiplier: {multiplier:.2f}x")
    
    if gbpjpy_pnl > eurusd_pnl:
        if multiplier >= 1.5:
            print(f"   → HYPOTHESIS CONFIRMED: GBP/JPY produces {multiplier:.2f}x profits! ✅✅")
        else:
            print(f"   → GBP/JPY is more profitable but not 1.5-2x as expected")
    else:
        print(f"   → HYPOTHESIS REJECTED: EUR/USD is more profitable")
    
    eurusd_wr = comparison_df[comparison_df['Pair'] == 'EUR/USD']['Win Rate %'].values[0]
    gbpjpy_wr = comparison_df[comparison_df['Pair'] == 'GBP/JPY']['Win Rate %'].values[0]
    
    print(f"\n2. WIN RATE COMPARISON:")
    print(f"   EUR/USD: {eurusd_wr:.2f}%")
    print(f"   GBP/JPY: {gbpjpy_wr:.2f}%")
    print(f"   Difference: {gbpjpy_wr - eurusd_wr:+.2f}%")
    
    print(f"\n3. SUCCESS CRITERIA EVALUATION (GBP/JPY):")
    print(f"   Total P&L > $2.11: ${gbpjpy_pnl:.2f} {'✅' if gbpjpy_pnl > 2.11 else '❌'}")
    print(f"   Win Rate > 46%: {gbpjpy_wr:.2f}% {'✅' if gbpjpy_wr > 46 else '❌'}")
    
    max_dd_gbpjpy = comparison_df[comparison_df['Pair'] == 'GBP/JPY']['Max Drawdown'].values[0]
    print(f"   Max Drawdown < $2.00: ${abs(max_dd_gbpjpy):.2f} {'✅' if abs(max_dd_gbpjpy) < 2.00 else '❌'}")
    
    # Analyze by hour (if signals available)
    try:
        eurusd_signals = pd.read_csv('data/eurusd_15min_6months_b_regimeswitching_signals.csv')
        eurusd_signals['datetime'] = pd.to_datetime(eurusd_signals['datetime'], utc=True)
        eurusd_hourly = analyze_by_hour(eurusd_results, 'EUR/USD')
        
        gbpjpy_signals = pd.read_csv('data/gbpjpy_15min_6months_strategy_b_signals.csv')
        gbpjpy_signals['datetime'] = pd.to_datetime(gbpjpy_signals['datetime'], utc=True)
        gbpjpy_hourly = analyze_by_hour(gbpjpy_results, 'GBP/JPY')
        
        print(f"\n4. BEST TRADING HOURS (GBP/JPY):")
        print(gbpjpy_hourly.head(5).to_string(index=False))
        
        # Volatility regime analysis
        eurusd_regime = analyze_volatility_regime(eurusd_results, eurusd_signals)
        gbpjpy_regime = analyze_volatility_regime(gbpjpy_results, gbpjpy_signals)
        
        print(f"\n5. VOLATILITY REGIME PERFORMANCE (GBP/JPY):")
        print(gbpjpy_regime.to_string(index=False))
        
    except Exception as e:
        logger.warning(f"Could not analyze by hour/regime: {str(e)}")
    
    # Save comparison
    comparison_df.to_csv('results/quant_analysis/gbpjpy_vs_eurusd_comparison.csv', index=False)
    print(f"\nComparison saved to: results/quant_analysis/gbpjpy_vs_eurusd_comparison.csv")
    print("=" * 90)


if __name__ == "__main__":
    main()























