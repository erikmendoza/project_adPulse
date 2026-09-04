import json
import os
import shutil
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCE_DIR = Path(os.environ["DOWNLOADS_SOURCE_DIR"])
SOURCE_PATH = SOURCE_DIR / "meta_ads.json"
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "json_daily" / "meta_ads.json"

shutil.copy(SOURCE_PATH, RAW_PATH)

with open(RAW_PATH) as f:
    data = json.load(f)

records = data["data"]

print(f"rows: {len(records)}")

df = pd.DataFrame(records)

print(df.dtypes)
