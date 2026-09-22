from pathlib import Path

import pandas as pd

from src.utils.logging_config import get_logger
from src.utils.paths import get_data_dir

logger = get_logger(Path(__file__).stem)

MAPPING_PATH = get_data_dir("silver") / "campaign_mapping.parquet"
SILVER_PATH = get_data_dir("silver")
GOLD_PATH = get_data_dir("gold")

TARGET_COLUMNS = [
    "date",
    "source",
    "original_campaign_name",
    "impressions",
    "clicks",
    "conversions",
    "spend_eur",
    "revenue_eur",
]


def standardize_source(df, source, rename_map, defaults=None):
    df = df.rename(columns=rename_map)
    df["source"] = source
    if defaults:
        for col, value in defaults.items():
            df[col] = value
    return df[TARGET_COLUMNS]


mapping_long = pd.read_parquet(MAPPING_PATH)

google = pd.read_parquet(SILVER_PATH / "google_ads.parquet")

google = standardize_source(
    google,
    source="google",
    rename_map={"campaign_name": "original_campaign_name", "cost_eur": "spend_eur"},
    defaults={"revenue_eur": 0.0},
)
logger.info(f"Google rows: {len(google)}")

meta = pd.read_parquet(SILVER_PATH / "meta_ads.parquet")
meta = standardize_source(
    meta,
    source="meta",
    rename_map={
        "campaign_name": "original_campaign_name",
        "date_start": "date",
        "spend": "spend_eur",
        "purchase": "conversions",  # Only action representing an actual conversion
    },
    defaults={"revenue_eur": 0.0},
)
logger.info(f"Meta rows: {len(meta)}")

email = pd.read_parquet(SILVER_PATH / "email_campaigns.parquet")
email = standardize_source(
    email,
    source="email",
    rename_map={
        "campaign_name": "original_campaign_name",
        "week_start": "date",
        "total_cost": "spend_eur",
        "converted": "conversions",
        "clicked": "clicks",
    },
    defaults={"impressions": 0},
)
logger.info(f"Email rows: {len(email)}")

facts = pd.concat([google, meta, email], ignore_index=True)
logger.info(f"Fact rows: {len(facts)}")

unified = facts.merge(
    mapping_long,
    on=["source", "original_campaign_name"],
    how="left",
)
logger.info(f"Unified rows: {len(unified)}")

unified["is_mapped"] = unified["campaign_group"].notna()

for source in unified["source"].unique():
    sub = unified[unified["source"] == source]
    total_spend = sub["spend_eur"].sum()
    mapped_spend = sub.loc[sub["is_mapped"], "spend_eur"].sum()
    logger.info(f"{source} total spend: {total_spend} mapped spend: {mapped_spend}")
    pct = mapped_spend / total_spend * 100 if total_spend else 0
    logger.info(f"{source} mapped spend:{pct:.2f}%")

unmapped = unified.loc[~unified["is_mapped"], "original_campaign_name"].unique()
if len(unmapped) > 0:
    logger.warning(f"{len(unmapped)} unmapped campaigns: {list(unmapped)}")

unified["loaded_at"] = pd.Timestamp.now()

unified = unified[
    [
        "date",
        "source",
        "campaign_group",
        "original_campaign_name",
        "product_category",
        "impressions",
        "clicks",
        "conversions",
        "spend_eur",
        "revenue_eur",
        "is_mapped",
        "loaded_at",
    ]
]

count_cols = [
    "impressions",
    "clicks",
    "conversions",
]
unified[count_cols] = unified[count_cols].astype("Int64")

duplicated = unified.duplicated(subset=["date", "source", "original_campaign_name"])
logger.info(f"Unified rows duplicated: {duplicated.sum()}")

assert duplicated.sum() == 0, "Duplicated rows found in unified_campaigns table"

GOLD_PATH.mkdir(parents=True, exist_ok=True)
unified.to_parquet(GOLD_PATH / "unified_campaigns.parquet")

logger.info(f"saved {len(unified)} rows to {GOLD_PATH / 'unified_campaigns.parquet'}")
