"""
Compare Portfolio vs Single-Pair Performance
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
    """Compare portfolio to single pair"""
    logger.info("=" * 70)
    logger.info("PORTFOLIO vs SINGLE-PAIR COMPARISON")
    logger.info("=" * 70)
    
    # Load portfolio results
    portfolio_file = 'results/backtest_results_portfolio_strategy_b.csv'
    eurusd_file = 'results/backtest_results_b_regimeswitching.csv'
    
    try:
        portfolio_df = pd.read_csv(portfolio_file)
        portfolio_df['exit_time'] = pd.to_datetime(portfolio_df['exit_time'], utc=True)
        portfolio_df['entry_time'] = pd.to_datetime(portfolio_df['entry_time'], utc=True)
    except FileNotFoundError:
        logger.error(f"Portfolio results not found: {portfolio_file}")
        return
    
    try:
        eurusd_df = pd.read_csv(eurusd_file)
        eurusd_df['exit_time'] = pd.to_datetime(eurusd_df['exit_time'], utc=True)
        eurusd_df['entry_time'] = pd.to_datetime(eurusd_df['entry_time'], utc=True)
    except FileNotFoundError:
        logger.error(f"EUR/USD results not found: {eurusd_file}")
        return
    
    # Calculate metrics
    comparison_data = []
    
    for name, df in [('EUR/USD Single', eurusd_df), ('Portfolio', portfolio_df)]:
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
            'Strategy': name,
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
    print("PORTFOLIO vs SINGLE-PAIR COMPARISON")
    print("=" * 90)
    print(comparison_df.to_string(index=False))
    
    # Calculate improvement
    single_pnl = comparison_df[comparison_df['Strategy'] == 'EUR/USD Single']['Total P&L'].values[0]
    portfolio_pnl = comparison_df[comparison_df['Strategy'] == 'EUR/USD Single']['Total P&L'].values[0] if len(comparison_df[comparison_df['Strategy'] == 'Portfolio']) == 0 else comparison_df[comparison_df['Strategy'] == 'Portfolio']['Total P&L'].values[0]
    
    improvement = portfolio_pnl - single_pnl
    improvement_pct = (improvement / abs(single_pnl)) * 100 if single_pnl != 0 else 0
    
    print("\n" + "=" * 90)
    print("KEY FINDINGS")
    print("=" * 90)
    print(f"\n1. PROFITABILITY:")
    print(f"   EUR/USD Single: ${single_pnl:.2f}")
    print(f"   Portfolio: ${portfolio_pnl:.2f}")
    print(f"   Difference: ${improvement:.2f} ({improvement_pct:+.1f}%)")
    
    # Per-pair breakdown
    if 'pair' in portfolio_df.columns:
        print(f"\n2. PER-PAIR BREAKDOWN:")
        for pair in portfolio_df['pair'].unique():
            pair_df = portfolio_df[portfolio_df['pair'] == pair]
            pair_pnl = pair_df['pnl'].sum()
            pair_wr = (pair_df['pnl'] > 0).sum() / len(pair_df) * 100 if len(pair_df) > 0 else 0
            print(f"   {pair.upper()}: ${pair_pnl:.2f} ({pair_wr:.1f}% win rate, {len(pair_df)} trades)")
    
    print("\n" + "=" * 90)
    print("SUCCESS CRITERIA EVALUATION")
    print("=" * 90)
    print(f"Portfolio P&L > $4: ${portfolio_pnl:.2f} {'✅' if portfolio_pnl > 4 else '❌'}")
    portfolio_wr = comparison_df[comparison_df['Strategy'] == 'Portfolio']['Win Rate %'].values[0] if len(comparison_df[comparison_df['Strategy'] == 'Portfolio']) > 0 else 0
    print(f"Win Rate > 45%: {portfolio_wr:.2f}% {'✅' if portfolio_wr > 45 else '❌'}")
    print(f"Diversification benefit: {'✅ YES' if portfolio_pnl > single_pnl else '❌ NO'}")
    print("=" * 90)
    
    # Save comparison
    comparison_df.to_csv('results/quant_analysis/portfolio_vs_single_comparison.csv', index=False)
    print(f"\nComparison saved to: results/quant_analysis/portfolio_vs_single_comparison.csv")


if __name__ == "__main__":
    main()























