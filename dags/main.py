from airflow import DAG
import pendulum
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

from api.video_stats import (
    get_playlist_id,
    get_video_ids,
    extract_video_data,
    save_to_json,
)

from datawarehouse.dwh import staging_table, core_table
from dataquality.soda import yt_elt_data_quality

# Timezone
local_tz = pendulum.timezone("Europe/Malta")

# Default Args
default_args = {
    "owner": "dataengineers",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "email": "data@engineers.com",
    "max_active_runs": 1,
    "dagrun_timeout": timedelta(hours=1),
    "start_date": datetime(2025, 1, 1, tzinfo=local_tz),
}

staging_schema = "staging"
core_schema = "core"

# ─────────────────────────────────────────────────────────────
# DAG 1: produce_json
# ─────────────────────────────────────────────────────────────
with DAG(
    dag_id="produce_json",
    default_args=default_args,
    description="DAG to produce JSON file with raw data",
    schedule="0 14 * * *",
    catchup=False,
) as dag_produce:

    get_playlist = PythonOperator(
        task_id="get_playlist_id",
        python_callable=get_playlist_id,
    )

    get_videos = PythonOperator(
        task_id="get_video_ids",
        python_callable=get_video_ids,
        op_args=[get_playlist.output],
    )

    extract_data = PythonOperator(
        task_id="extract_video_data",
        python_callable=extract_video_data,
        op_args=[get_videos.output],
    )

    save_json = PythonOperator(
        task_id="save_to_json",
        python_callable=save_to_json,
        op_args=[extract_data.output],
    )

    trigger_update_db = TriggerDagRunOperator(
        task_id="trigger_update_db",
        trigger_dag_id="update_db",
        wait_for_completion=False,
    )

    get_playlist >> get_videos >> extract_data >> save_json >> trigger_update_db


# ─────────────────────────────────────────────────────────────
# DAG 2: update_db
# ─────────────────────────────────────────────────────────────
with DAG(
    dag_id="update_db",
    default_args=default_args,
    description="DAG to process JSON file and insert data into both staging and core schemas",
    schedule=None,
    catchup=False,
) as dag_update:

    update_staging = staging_table()
    update_core = core_table()

    trigger_data_quality = TriggerDagRunOperator(
        task_id="trigger_data_quality",
        trigger_dag_id="data_quality",
        wait_for_completion=False,
    )

    update_staging >> update_core >> trigger_data_quality


# ─────────────────────────────────────────────────────────────
# DAG 3: data_quality
# ─────────────────────────────────────────────────────────────
with DAG(
    dag_id="data_quality",
    default_args=default_args,
    description="DAG to check the data quality on both layers in the database",
    schedule=None,
    catchup=False,
) as dag_quality:

    soda_validate_staging = yt_elt_data_quality(staging_schema)
    soda_validate_core = yt_elt_data_quality(core_schema)

    soda_validate_staging >> soda_validate_core
