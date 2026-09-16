import pandas as pd

from src.utils.paths import get_data_dir, get_project_root

PROJECT_ROOT = get_project_root()

MAPPING_PATH = get_data_dir("raw") / "csv_mapping" / "campaign_mapping.csv"
GOLD_PATH = get_data_dir("gold")

mapping = pd.read_csv(MAPPING_PATH)

# print(mapping.head(5))

mapping = mapping.rename(
    columns={
        "google_name": "google",
        "meta_name": "meta",
        "email_name": "email",
    }
)

# print(mapping.head(5))

mapping_long = mapping.melt(
    id_vars=["campaign_group", "product_category"],
    value_vars=["google", "meta", "email"],
    value_name="original_campaign_name",
    var_name="source",
)

# print(mapping_long)

mapping_long = mapping_long.dropna(subset=["original_campaign_name"])

print(mapping_long)
# print(f"rows: {len(mapping_long)}")


SILVER_PATH = get_data_dir("silver")

google = pd.read_parquet(SILVER_PATH / "google_ads.parquet")

# print(google.head(5))
# print(f"rows: {len(google)}")

google = google.rename(
    columns={
        "cost_eur": "spend_eur",
        "campaign_name": "original_campaign_name",
    }
)

google["source"] = "google"
google["revenue_eur"] = 0.0

google = google[
    [
        "date",
        "source",
        "original_campaign_name",
        "impressions",
        "clicks",
        "conversions",
        "spend_eur",
        "revenue_eur",
    ]
]

print(google.head(5))

meta = pd.read_parquet(SILVER_PATH / "meta_ads.parquet")

# print(meta.head(5))
# print(f"rows: {len(meta)}")

meta = meta.rename(
    columns={
        "campaign_name": "original_campaign_name",
        "date_start": "date",
        "spend": "spend_eur",
        "purchase": "conversions",  # Only action representing an actual conversion
    }
)
meta["source"] = "meta"
meta["revenue_eur"] = 0.0

meta = meta[
    [
        "date",
        "source",
        "original_campaign_name",
        "impressions",
        "clicks",
        "conversions",
        "spend_eur",
        "revenue_eur",
    ]
]

print(meta.head(5))

email = pd.read_parquet(SILVER_PATH / "email_campaigns.parquet")

# print(email.head(5))
# print(f"rows: {len(email)}")

email = email.rename(
    columns={
        "campaign_name": "original_campaign_name",
        "week_start": "date",
        "total_cost": "spend_eur",
        "converted": "conversions",
        "clicked": "clicks",
    }
)
email["source"] = "email"
email["impressions"] = 0

email = email[
    [
        "date",
        "source",
        "original_campaign_name",
        "impressions",
        "clicks",
        "conversions",
        "spend_eur",
        "revenue_eur",
    ]
]

print(email.head(5))

facts = pd.concat([google, meta, email], ignore_index=True)

print(facts)
print(f"rows: {len(facts)}")

unified = facts.merge(
    mapping_long,
    on=["source", "original_campaign_name"],
    how="left",
)

print(unified)
print(f"rows: {len(unified)}")

unified["is_mapped"] = unified["campaign_group"].notna()

# print(unified)
# print(unified["is_mapped"].value_counts())

unified["loaded_at"] = pd.Timestamp.now()

# print(unified[["date", "source", "loaded_at"]].head())

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

print(unified.head())
print(unified.dtypes)

duplicated = unified.duplicated(subset=["date", "source", "original_campaign_name"])
print(f"duplicated: {duplicated.sum()}")

assert duplicated.sum() == 0, "Duplicated rows found in unified_campaigns table"

unified.to_parquet(GOLD_PATH / "unified_campaigns.parquet")

print(f"saved {len(unified)} rows to {GOLD_PATH / 'unified_campaigns.parquet'}")
