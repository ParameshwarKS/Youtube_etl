# Data Quality, Integration and Unit testing

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
