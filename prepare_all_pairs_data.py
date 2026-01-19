"""Prepare all pairs data for portfolio test"""
import pandas as pd
import os

# Check EUR/USD
eurusd_file = 'data/eurusd_15min_6months.csv'
if os.path.exists(eurusd_file):
    print(f"✅ EUR/USD: {len(pd.read_csv(eurusd_file))} candles")
else:
    print("❌ EUR/USD: Not found")

# Check GBP/USD
gbpusd_file = 'data/gbpusd_15min.csv'
if os.path.exists(gbpusd_file):
    df = pd.read_csv(gbpusd_file, nrows=10)
    print(f"\nGBP/USD file exists. Columns: {df.columns.tolist()}")
    print(f"Sample data:\n{df.head()}")
    
    # Check if it has datetime column or different structure
    if 'Datetime' in df.columns:
        df_full = pd.read_csv(gbpusd_file)
        df_full['datetime'] = pd.to_datetime(df_full['Datetime'], utc=True)
        df_6months = df_full[(df_full['datetime'] >= '2024-06-01') & (df_full['datetime'] <= '2024-12-31')]
        if len(df_6months) > 0:
            df_6months[['datetime', 'Open', 'High', 'Low', 'Close']].rename(columns={
                'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close'
            }).to_csv('data/gbpusd_15min_6months.csv', index=False)
            print(f"✅ GBP/USD: Prepared {len(df_6months)} candles")
        else:
            print("❌ GBP/USD: No data in June-Dec 2024 range")
    elif 'datetime' in df.columns:
        df_full = pd.read_csv(gbpusd_file)
        df_full['datetime'] = pd.to_datetime(df_full['datetime'], utc=True)
        df_6months = df_full[(df_full['datetime'] >= '2024-06-01') & (df_full['datetime'] <= '2024-12-31')]
        if len(df_6months) > 0:
            df_6months.to_csv('data/gbpusd_15min_6months.csv', index=False)
            print(f"✅ GBP/USD: Prepared {len(df_6months)} candles")
        else:
            print("❌ GBP/USD: No data in June-Dec 2024 range")
    else:
        print(f"❌ GBP/USD: Unexpected column structure: {df.columns.tolist()}")
else:
    print("❌ GBP/USD: File not found")

print("\nNote: USD/JPY data needs to be downloaded from HistData.com")























