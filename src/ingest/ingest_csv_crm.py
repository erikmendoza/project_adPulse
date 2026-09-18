import shutil

import pandas as pd

from src.utils.paths import get_data_dir, get_project_root, get_source_dir

PROJECT_ROOT = get_project_root()
FILENAME = "crm_sales.csv"
SOURCE_DIR = get_source_dir()
SOURCE_PATH = SOURCE_DIR / "crm_ventas.csv"
RAW_PATH = get_data_dir("raw") / "csv_crm" / FILENAME
RAW_DIR = get_data_dir("raw") / "csv_crm"
RAW_DIR.mkdir(parents=True, exist_ok=True)

shutil.copy(SOURCE_PATH, RAW_PATH)

df = pd.read_csv(RAW_PATH)

print(f"rows: {len(df)} columns: {len(df.columns)}")
print(df.dtypes)
