from pathlib import Path

import pandas as pd

from src.utils.cleaning import (
    coerce_datetime,
    coerce_numeric,
    drop_exact_duplicates,
    filter_future_dates,
    strip_whitespace,
)
from src.utils.logging_config import get_logger
from src.utils.paths import get_data_dir


def run():

    logger = get_logger(Path(__file__).stem)

    RAW_PATH = get_data_dir("raw") / "csv_daily" / "google_ads_weekly.csv"
    SILVER_PATH = get_data_dir("silver")

    dtype = {"campaign_name": "string"}
    df = pd.read_csv(RAW_PATH, dtype=dtype)

    df, invalid = coerce_datetime(df, "date", format="%Y-%m-%d")
    if invalid > 0:
        logger.warning(f"{invalid} invalid values in date converted to null")

    numeric_cols = ["impressions", "clicks", "conversions"]
    for col in numeric_cols:
        df, invalid = coerce_numeric(df, col, dtype="Int64")
        if invalid > 0:
            logger.warning(f"{invalid} invalid values in {col} converted to null")

    decimal_cols = ["cost_eur"]
    for col in decimal_cols:
        df, invalid = coerce_numeric(df, col, dtype="float64")
        if invalid > 0:
            logger.warning(f"{invalid} invalid values in {col} converted to null")

    df, invalid = coerce_numeric(df, "cost_eur", dtype="float64")
    if invalid > 0:
        logger.warning(f"{invalid} invalid values in cost_eur converted to null")

    df = strip_whitespace(df, ["campaign_name"])

    df, removed = drop_exact_duplicates(df)
    if removed > 0:
        logger.info(f"Removed {removed} exact duplicate rows")

    df, removed = filter_future_dates(df, "date")
    if removed > 0:
        logger.info(f"Removed {removed} rows with future date")

    SILVER_PATH.mkdir(parents=True, exist_ok=True)
    df.to_parquet(SILVER_PATH / "google_ads.parquet", index=False)

    logger.info(f"rows: {len(df)} columns: {len(df.columns)}")


if __name__ == "__main__":
    run()
