"""
Comprehensive Portfolio Analysis
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
    """Comprehensive portfolio analysis"""
    logger.info("=" * 70)
    logger.info("COMPREHENSIVE PORTFOLIO ANALYSIS")
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
    
    print("\n" + "=" * 90)
    print("1. INDIVIDUAL PAIR PERFORMANCE")
    print("=" * 90)
    
    pair_stats = []
    for pair in portfolio_df['pair'].unique():
        pair_df = portfolio_df[portfolio_df['pair'] == pair]
        total_trades = len(pair_df)
        win_rate = (pair_df['pnl'] > 0).sum() / total_trades * 100 if total_trades > 0 else 0
        total_pnl = pair_df['pnl'].sum()
        avg_pips = pair_df['pips'].mean()
        
        daily_pnl = pair_df.groupby(pair_df['exit_time'].dt.date)['pnl'].sum()
        cumulative = daily_pnl.cumsum()
        running_max = cumulative.cummax()
        drawdown = cumulative - running_max
        max_drawdown = drawdown.min()
        
        pair_stats.append({
            'Pair': pair.upper(),
            'Trades': total_trades,
            'Win Rate %': win_rate,
            'Total P&L': total_pnl,
            'Avg Pips': avg_pips,
            'Max Drawdown': max_drawdown
        })
    
    pair_df_table = pd.DataFrame(pair_stats)
    print(pair_df_table.to_string(index=False))
    
    # Portfolio totals
    total_trades = len(portfolio_df)
    win_rate = (portfolio_df['pnl'] > 0).sum() / total_trades * 100 if total_trades > 0 else 0
    total_pnl = portfolio_df['pnl'].sum()
    avg_pips = portfolio_df['pips'].mean()
    
    daily_pnl = portfolio_df.groupby(portfolio_df['exit_time'].dt.date)['pnl'].sum()
    cumulative = daily_pnl.cumsum()
    running_max = cumulative.cummax()
    drawdown = cumulative - running_max
    max_drawdown = drawdown.min()
    
    print("\n" + "=" * 90)
    print("2. TOTAL PORTFOLIO PERFORMANCE")
    print("=" * 90)
    print(f"Total Trades: {total_trades}")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Total P&L: ${total_pnl:.2f}")
    print(f"Average Pips: {avg_pips:.2f}")
    print(f"Max Drawdown: ${max_drawdown:.2f}")
    
    # Monthly breakdown
    portfolio_df['month'] = portfolio_df['exit_time'].dt.to_period('M')
    monthly = portfolio_df.groupby('month').agg({
        'pnl': ['sum', 'count']
    })
    monthly.columns = ['Total P&L', 'Trades']
    monthly['Win Rate %'] = portfolio_df.groupby('month').apply(
        lambda x: (x['pnl'] > 0).sum() / len(x) * 100 if len(x) > 0 else 0
    ).values
    
    print("\n" + "=" * 90)
    print("3. MONTHLY PORTFOLIO PERFORMANCE")
    print("=" * 90)
    print(monthly.to_string())
    
    # Comparison
    eurusd_pnl = eurusd_df['pnl'].sum()
    eurusd_wr = (eurusd_df['pnl'] > 0).sum() / len(eurusd_df) * 100
    
    print("\n" + "=" * 90)
    print("4. PORTFOLIO vs EUR/USD SINGLE-PAIR")
    print("=" * 90)
    print(f"EUR/USD Single: ${eurusd_pnl:.2f} ({eurusd_wr:.2f}% win rate, {len(eurusd_df)} trades)")
    print(f"Portfolio: ${total_pnl:.2f} ({win_rate:.2f}% win rate, {total_trades} trades)")
    improvement = total_pnl - eurusd_pnl
    improvement_pct = (improvement / abs(eurusd_pnl)) * 100 if eurusd_pnl != 0 else 0
    print(f"Difference: ${improvement:.2f} ({improvement_pct:+.1f}%)")
    
    # Correlation analysis (do pairs trade at same times?)
    portfolio_df['entry_date'] = portfolio_df['entry_time'].dt.date
    pair_correlations = []
    pairs = portfolio_df['pair'].unique()
    for i, pair1 in enumerate(pairs):
        for pair2 in pairs[i+1:]:
            pair1_dates = set(portfolio_df[portfolio_df['pair'] == pair1]['entry_date'])
            pair2_dates = set(portfolio_df[portfolio_df['pair'] == pair2]['entry_date'])
            common_dates = pair1_dates.intersection(pair2_dates)
            correlation = len(common_dates) / max(len(pair1_dates), len(pair2_dates)) * 100 if max(len(pair1_dates), len(pair2_dates)) > 0 else 0
            pair_correlations.append({
                'Pair 1': pair1.upper(),
                'Pair 2': pair2.upper(),
                'Common Trade Days': len(common_dates),
                'Correlation %': correlation
            })
    
    if pair_correlations:
        print("\n" + "=" * 90)
        print("5. PAIR CORRELATION (Trading Day Overlap)")
        print("=" * 90)
        corr_df = pd.DataFrame(pair_correlations)
        print(corr_df.to_string(index=False))
    
    # Success criteria
    print("\n" + "=" * 90)
    print("6. SUCCESS CRITERIA EVALUATION")
    print("=" * 90)
    print(f"Portfolio P&L > $4: ${total_pnl:.2f} {'✅' if total_pnl > 4 else '❌'}")
    print(f"Win Rate > 45%: {win_rate:.2f}% {'✅' if win_rate > 45 else '❌'}")
    print(f"Max Drawdown < $10: ${abs(max_drawdown):.2f} {'✅' if abs(max_drawdown) < 10 else '❌'}")
    print(f"Diversification benefit: {'✅ YES' if total_pnl > eurusd_pnl else '❌ NO'}")
    
    print("\n" + "=" * 90)
    print("ANALYSIS COMPLETE")
    print("=" * 90)


if __name__ == "__main__":
    main()























