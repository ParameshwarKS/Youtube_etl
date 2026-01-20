# 🧪 Data Quality, Integration and Unit testing

## Data Quality Checks
We use SODA to perform few data quality checks on the data that is loaded into the database. Below are the checks which we perform:
1) Check if there are zero nulls in the column video_id
2) Check if there are no duplicates for the column video_id
3) Check if the comment counts are less than view counts
4) Check if the like counts are less than view counts

### yaml for checks
```yaml
checks for yt_api:
  - missing_count("Video_ID") = 0
  - duplicate_count("Video_ID") = 0

  - likes_count_greater_than_vid_views = 0:
      name: Check for Like_Count greater than Video_Views
      likes_count_greater_than_vid_views query: |
        SELECT COUNT(*)
        FROM yt_api
        where "Likes_Count" > "Video_Views"

  - comments_count_greater_than_vid_views = 0:
      name: Check for Like_Count greater than Video_Views
      comments_count_greater_than_vid_views query: |
        SELECT COUNT(*)
        FROM yt_api
        where "Comments_Count" > "Video_Views"
```
We create a python function to call which can be added as a task to the our DAG. The function uses a bash command which calls the above mentioned yaml code and perform the checks. We also need to provide the configuration of the postgres database so that it can connect to the database and perform the checks.

### yaml of configuration
```yaml
data_source pg_datasource:
  type: postgres
  username: ${ELT_DATABASE_USERNAME}
  password: ${ELT_DATABASE_PASSWORD}
  host: ${POSTGRES_CONN_HOST}
  port: ${POSTGRES_CONN_PORT}
  database: ${ELT_DATABASE_NAME}
  schema: ${SCHEMA}
```

### yaml for data quality checks
```yaml
checks for yt_api:
  - missing_count("Video_ID") = 0
  - duplicate_count("Video_ID") = 0

  - likes_count_greater_than_vid_views = 0:
      name: Check for Like_Count greater than Video_Views
      likes_count_greater_than_vid_views query: |
        SELECT COUNT(*)
        FROM yt_api
        where "Likes_Count" > "Video_Views"

  - comments_count_greater_than_vid_views = 0:
      name: Check for Like_Count greater than Video_Views
      comments_count_greater_than_vid_views query: |
        SELECT COUNT(*)
        FROM yt_api
        where "Comments_Count" > "Video_Views"
```

### Python function to perform the data quality check
```python
def yt_elt_data_quality(schema):
    try:
        task = BashOperator(
            task_id = f"soda_test_{schema}",
            bash_command = f"soda scan -d {DATASOURCE} -c {SODA_PATH}/configuration.yml -v SCHEMA={schema} {SODA_PATH}/checks.yml",
        )
        return task
    except Exception as e:
        logger.error(f"Error running data quality check for schema: {schema}")
        raise e
```

## Integration Checks
- We check if the api that we are using to pull the data, if it is responding correctly by checking the response status.
- We check if the connection with the database is established properly and the cursor which we are using to interact with the database is responding properly.

### Python function to check for the api response
```python
def test_youtube_api_response(airflow_variable):
    api_key = airflow_variable("api_key")
    channel_handle = airflow_variable("channel_handle")

    url = f"https://youtube.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={channel_handle}&key={api_key}"

    try:
        response = requests.get(url)
        assert response.status_code == 200
    except requests.RequestException as e:
        pytest.fail(f"Request to Youtube API failed: {e}")
```

### Python function to check for the database connection
```python
def test_real_postgres_connection(real_postgres_connection):
    cursor = None

    try:
        cursor = real_postgres_connection.cursor()
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()

        assert result[0] == 1

    except psycopg2.Error as e:
        pytest.fail(f"Database query failed: {e}")

    finally:
        if cursor is not None:
            cursor.close()
```
