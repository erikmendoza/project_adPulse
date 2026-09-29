import pandas as pd

from src.utils.paths import get_data_dir

# ASSUMPTION: 2.3x repeat-purchase multiplier comes from PharmaLife's 3-year
# CRM history (external to this pipeline). One month of CRM data isn't
# enough to observe real recurrence.
LTV_MULTIPLIER = 2.3

GOLD_PATH = get_data_dir("gold")


def build_source_roas(
    credit_by_source: pd.Series, crm_sales: pd.DataFrame
) -> pd.DataFrame:
    average_order_value = crm_sales["amount_eur"].mean()
    attributed_revenue = credit_by_source * average_order_value

    unified = pd.read_parquet(GOLD_PATH / "unified_campaigns.parquet")
    spend_by_source = unified.groupby("source")["spend_eur"].sum()
    roas = attributed_revenue / spend_by_source

    # ROAS LTV
    ltv_order_value = average_order_value * LTV_MULTIPLIER
    attributed_revenue_ltv = credit_by_source * ltv_order_value
    roas_ltv = attributed_revenue_ltv / spend_by_source

    return pd.DataFrame(
        {
            "credit": credit_by_source,
            "attributed_revenue": attributed_revenue,
            "attributed_revenue_ltv": attributed_revenue_ltv,
            "spend_eur": spend_by_source,
            "roas": roas,
            "roas_ltv": roas_ltv,
        }
    ).reset_index()
