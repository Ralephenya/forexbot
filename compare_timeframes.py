"""
Compare Strategy B performance on 15-minute vs 1-hour timeframes
"""

import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_sharpe_ratio(trades_df):
    """Calculate Sharpe Ratio"""
    if len(trades_df) == 0:
        return 0
    
    returns = trades_df['pnl'].values
    if len(returns) == 0 or returns.std() == 0:
        return 0
    
    excess_returns = returns - 0  # No risk-free rate
    sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252) if excess_returns.std() > 0 else 0
    
    return sharpe


def main():
    """Compare 15-minute vs 1-hour results"""
    logger.info("=" * 70)
    logger.info("TIMEFRAME COMPARISON: 15-MINUTE vs 1-HOUR")
    logger.info("=" * 70)
    
    # Load results
    results_15min = pd.read_csv('results/backtest_results_b_regimeswitching.csv')
    results_1hour = pd.read_csv('results/backtest_results_strategy_b_1hour.csv')
    
    results_15min['exit_time'] = pd.to_datetime(results_15min['exit_time'], utc=True)
    results_15min['entry_time'] = pd.to_datetime(results_15min['entry_time'], utc=True)
    results_1hour['exit_time'] = pd.to_datetime(results_1hour['exit_time'], utc=True)
    results_1hour['entry_time'] = pd.to_datetime(results_1hour['entry_time'], utc=True)
    
    # Calculate metrics for both
    comparison_data = []
    
    for name, df in [('15-Minute', results_15min), ('1-Hour', results_1hour)]:
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
        
        # Average trade duration (in hours for 15-min, hours for 1-hour)
        df['duration'] = (df['exit_time'] - df['entry_time']).dt.total_seconds() / 3600
        avg_duration = df['duration'].mean()
        
        comparison_data.append({
            'Timeframe': name,
            'Trades': total_trades,
            'Win Rate %': win_rate,
            'Total P&L': total_pnl,
            'Avg Pips': avg_pips,
            'Max Drawdown': max_drawdown,
            'Sharpe Ratio': sharpe,
            'Profit Factor': profit_factor,
            'Avg Duration (hours)': avg_duration
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # Print comparison
    print("\n" + "=" * 90)
    print("STRATEGY B: TIMEFRAME COMPARISON")
    print("=" * 90)
    print(comparison_df.to_string(index=False))
    
    # Calculate improvement
    pnl_15min = comparison_df[comparison_df['Timeframe'] == '15-Minute']['Total P&L'].values[0]
    pnl_1hour = comparison_df[comparison_df['Timeframe'] == '1-Hour']['Total P&L'].values[0]
    
    improvement = pnl_1hour - pnl_15min
    improvement_pct = (improvement / abs(pnl_15min)) * 100 if pnl_15min != 0 else 0
    
    print("\n" + "=" * 90)
    print("KEY FINDINGS")
    print("=" * 90)
    print(f"\n1. PROFITABILITY:")
    print(f"   15-Minute: ${pnl_15min:.2f}")
    print(f"   1-Hour: ${pnl_1hour:.2f}")
    print(f"   Difference: ${improvement:.2f} ({improvement_pct:+.1f}%)")
    
    if pnl_1hour > pnl_15min:
        print(f"   → 1-Hour timeframe is MORE profitable! ✅")
    else:
        print(f"   → 15-Minute timeframe is more profitable")
    
    trades_15min = comparison_df[comparison_df['Timeframe'] == '15-Minute']['Trades'].values[0]
    trades_1hour = comparison_df[comparison_df['Timeframe'] == '1-Hour']['Trades'].values[0]
    
    print(f"\n2. TRADE FREQUENCY:")
    print(f"   15-Minute: {trades_15min} trades")
    print(f"   1-Hour: {trades_1hour} trades")
    print(f"   Reduction: {trades_15min - trades_1hour} trades ({((trades_15min - trades_1hour) / trades_15min * 100):.1f}% fewer)")
    
    wr_15min = comparison_df[comparison_df['Timeframe'] == '15-Minute']['Win Rate %'].values[0]
    wr_1hour = comparison_df[comparison_df['Timeframe'] == '1-Hour']['Win Rate %'].values[0]
    
    print(f"\n3. WIN RATE:")
    print(f"   15-Minute: {wr_15min:.2f}%")
    print(f"   1-Hour: {wr_1hour:.2f}%")
    print(f"   Difference: {wr_1hour - wr_15min:+.2f}%")
    
    sharpe_15min = comparison_df[comparison_df['Timeframe'] == '15-Minute']['Sharpe Ratio'].values[0]
    sharpe_1hour = comparison_df[comparison_df['Timeframe'] == '1-Hour']['Sharpe Ratio'].values[0]
    
    print(f"\n4. RISK-ADJUSTED RETURNS (Sharpe Ratio):")
    print(f"   15-Minute: {sharpe_15min:.2f}")
    print(f"   1-Hour: {sharpe_1hour:.2f}")
    print(f"   Difference: {sharpe_1hour - sharpe_15min:+.2f}")
    
    if sharpe_1hour > sharpe_15min:
        print(f"   → 1-Hour has BETTER risk-adjusted returns! ✅")
    
    print("\n" + "=" * 90)
    print("CONCLUSION")
    print("=" * 90)
    
    if pnl_1hour > pnl_15min and sharpe_1hour > sharpe_15min:
        print("✅ HYPOTHESIS CONFIRMED: 1-Hour timeframe shows better performance!")
        print(f"   - Higher profitability (${improvement:.2f} more)")
        print(f"   - Better risk-adjusted returns (Sharpe {sharpe_1hour:.2f} vs {sharpe_15min:.2f})")
        print(f"   - Fewer trades = lower transaction costs")
    elif pnl_1hour > pnl_15min:
        print("⚠️  PARTIAL CONFIRMATION: 1-Hour is more profitable but has lower Sharpe")
    else:
        print("❌ HYPOTHESIS REJECTED: 15-Minute timeframe performs better")
        print(f"   - 15-Minute: ${pnl_15min:.2f} vs 1-Hour: ${pnl_1hour:.2f}")
    
    # Save comparison
    comparison_df.to_csv('results/quant_analysis/timeframe_comparison.csv', index=False)
    print(f"\nComparison saved to: results/quant_analysis/timeframe_comparison.csv")
    print("=" * 90)


if __name__ == "__main__":
    main()

