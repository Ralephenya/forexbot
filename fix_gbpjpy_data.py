"""Fix GBP/JPY data format from yfinance"""
import pandas as pd

# Read the CSV - skip first 2 rows (metadata)
df = pd.read_csv('data/gbpjpy_15min.csv', skiprows=2)

# The actual column names are in the original CSV, but we'll rename them
# Based on yfinance format: first col is datetime, then Close, High, Low, Open, Volume
df.columns = ['datetime', 'close', 'high', 'low', 'open', 'volume']

# Convert datetime (remove timezone string if present)
df['datetime'] = df['datetime'].astype(str).str.replace('+00:00', '').str.strip()
df['datetime'] = pd.to_datetime(df['datetime'], utc=True)

# Convert price columns to float
for col in ['open', 'high', 'low', 'close']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Drop rows with NaN
df = df.dropna().reset_index(drop=True)

# Reorder columns
df = df[['datetime', 'open', 'high', 'low', 'close']]

# Save
df.to_csv('data/gbpjpy_15min.csv', index=False)
print(f"Fixed! Saved {len(df)} rows")
print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")
print("\nSample:")
print(df.head())

