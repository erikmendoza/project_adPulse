from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_PATH = PROJECT_ROOT / "data" / "raw" / "csv_daily" / "google_ads_weekly.csv"
SILVER_PATH = PROJECT_ROOT / "data" / "silver"

df = pd.read_csv(RAW_PATH)
df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
df.to_parquet(SILVER_PATH / "google_ads.parquet")
print(f"rows: {len(df)} columns: {len(df.columns)}")
print(df.dtypes)
print(df.head(5))
