"""
Compare Strategy B performance across all timeframes: 15-min, 30-min, 1-hour
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
    
    excess_returns = returns - 0
    sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252) if excess_returns.std() > 0 else 0
    return sharpe


def main():
    """Compare all timeframes"""
    logger.info("=" * 70)
    logger.info("TIMEFRAME COMPARISON: 15-MIN vs 30-MIN vs 1-HOUR")
    logger.info("=" * 70)
    
    # Load results
    results_15min = pd.read_csv('results/backtest_results_b_regimeswitching.csv')
    results_30min = pd.read_csv('results/backtest_results_strategy_b_30min.csv')
    results_1hour = pd.read_csv('results/backtest_results_strategy_b_1hour.csv')
    
    # Convert datetime columns
    for df in [results_15min, results_30min, results_1hour]:
        df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True)
        df['entry_time'] = pd.to_datetime(df['entry_time'], utc=True)
    
    # Calculate metrics for all
    comparison_data = []
    
    for name, df in [('15-Minute', results_15min), ('30-Minute', results_30min), ('1-Hour', results_1hour)]:
        total_trades = len(df)
        win_rate = (df['pnl'] > 0).sum() / total_trades * 100 if total_trades > 0 else 0
        total_pnl = df['pnl'].sum()
        avg_pips = df['pips'].mean()
        
        sharpe = calculate_sharpe_ratio(df)
        
        daily_pnl = df.groupby(df['exit_time'].dt.date)['pnl'].sum()
        cumulative = daily_pnl.cumsum()
        running_max = cumulative.cummax()
        drawdown = cumulative - running_max
        max_drawdown = drawdown.min()
        
        winning_pnl = df[df['pnl'] > 0]['pnl'].sum()
        losing_pnl = abs(df[df['pnl'] < 0]['pnl'].sum())
        profit_factor = winning_pnl / losing_pnl if losing_pnl > 0 else 0
        
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
    print("STRATEGY B: TIMEFRAME COMPARISON (15-MIN vs 30-MIN vs 1-HOUR)")
    print("=" * 90)
    print(comparison_df.to_string(index=False))
    
    # Find best performer
    best = comparison_df.loc[comparison_df['Total P&L'].idxmax()]
    
    print("\n" + "=" * 90)
    print("KEY FINDINGS")
    print("=" * 90)
    
    print(f"\n1. PROFITABILITY RANKING:")
    sorted_by_pnl = comparison_df.sort_values('Total P&L', ascending=False)
    for idx, row in sorted_by_pnl.iterrows():
        rank = list(sorted_by_pnl.index).index(idx) + 1
        print(f"   {rank}. {row['Timeframe']}: ${row['Total P&L']:.2f}")
    
    print(f"\n2. WIN RATE RANKING:")
    sorted_by_wr = comparison_df.sort_values('Win Rate %', ascending=False)
    for idx, row in sorted_by_wr.iterrows():
        rank = list(sorted_by_wr.index).index(idx) + 1
        print(f"   {rank}. {row['Timeframe']}: {row['Win Rate %']:.2f}%")
    
    print(f"\n3. SHARPE RATIO RANKING (Risk-Adjusted Returns):")
    sorted_by_sharpe = comparison_df.sort_values('Sharpe Ratio', ascending=False)
    for idx, row in sorted_by_sharpe.iterrows():
        rank = list(sorted_by_sharpe.index).index(idx) + 1
        print(f"   {rank}. {row['Timeframe']}: {row['Sharpe Ratio']:.2f}")
    
    print(f"\n4. TRADE FREQUENCY:")
    for _, row in comparison_df.iterrows():
        print(f"   {row['Timeframe']}: {int(row['Trades'])} trades")
    
    # 30-minute specific analysis
    pnl_15min = comparison_df[comparison_df['Timeframe'] == '15-Minute']['Total P&L'].values[0]
    pnl_30min = comparison_df[comparison_df['Timeframe'] == '30-Minute']['Total P&L'].values[0]
    pnl_1hour = comparison_df[comparison_df['Timeframe'] == '1-Hour']['Total P&L'].values[0]
    
    print(f"\n5. 30-MINUTE ANALYSIS:")
    print(f"   15-Minute: ${pnl_15min:.2f}")
    print(f"   30-Minute: ${pnl_30min:.2f}")
    print(f"   1-Hour: ${pnl_1hour:.2f}")
    
    if pnl_30min > pnl_15min and pnl_30min > pnl_1hour:
        print(f"   → 30-Minute is OPTIMAL! ✅✅ (Goldilocks timeframe)")
    elif pnl_30min > pnl_15min or pnl_30min > pnl_1hour:
        print(f"   → 30-Minute is better than one other timeframe")
    else:
        print(f"   → 30-Minute is NOT optimal")
    
    # Success criteria for 30-minute
    wr_30min = comparison_df[comparison_df['Timeframe'] == '30-Minute']['Win Rate %'].values[0]
    sharpe_30min = comparison_df[comparison_df['Timeframe'] == '30-Minute']['Sharpe Ratio'].values[0]
    
    print(f"\n6. SUCCESS CRITERIA EVALUATION (30-Minute):")
    print(f"   Total P&L > $2.11: ${pnl_30min:.2f} {'✅' if pnl_30min > 2.11 else '❌'}")
    print(f"   Win Rate > 46%: {wr_30min:.2f}% {'✅' if wr_30min > 46 else '❌'}")
    print(f"   Sharpe Ratio > 2.05: {sharpe_30min:.2f} {'✅' if sharpe_30min > 2.05 else '❌'}")
    
    print("\n" + "=" * 90)
    print("RECOMMENDATION")
    print("=" * 90)
    
    best_timeframe = comparison_df.loc[comparison_df['Total P&L'].idxmax(), 'Timeframe']
    best_pnl = comparison_df['Total P&L'].max()
    best_sharpe = comparison_df.loc[comparison_df['Sharpe Ratio'].idxmax(), 'Timeframe']
    
    print(f"Best Profitability: {best_timeframe} (${best_pnl:.2f})")
    print(f"Best Risk-Adjusted: {best_sharpe} (Sharpe {comparison_df.loc[comparison_df['Sharpe Ratio'].idxmax(), 'Sharpe Ratio']:.2f})")
    
    if best_timeframe == '30-Minute':
        print(f"\n✅ RECOMMENDATION: Use 30-Minute timeframe (Goldilocks zone)")
        print(f"   - Best profitability")
        print(f"   - Optimal balance between signal quality and frequency")
    elif best_sharpe == '30-Minute':
        print(f"\n✅ RECOMMENDATION: Use 30-Minute timeframe (best risk-adjusted)")
    else:
        print(f"\n✅ RECOMMENDATION: Use {best_timeframe} timeframe")
    
    # Save comparison
    comparison_df.to_csv('results/quant_analysis/timeframe_comparison_3way.csv', index=False)
    print(f"\nComparison saved to: results/quant_analysis/timeframe_comparison_3way.csv")
    print("=" * 90)


if __name__ == "__main__":
    main()























