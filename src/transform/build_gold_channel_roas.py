from pathlib import Path

import pandas as pd

from src.utils.logging_config import get_logger
from src.utils.paths import get_data_dir

logger = get_logger(Path(__file__).stem)

SILVER_PATH = get_data_dir("silver")
GOLD_PATH = get_data_dir("gold")

LTV_MUlTIPLIER = 2.3


def get_reconciliation_factor(
    crm_total_conversions: int, total_reported_conversions: int
) -> float:
    return crm_total_conversions / total_reported_conversions


def get_reconciled_conversions(
    conversions_by_source: pd.Series, reconciliation_factor: float
) -> pd.Series:
    return conversions_by_source * reconciliation_factor


def get_average_order_value(crm: pd.DataFrame) -> float:
    return crm["amount_eur"].mean()


def get_ltv_order_value(average_order_value: float, LTV_MUlTIPLIER: float) -> float:
    return average_order_value * LTV_MUlTIPLIER


def compute_revenue(conversions: pd.Series, average_order_value: float) -> pd.Series:
    return conversions * average_order_value


def compute_roas(reconciled_revenue: pd.Series, spend_by_source: pd.Series) -> pd.Series:
    return reconciled_revenue / spend_by_source


unified = pd.read_parquet(GOLD_PATH / "unified_campaigns.parquet")
crm = pd.read_parquet(SILVER_PATH / "crm_sales.parquet")

crm_total_conversions = len(crm)
total_reported_conversions = unified["conversions"].sum()
reconciliation_factor = get_reconciliation_factor(
    crm_total_conversions, total_reported_conversions
)

conversions_by_source = unified.groupby("source")["conversions"].sum()
reconciled_conversions = get_reconciled_conversions(
    conversions_by_source, reconciliation_factor
)

average_order_value = get_average_order_value(crm)
reconciled_revenue = compute_revenue(reconciled_conversions, average_order_value)
spend_by_source = unified.groupby("source")["spend_eur"].sum()
roas_by_source = compute_roas(reconciled_revenue, spend_by_source)

global_revenue = crm["amount_eur"].sum()
crm_total_spend = unified["spend_eur"].sum()
global_roas = compute_roas(global_revenue, crm_total_spend)

# ASSUMPTION: 2.3x repeat-purchase multiplier comes from PharmaLife's 3-year
# CRM history (external to this pipeline). January alone shows 1.01
# purchases/customer, not enough time span to observe real recurrence.

ltv_order_value = get_ltv_order_value(average_order_value, LTV_MUlTIPLIER)

reconciled_revenue_ltv = compute_revenue(reconciled_conversions, ltv_order_value)
roas_ltv_by_source = compute_roas(reconciled_revenue_ltv, spend_by_source)

global_revenue_ltv = compute_revenue(crm_total_conversions, ltv_order_value)
global_roas_ltv = compute_roas(global_revenue_ltv, crm_total_spend)

logger.info(
    f"({crm_total_conversions} CRM sales / {total_reported_conversions} reported conversions)"
    f" = {reconciliation_factor:.4f} Reconciliation factor"
)

for source in reconciled_revenue.index:
    logger.info(
        f"{source}: {reconciled_conversions[source]:.0f} reconciled conversions, "
        f"€{reconciled_revenue[source]:,.2f} reconciled revenue, "
        f"ROAS {roas_by_source[source]:.2f}x"
    )

logger.info(
    f"Global ROAS: {global_roas:.2f}x"
    f"(€{reconciled_revenue.sum():,.2f} revenue / €{spend_by_source.sum():,.2f} spend)"
)
for source in reconciled_revenue_ltv.index:
    logger.info(
        f"{source}: LTV revenue €{reconciled_revenue_ltv[source]:,.2f}, "
        f"ROAS (LTV) {roas_ltv_by_source[source]:.2f}x"
    )

logger.warning(
    f"Global ROAS (LTV, 12mo): {global_roas_ltv:.2f}x vs first-purchase ROAS: {global_roas:.2f}x — "
    "these mix 1 month of spend against a 12-month revenue projection, not directly comparable"
)

channel_roas = pd.DataFrame(
    {
        "reported_conversions": conversions_by_source,
        "reconciled_conversions": reconciled_conversions,
        "reconciled_revenue": reconciled_revenue,
        "reconciled_revenue_ltv": reconciled_revenue_ltv,
        "spend_eur": spend_by_source,
        "roas": roas_by_source,
        "roas_ltv": roas_ltv_by_source,
    }
).reset_index()

GOLD_PATH.mkdir(parents=True, exist_ok=True)
channel_roas.to_parquet(GOLD_PATH / "channel_roas.parquet")
logger.info(f"rows: {len(channel_roas)} columns: {len(channel_roas.columns)}")

executive_summary = channel_roas.rename(
    columns={"source": "channel", "roas": "roas_first_purchase"}
).drop(columns=["reconciled_revenue", "reconciled_revenue_ltv"])

total_row = pd.DataFrame(
    [
        {
            "channel": "TOTAL",
            "reported_conversions": conversions_by_source.sum(),
            "reconciled_conversions": crm_total_conversions,
            "spend_eur": crm_total_spend,
            "roas_first_purchase": global_roas,
            "roas_ltv": global_roas_ltv,
        }
    ]
)
executive_summary = pd.concat([executive_summary, total_row], ignore_index=True)

executive_summary.to_parquet(GOLD_PATH / "executive_summary.parquet")
logger.info(f"rows: {len(executive_summary)} columns: {len(executive_summary.columns)}")
