"""Compare Hybrid Strategy vs Standalone Strategies"""
import pandas as pd

# Load hybrid results
hybrid_df = pd.read_csv('results/backtest_results_6months_hybrid.csv')
hybrid_df['exit_time'] = pd.to_datetime(hybrid_df['exit_time'], utc=True)

# Load standalone results for comparison
rsi_df = pd.read_csv('results/backtest_results_6months.csv')
rsi_df['exit_time'] = pd.to_datetime(rsi_df['exit_time'], utc=True)

vwap_df = pd.read_csv('results/backtest_results_6months_vwap_2sd.csv')
vwap_df['exit_time'] = pd.to_datetime(vwap_df['exit_time'], utc=True)

print("\n" + "=" * 70)
print("HYBRID STRATEGY COMPARISON")
print("=" * 70)
print()

# Calculate metrics for each
strategies = {
    'RSI Standalone': rsi_df,
    'VWAP 2.0 SD Standalone': vwap_df,
    'VWAP + RSI Hybrid': hybrid_df
}

comparison_data = []
for name, df in strategies.items():
    total_trades = len(df)
    win_rate = (df['pnl'] > 0).sum() / total_trades * 100 if total_trades > 0 else 0
    total_pnl = df['pnl'].sum()
    avg_pips = df['pips'].mean()
    
    # Calculate drawdown
    daily_pnl = df.groupby(df['exit_time'].dt.date)['pnl'].sum()
    cumulative = daily_pnl.cumsum()
    running_max = cumulative.cummax()
    drawdown = cumulative - running_max
    max_dd = drawdown.min()
    
    comparison_data.append({
        'Strategy': name,
        'Trades': total_trades,
        'Win Rate %': win_rate,
        'Total P&L': total_pnl,
        'Avg Pips': avg_pips,
        'Max Drawdown': max_dd
    })

comparison_df = pd.DataFrame(comparison_data)
comparison_df = comparison_df.sort_values('Total P&L', ascending=False)

print("STRATEGY COMPARISON TABLE")
print("=" * 70)
print(f"{'Strategy':<30} {'Trades':<8} {'Win Rate':<10} {'Total P&L':<12} {'Avg Pips':<10} {'Drawdown':<12}")
print("-" * 70)
for _, row in comparison_df.iterrows():
    pnl_str = f"${row['Total P&L']:.2f}"
    pnl_mark = "✓" if row['Total P&L'] > 0 else "✗"
    print(f"{row['Strategy']:<30} {int(row['Trades']):<8} "
          f"{row['Win Rate %']:<10.2f}% {pnl_mark} {pnl_str:<10} "
          f"{row['Avg Pips']:<10.2f} ${row['Max Drawdown']:<11.2f}")

print()
print("=" * 70)
print("KEY INSIGHTS")
print("=" * 70)

hybrid_pnl = comparison_df[comparison_df['Strategy'] == 'VWAP + RSI Hybrid']['Total P&L'].values[0]
rsi_pnl = comparison_df[comparison_df['Strategy'] == 'RSI Standalone']['Total P&L'].values[0]
vwap_pnl = comparison_df[comparison_df['Strategy'] == 'VWAP 2.0 SD Standalone']['Total P&L'].values[0]

hybrid_trades = comparison_df[comparison_df['Strategy'] == 'VWAP + RSI Hybrid']['Trades'].values[0]
rsi_trades = comparison_df[comparison_df['Strategy'] == 'RSI Standalone']['Trades'].values[0]
vwap_trades = comparison_df[comparison_df['Strategy'] == 'VWAP 2.0 SD Standalone']['Trades'].values[0]

print(f"\n1. SIGNAL REDUCTION (Filtering Effect):")
print(f"   RSI Standalone: {int(rsi_trades)} trades")
print(f"   VWAP 2.0 SD: {int(vwap_trades)} trades")
print(f"   Hybrid: {int(hybrid_trades)} trades")
print(f"   Reduction: {int(vwap_trades)} → {int(hybrid_trades)} ({int((1 - hybrid_trades/vwap_trades) * 100)}% fewer)")

print(f"\n2. PROFITABILITY:")
if hybrid_pnl > rsi_pnl and hybrid_pnl > vwap_pnl:
    print(f"   Hybrid is MOST profitable (${hybrid_pnl:.2f})")
elif hybrid_pnl > rsi_pnl or hybrid_pnl > vwap_pnl:
    print(f"   Hybrid is better than one standalone (${hybrid_pnl:.2f})")
else:
    print(f"   Hybrid is less profitable (${hybrid_pnl:.2f})")

print(f"\n3. SIGNAL QUALITY:")
hybrid_wr = comparison_df[comparison_df['Strategy'] == 'VWAP + RSI Hybrid']['Win Rate %'].values[0]
rsi_wr = comparison_df[comparison_df['Strategy'] == 'RSI Standalone']['Win Rate %'].values[0]
vwap_wr = comparison_df[comparison_df['Strategy'] == 'VWAP 2.0 SD Standalone']['Win Rate %'].values[0]
print(f"   Hybrid Win Rate: {hybrid_wr:.2f}%")
print(f"   RSI Win Rate: {rsi_wr:.2f}%")
print(f"   VWAP Win Rate: {vwap_wr:.2f}%")
if hybrid_wr > rsi_wr and hybrid_wr > vwap_wr:
    print(f"   → Hybrid has HIGHEST win rate ✅")
elif hybrid_wr > rsi_wr or hybrid_wr > vwap_wr:
    print(f"   → Hybrid has better win rate than one standalone")
else:
    print(f"   → Hybrid win rate is lower (not improved)")

print("\n" + "=" * 70)























