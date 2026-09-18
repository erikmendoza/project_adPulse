import shutil
from pathlib import Path

import pandas as pd

from src.utils.logging_config import get_logger
from src.utils.paths import get_data_dir, get_project_root, get_source_dir

logger = get_logger(Path(__file__).stem)

PROJECT_ROOT = get_project_root()
FILENAME = "google_ads_weekly.csv"
SOURCE_DIR = get_source_dir()
SOURCE_PATH = SOURCE_DIR / "google_ads_weekly.csv"
RAW_DIR = get_data_dir("raw") / "csv_daily"
RAW_PATH = RAW_DIR / FILENAME

RAW_DIR.mkdir(parents=True, exist_ok=True)
shutil.copy(SOURCE_PATH, RAW_PATH)

df = pd.read_csv(RAW_PATH)

logger.info(f"rows: {len(df)} columns: {len(df.columns)}")
logger.info(df.dtypes)
