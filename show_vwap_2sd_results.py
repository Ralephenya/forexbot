"""Display VWAP 2.0 SD optimized results"""
import pandas as pd

df = pd.read_csv('results/backtest_results_6months_vwap_2sd.csv')
df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True)
df['month'] = df['exit_time'].dt.to_period('M')

# Exit reason breakdown
print("\n" + "=" * 70)
print("VWAP 2.0 SD STRATEGY - EXIT REASON BREAKDOWN")
print("=" * 70)
exit_reasons = df.groupby('exit_reason').agg({
    'pnl': ['count', 'sum', 'mean']
})
exit_reasons.columns = ['Count', 'Total P&L', 'Avg P&L']
print(exit_reasons.to_string())

# Monthly breakdown
monthly = df.groupby('month').agg({
    'pnl': ['sum', 'count'],
    'pips': 'mean'
})
monthly.columns = ['Total P&L', 'Trades', 'Avg Pips']
monthly['Win Rate %'] = df.groupby('month').apply(lambda x: (x['pnl'] > 0).sum() / len(x) * 100).values

print("\n" + "=" * 70)
print("VWAP 2.0 SD STRATEGY - MONTHLY BREAKDOWN")
print("=" * 70)
print(monthly.to_string())

print("\n" + "=" * 70)
print("OVERALL RESULTS (2.0 SD OPTIMIZED):")
print("=" * 70)
print(f"  Total Trades: {len(df)}")
print(f"  Win Rate: {(df['pnl'] > 0).sum() / len(df) * 100:.2f}%")
print(f"  Total P&L: ${df['pnl'].sum():.2f}")
print(f"  Average Pips per Trade: {df['pips'].mean():.2f}")
daily_pnl = df.groupby(df['exit_time'].dt.date)['pnl'].sum()
cumulative = daily_pnl.cumsum()
running_max = cumulative.cummax()
drawdown = cumulative - running_max
print(f"  Max Drawdown: ${drawdown.min():.2f}")
print("=" * 70 + "\n")























