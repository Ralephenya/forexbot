"""
Compare Strategy B WITH vs WITHOUT news filter
"""

import pandas as pd
import numpy as np
import logging
from news_filter import get_major_news_events_2024, print_news_events

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
    """Compare WITH vs WITHOUT news filter"""
    logger.info("=" * 70)
    logger.info("NEWS FILTER COMPARISON: WITH vs WITHOUT")
    logger.info("=" * 70)
    
    # Print news events calendar
    print_news_events()
    
    # Load results
    results_with_filter = pd.read_csv('results/backtest_results_strategy_b_with_news_filter.csv')
    results_without_filter = pd.read_csv('results/backtest_results_strategy_b_no_news_filter.csv')
    
    # Convert datetime columns
    for df in [results_with_filter, results_without_filter]:
        df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True)
        df['entry_time'] = pd.to_datetime(df['entry_time'], utc=True)
    
    # Calculate metrics for both
    comparison_data = []
    
    for name, df in [('WITHOUT News Filter', results_without_filter), ('WITH News Filter', results_with_filter)]:
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
        
        comparison_data.append({
            'Version': name,
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
    print("STRATEGY B: WITH vs WITHOUT NEWS FILTER COMPARISON")
    print("=" * 90)
    print(comparison_df.to_string(index=False))
    
    # Calculate differences
    pnl_without = comparison_df[comparison_df['Version'] == 'WITHOUT News Filter']['Total P&L'].values[0]
    pnl_with = comparison_df[comparison_df['Version'] == 'WITH News Filter']['Total P&L'].values[0]
    wr_without = comparison_df[comparison_df['Version'] == 'WITHOUT News Filter']['Win Rate %'].values[0]
    wr_with = comparison_df[comparison_df['Version'] == 'WITH News Filter']['Win Rate %'].values[0]
    dd_without = comparison_df[comparison_df['Version'] == 'WITHOUT News Filter']['Max Drawdown'].values[0]
    dd_with = comparison_df[comparison_df['Version'] == 'WITH News Filter']['Max Drawdown'].values[0]
    trades_without = comparison_df[comparison_df['Version'] == 'WITHOUT News Filter']['Trades'].values[0]
    trades_with = comparison_df[comparison_df['Version'] == 'WITH News Filter']['Trades'].values[0]
    
    print("\n" + "=" * 90)
    print("KEY FINDINGS")
    print("=" * 90)
    
    print(f"\n1. PROFITABILITY:")
    print(f"   WITHOUT News Filter: ${pnl_without:.2f}")
    print(f"   WITH News Filter: ${pnl_with:.2f}")
    difference = pnl_with - pnl_without
    difference_pct = (difference / abs(pnl_without)) * 100 if pnl_without != 0 else 0
    print(f"   Difference: ${difference:+.2f} ({difference_pct:+.1f}%)")
    if pnl_with > pnl_without:
        print(f"   → News filter IMPROVED profitability ✅")
    elif pnl_with < pnl_without:
        print(f"   → News filter REDUCED profitability ❌")
    else:
        print(f"   → News filter had NO effect on profitability")
    
    print(f"\n2. WIN RATE:")
    print(f"   WITHOUT News Filter: {wr_without:.2f}%")
    print(f"   WITH News Filter: {wr_with:.2f}%")
    wr_diff = wr_with - wr_without
    print(f"   Difference: {wr_diff:+.2f}%")
    if wr_with > wr_without:
        print(f"   → News filter IMPROVED win rate ✅")
    elif wr_with < wr_without:
        print(f"   → News filter REDUCED win rate ❌")
    else:
        print(f"   → News filter had NO effect on win rate")
    
    print(f"\n3. MAX DRAWDOWN:")
    print(f"   WITHOUT News Filter: ${dd_without:.2f}")
    print(f"   WITH News Filter: ${dd_with:.2f}")
    dd_diff = abs(dd_with) - abs(dd_without)
    print(f"   Difference: ${dd_diff:+.2f} (lower is better)")
    if abs(dd_with) < abs(dd_without):
        print(f"   → News filter REDUCED drawdown ✅")
    elif abs(dd_with) > abs(dd_without):
        print(f"   → News filter INCREASED drawdown ❌")
    else:
        print(f"   → News filter had NO effect on drawdown")
    
    print(f"\n4. TRADE FREQUENCY:")
    print(f"   WITHOUT News Filter: {trades_without} trades")
    print(f"   WITH News Filter: {trades_with} trades")
    trades_diff = trades_with - trades_without
    print(f"   Difference: {trades_diff:+d} trades ({trades_diff/abs(trades_without)*100:+.1f}%)")
    
    # Success criteria evaluation
    print("\n" + "=" * 90)
    print("SUCCESS CRITERIA EVALUATION")
    print("=" * 90)
    
    print(f"Win Rate > 47%: {wr_with:.2f}% {'✅' if wr_with > 47 else '❌'}")
    print(f"Total P&L > $2.00: ${pnl_with:.2f} {'✅' if pnl_with > 2.00 else '❌'}")
    print(f"Lower drawdown: ${abs(dd_with):.2f} vs ${abs(dd_without):.2f} {'✅' if abs(dd_with) < abs(dd_without) else '❌'}")
    
    # Overall assessment
    print("\n" + "=" * 90)
    print("OVERALL ASSESSMENT")
    print("=" * 90)
    
    improvements = 0
    if pnl_with > pnl_without:
        improvements += 1
    if wr_with > wr_without:
        improvements += 1
    if abs(dd_with) < abs(dd_without):
        improvements += 1
    
    if improvements >= 2:
        print("✅ RECOMMENDATION: USE NEWS FILTER")
        print("   News filter improves performance on multiple metrics")
    elif improvements == 1:
        print("⚠️ RECOMMENDATION: NEWS FILTER MIXED RESULTS")
        print("   News filter improves some metrics but not others")
    else:
        print("❌ RECOMMENDATION: DO NOT USE NEWS FILTER")
        print("   News filter does not improve performance")
    
    # Save comparison
    comparison_df.to_csv('results/quant_analysis/news_filter_comparison.csv', index=False)
    print(f"\nComparison saved to: results/quant_analysis/news_filter_comparison.csv")
    print("=" * 90)


if __name__ == "__main__":
    main()























