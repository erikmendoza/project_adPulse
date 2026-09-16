import json
import os
import shutil
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from src.utils.paths import get_data_dir, get_project_root

load_dotenv()

PROJECT_ROOT = get_project_root()

SOURCE_DIR = Path(os.environ["DOWNLOADS_SOURCE_DIR"])
SOURCE_PATH = SOURCE_DIR / "meta_ads.json"
RAW_PATH = get_data_dir("raw") / "json_daily" / "meta_ads.json"

shutil.copy(SOURCE_PATH, RAW_PATH)

with open(RAW_PATH) as f:
    data = json.load(f)

records = data["data"]

print(f"rows: {len(records)}")

df = pd.DataFrame(records)

print(df.dtypes)
