from datetime import datetime, timedelta

from airflow.providers.smtp.notifications.smtp import send_smtp_notification
from airflow.providers.standard.operators.python import PythonOperator

from airflow import DAG
from src.ingest.ingest_csv_crm import run as ingest_crm_fn
from src.ingest.ingest_csv_daily import run as ingest_google_fn
from src.ingest.ingest_csv_mapping import run as ingest_mapping_fn
from src.ingest.ingest_csv_weekly import run as ingest_email_fn
from src.ingest.ingest_json_daily import run as ingest_meta_fn
from src.transform.build_gold_executive_summary import run as build_gold_executive_fn
from src.transform.build_gold_linear_attribution import run as build_gold_linear_fn
from src.transform.build_gold_proportional_reconciliation import (
    run as build_gold_proportional_fn,
)
from src.transform.build_gold_time_decay_attribution import (
    run as build_gold_time_decay_fn,
)
from src.transform.build_gold_unified_campaigns import run as build_gold_unified_fn
from src.transform.build_silver_campaign_mapping import run as build_silver_mapping_fn
from src.transform.build_silver_crm import run as build_silver_crm_fn
from src.transform.build_silver_email_campaigns import run as build_silver_email_fn
from src.transform.build_silver_google_ads import run as build_silver_google_fn
from src.transform.build_silver_meta_ads import run as build_silver_meta_fn

default_args = {
    "owner": "data-team",
    "depends_on_past": False,
    "on_failure_callback": send_smtp_notification(
        to=["eriik_mendoza@outlook.com"],
        subject="Airflow: task {{ ti.task_id }} failed",
        html_content="Task {{ ti.task_id }} in DAG {{ dag.dag_id }} failed.",
        smtp_conn_id="adpulse_smtp",
    ),
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}
with DAG(
    "pharmalife_weekly_report",
    default_args=default_args,
    description="Pipeline semanal PharmaLife: ingesta -> unificacion -> reconciliación -> reporte",
    schedule="0 7 * * 1",  # Lunes 7:00 AM
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["pharmalife", "weekly", "production"],
) as dag:
    ingest_google = PythonOperator(
        task_id="ingest_google", python_callable=ingest_google_fn
    )
    ingest_meta = PythonOperator(task_id="ingest_meta", python_callable=ingest_meta_fn)
    ingest_email = PythonOperator(task_id="ingest_email", python_callable=ingest_email_fn)
    ingest_crm = PythonOperator(task_id="ingest_crm", python_callable=ingest_crm_fn)
    ingest_mapping = PythonOperator(
        task_id="ingest_mapping", python_callable=ingest_mapping_fn
    )

    build_silver_mapping = PythonOperator(
        task_id="build_silver_mapping", python_callable=build_silver_mapping_fn
    )
    build_silver_crm = PythonOperator(
        task_id="build_silver_crm", python_callable=build_silver_crm_fn
    )
    build_silver_email = PythonOperator(
        task_id="build_silver_email", python_callable=build_silver_email_fn
    )
    build_silver_google = PythonOperator(
        task_id="build_silver_google", python_callable=build_silver_google_fn
    )
    build_silver_meta = PythonOperator(
        task_id="build_silver_meta", python_callable=build_silver_meta_fn
    )
    build_gold_unified = PythonOperator(
        task_id="build_gold_unified", python_callable=build_gold_unified_fn
    )
    build_gold_proportional = PythonOperator(
        task_id="build_gold_proportional", python_callable=build_gold_proportional_fn
    )
    build_gold_linear = PythonOperator(
        task_id="build_gold_linear", python_callable=build_gold_linear_fn
    )
    build_gold_time_decay = PythonOperator(
        task_id="build_gold_time_decay", python_callable=build_gold_time_decay_fn
    )
    build_gold_executive = PythonOperator(
        task_id="build_gold_executive", python_callable=build_gold_executive_fn
    )

    ingest_google >> build_silver_google
    ingest_meta >> build_silver_meta
    ingest_email >> build_silver_email
    ingest_mapping >> build_silver_mapping
    ingest_crm >> build_silver_crm

    [
        build_silver_google,
        build_silver_meta,
        build_silver_email,
        build_silver_mapping,
    ] >> build_gold_unified

    [build_silver_crm, build_gold_unified] >> build_gold_proportional
    [build_silver_crm, build_gold_unified] >> build_gold_linear
    [build_silver_crm, build_gold_unified] >> build_gold_time_decay

    [
        build_gold_proportional,
        build_gold_linear,
        build_gold_time_decay,
    ] >> build_gold_executive
