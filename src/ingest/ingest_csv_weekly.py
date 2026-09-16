import shutil

import pandas as pd

from src.utils.paths import get_data_dir, get_project_root, get_source_dir

PROJECT_ROOT = get_project_root()

SOURCE_DIR = get_source_dir()
SOURCE_PATH = SOURCE_DIR / "email_campaigns.csv"
RAW_PATH = get_data_dir("raw") / "csv_weekly" / "email_campaigns.csv"

shutil.copy(SOURCE_PATH, RAW_PATH)

df_email = pd.read_csv(RAW_PATH)

print(f"rows: {len(df_email)} columns: {len(df_email.columns)}")

print(df_email.dtypes)
