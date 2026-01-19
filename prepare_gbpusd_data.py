"""Prepare GBP/USD data for portfolio test"""
import pandas as pd

df = pd.read_csv('data/gbpusd_15min.csv')
df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
print(f"Original: {len(df)} candles")
print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")

# Filter to June-December 2024
df_filtered = df[(df['datetime'] >= '2024-06-01') & (df['datetime'] <= '2024-12-31')].copy()
print(f"Filtered: {len(df_filtered)} candles (June-Dec 2024)")

if len(df_filtered) > 0:
    df_filtered.to_csv('data/gbpusd_15min_6months.csv', index=False)
    print("Saved to data/gbpusd_15min_6months.csv")
else:
    print("No data in range!")























