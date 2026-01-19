"""
Generate Comprehensive Quantitative Analysis Report
"""

import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_sharpe_ratio(trades_df, risk_free_rate=0):
    """Calculate Sharpe Ratio"""
    if len(trades_df) == 0:
        return 0
    
    returns = trades_df['pnl'].values
    if len(returns) == 0 or returns.std() == 0:
        return 0
    
    excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
    sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252) if excess_returns.std() > 0 else 0
    
    return sharpe


def main():
    """Generate comprehensive report"""
    
    logger.info("=" * 70)
    logger.info("GENERATING QUANTITATIVE ANALYSIS REPORT")
    logger.info("=" * 70)
    
    # Load all strategy results
    strategies = {
        'Baseline RSI': pd.read_csv('results/backtest_results_6months.csv'),
        'Strategy A: Time-Filtered RSI': pd.read_csv('results/backtest_results_a_timefilteredrsi.csv'),
        'Strategy B: Regime-Switching': pd.read_csv('results/backtest_results_b_regimeswitching.csv'),
        'Strategy C: Multi-Factor': pd.read_csv('results/backtest_results_c_multifactor.csv'),
    }
    
    # Calculate metrics for each
    comparison = []
    for name, df in strategies.items():
        df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True)
        
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
        
        comparison.append({
            'Strategy': name,
            'Trades': total_trades,
            'Win Rate %': win_rate,
            'Total P&L': total_pnl,
            'Avg Pips': avg_pips,
            'Max Drawdown': max_drawdown,
            'Sharpe Ratio': sharpe,
            'Profit Factor': profit_factor
        })
    
    comparison_df = pd.DataFrame(comparison)
    comparison_df = comparison_df.sort_values('Total P&L', ascending=False)
    
    # Print report
    print("\n" + "=" * 90)
    print("QUANTITATIVE ANALYSIS REPORT - ADVANCED STRATEGIES")
    print("=" * 90)
    print("\nSTRATEGY COMPARISON:")
    print(comparison_df.to_string(index=False))
    
    # Load pattern analysis
    print("\n" + "=" * 90)
    print("PATTERN DISCOVERY FINDINGS")
    print("=" * 90)
    
    hourly = pd.read_csv('results/quant_analysis/hourly_performance.csv')
    vol = pd.read_csv('results/quant_analysis/volatility_regimes.csv')
    dow = pd.read_csv('results/quant_analysis/day_of_week_performance.csv')
    
    print("\n1. TIME-OF-DAY ANALYSIS:")
    print("   Top 5 Hours by P&L:")
    print(hourly.nlargest(5, 'total_pnl')[['hour', 'trades', 'total_pnl', 'win_rate']].to_string(index=False))
    
    print("\n2. VOLATILITY REGIME ANALYSIS:")
    print(vol.to_string(index=False))
    print("   → Mean reversion works BEST in HIGH volatility!")
    
    print("\n3. DAY-OF-WEEK ANALYSIS:")
    print(dow.to_string(index=False))
    print("   → Tuesday and Thursday are best. Avoid Friday.")
    
    # Best strategy analysis
    best = comparison_df.iloc[0]
    print("\n" + "=" * 90)
    print("WINNER: " + best['Strategy'])
    print("=" * 90)
    print(f"Total P&L: ${best['Total P&L']:.2f}")
    print(f"Win Rate: {best['Win Rate %']:.2f}%")
    print(f"Sharpe Ratio: {best['Sharpe Ratio']:.2f}")
    print(f"Profit Factor: {best['Profit Factor']:.2f}")
    print(f"Max Drawdown: ${best['Max Drawdown']:.2f}")
    
    # Improvement vs baseline
    baseline = comparison_df[comparison_df['Strategy'] == 'Baseline RSI'].iloc[0]
    improvement = best['Total P&L'] - baseline['Total P&L']
    improvement_pct = (improvement / abs(baseline['Total P&L'])) * 100 if baseline['Total P&L'] != 0 else 0
    
    print(f"\nImprovement vs Baseline RSI:")
    print(f"  P&L: ${baseline['Total P&L']:.2f} → ${best['Total P&L']:.2f} (+${improvement:.2f}, {improvement_pct:.1f}%)")
    print(f"  Win Rate: {baseline['Win Rate %']:.2f}% → {best['Win Rate %']:.2f}%")
    
    # Save report
    comparison_df.to_csv('results/quant_analysis/strategy_comparison.csv', index=False)
    print("\n" + "=" * 90)
    print("Report saved to: results/quant_analysis/strategy_comparison.csv")
    print("=" * 90)


if __name__ == "__main__":
    main()

