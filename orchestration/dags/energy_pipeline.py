"""Nightly pipeline: ingest -> dbt -> quality -> features -> train."""
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

P = "/project"
with DAG(
    dag_id="energy_demand_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="0 2 * * *",
    catchup=False,
    default_args={"retries": 1},
    tags=["energy"],
) as dag:
    ingest   = BashOperator(task_id="ingest",         bash_command=f"cd {P} && python ingestion/backfill.py || true")
    dbt_run  = BashOperator(task_id="dbt_build",      bash_command=f"cd {P}/transforms && dbt build --profiles-dir .")
    quality  = BashOperator(task_id="quality_gate",   bash_command=f"cd {P} && python quality/validate_mart_lite.py")
    features = BashOperator(task_id="build_features", bash_command=f"cd {P} && python features/build_features.py")
    train    = BashOperator(task_id="train",          bash_command=f"cd {P} && GIT_PYTHON_REFRESH=quiet MLFLOW_TRACKING_URI=sqlite:////project/mlflow_airflow.db MLFLOW_EXPERIMENT=energy-airflow MLFLOW_ARTIFACT_LOCATION=file:/project/mlruns_airflow python ml/train.py")

    ingest >> dbt_run >> quality >> features >> train
