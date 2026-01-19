"""Quick script to display backtest results"""
import pandas as pd

df = pd.read_csv('results/backtest_results_6months.csv')
df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True)
df['month'] = df['exit_time'].dt.to_period('M')

# Monthly breakdown
monthly = df.groupby('month').agg({
    'pnl': ['sum', 'count'],
    'pips': 'mean'
})
monthly.columns = ['Total P&L', 'Trades', 'Avg Pips']
monthly['Win Rate %'] = df.groupby('month').apply(lambda x: (x['pnl'] > 0).sum() / len(x) * 100).values

print("\n" + "=" * 70)
print("6-MONTH RSI STRATEGY BACKTEST - MONTHLY BREAKDOWN")
print("=" * 70)
print(monthly.to_string())
print("\n" + "=" * 70)
print(f"OVERALL RESULTS:")
print(f"  Total Trades: {len(df)}")
print(f"  Win Rate: {(df['pnl'] > 0).sum() / len(df) * 100:.2f}%")
print(f"  Total P&L: ${df['pnl'].sum():.2f}")
print(f"  Average Pips per Trade: {df['pips'].mean():.2f}")
print("=" * 70 + "\n")























