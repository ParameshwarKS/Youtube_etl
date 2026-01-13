from airflow.decorators import dag, task
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
import pendulum
from datetime import timedelta

# Import your functions
from api.video_stats import get_playlist_id, get_video_ids, extract_video_data, save_to_json
from datawarehouse.dwh import staging_table, core_table
from dataquality.soda import yt_elt_data_quality

# Local timezone
local_tz = pendulum.timezone("Europe/Malta")

# Default args
default_args = {
    "owner": "dataengineers",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "email": "data@engineers.com",
    "max_active_runs": 1,
    "dagrun_timeout": timedelta(hours=1),
    "start_date": pendulum.datetime(2025, 1, 1, tz=local_tz),
}

staging_schema = "staging"
core_schema = "core"

# =========================
# DAG 1: produce_json
# =========================
@dag(
    dag_id="produce_json",
    default_args=default_args,
    schedule="0 14 * * *",
    catchup=False,
    description="DAG to produce JSON file with raw data",
)
def produce_json_dag():

    @task()
    def get_playlist_id_task():
        return get_playlist_id()

    @task()
    def get_video_ids_task(playlist_id):
        return get_video_ids(playlist_id)

    @task()
    def extract_video_data_task(video_ids):
        return extract_video_data(video_ids)

    @task()
    def save_to_json_task(data):
        save_to_json(data)

    playlist_id = get_playlist_id_task()
    video_ids = get_video_ids_task(playlist_id)
    extracted_data = extract_video_data_task(video_ids)
    save_to_json_task(extracted_data)

    # Trigger next DAG
    trigger_update_db = TriggerDagRunOperator(
        task_id="trigger_update_db",
        trigger_dag_id="update_db",
    )

    save_to_json_task(extracted_data) >> trigger_update_db


produce_json = produce_json_dag()


# =========================
# DAG 2: update_db
# =========================
@dag(
    dag_id="update_db",
    default_args=default_args,
    schedule=None,
    catchup=False,
    description="DAG to process JSON file and insert data into staging and core schemas",
)
def update_db_dag():

    @task()
    def update_staging_task():
        return staging_table()

    @task()
    def update_core_task():
        return core_table()

    staging = update_staging_task()
    core = update_core_task()

    # Trigger data quality DAG
    trigger_data_quality = TriggerDagRunOperator(
        task_id="trigger_data_quality",
        trigger_dag_id="data_quality",
    )

    staging >> core >> trigger_data_quality


update_db = update_db_dag()


# =========================
# DAG 3: data_quality
# =========================
@dag(
    dag_id="data_quality",
    default_args=default_args,
    schedule=None,
    catchup=False,
    description="DAG to check the data quality on both layers in the DB",
)
def data_quality_dag():

    @task()
    def validate_staging():
        return yt_elt_data_quality(staging_schema)

    @task()
    def validate_core():
        return yt_elt_data_quality(core_schema)

    staging_quality = validate_staging()
    core_quality = validate_core()

    staging_quality >> core_quality


data_quality = data_quality_dag()
