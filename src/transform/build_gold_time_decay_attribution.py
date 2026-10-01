from pathlib import Path

import pandas as pd

from src.utils.logging_config import get_logger
from src.utils.paths import get_data_dir
from src.utils.roas import build_source_roas


def run():
    logger = get_logger(Path(__file__).stem)

    SILVER_PATH = get_data_dir("silver")
    GOLD_PATH = get_data_dir("gold")

    crm_sales = pd.read_parquet(SILVER_PATH / "crm_sales.parquet")
    LTV_MUlTIPLIER = 2.3

    def time_decay_attribution(touchpoints_str, decay_factor=0.5):
        channels = [
            touchpoints.split(":")[0] for touchpoints in touchpoints_str.split(",")
        ]
        n = len(channels)
        weights = [decay_factor ** (n - 1 - i) for i in range(n)]
        total_weight = sum(weights)
        return [
            {"source": channel, "credit": weight / total_weight}
            for channel, weight in zip(channels, weights)
        ]

    attribution_rows = []
    for touchpoint in crm_sales["touchpoints"]:
        attribution_rows.extend(time_decay_attribution(touchpoint))

    attribution = pd.DataFrame(attribution_rows)

    credit_by_source = attribution.groupby("source")["credit"].sum()
    assert credit_by_source.sum() == len(crm_sales), (
        "Attribution credit does not sum to total CRM sales"
    )

    source_roas = build_source_roas(credit_by_source, crm_sales)

    for _, row in source_roas.iterrows():
        logger.info(
            f"{row['source']}: {row['credit']:.2f} credit, "
            f"€{row['attributed_revenue']:,.2f} revenue, "
            f"ROAS {row['roas']:.2f}x, ROAS LTV {row['roas_ltv']:.2f}x"
        )

    logger.info(
        f"Total credit: {source_roas['credit'].sum():.2f} (CRM sales: {len(crm_sales)})"
    )

    GOLD_PATH.mkdir(parents=True, exist_ok=True)
    source_roas.to_parquet(GOLD_PATH / "time_decay_attribution_roas.parquet")
    logger.info(
        f"Saved {len(source_roas)} rows to {GOLD_PATH / 'time_decay_attribution_roas.parquet'}"
    )


if __name__ == "__main__":
    run()
