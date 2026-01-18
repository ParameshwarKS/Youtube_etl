This document provides the explaination for load and transformation part of the ETL process which is being performed in this project.

## Create schema and tables
We create 2 schemas:
1) `staging` : Required for dumping the data into the datawarehouse that is ready to be transformed.
2) `core` : Required to store the tables that is transformed.

### Establishing the connection
First, we need to establish the connection to the postgres database in the Airflow. For this we will be using PostgresHook of Airflow. Also, we require cursor to interact with the database.
Creates a PostgreSQL database connection and cursor using Airflow’s connection system, and returns both so you can execute SQL queries.

```python
hook = PostgresHook(
    postgres_conn_id="postgres_db_yt_elt",
    database="elt_db"
)
```
**What is PostgresHook?**
- An Airflow abstraction over psycopg2
- Handles authentication, host, port, username, password automatically
- Reads credentials from Airflow Connections

```python
conn = hook.get_conn()
```
`hook.get_conn()` returns a psycopg2 connection object


```python
cur = conn.cursor(cursor_factory=RealDictCursor)
```
**What is a cursor?**
- Used to execute SQL
- Fetch results from the database

**What is RealDictCursor?**
- Returns each row as a Python dictionary instead of a tuple

### Function to create schema
```python
def create_schema(schema):
    conn, cur = get_conn_cursor()
    schema_sql = f"CREATE SCHEMA IF NOT EXISTS {schema};"
    cur.execute(schema_sql)
    conn.commit()
    close_conn_cursor(conn,cur)
```
`schema` is passed as an argument to the above function which can take the value as `staging` or `core`. 

### Columns and data type in staging schema:
 | Column Name  |    Data type    |     Constraint     |
 | ------------ | --------------- | ------------------ |
 | Video_ID     |   VARCHAR(11)   |PRIMARY KEY NOT NULL|
 | Video_Title  |      TEXT       |      NOT NULL      |
 | Upload_Date  |    TIMESTAMP    |      NOT NULL      |
 |  Duration    |   VARCHAR(20)   |      NOT NULL      |
 | Video_Views  |      INT        |                    |
 | Likes_Count  |      INT        |                    |
 |Comments_Count|      INT        |                    |

### Columns and data type in core schema:
 | Column Name  |    Data type    |     Constraint     |
 | ------------ | --------------- | ------------------ |
 | Video_ID     |   VARCHAR(11)   |PRIMARY KEY NOT NULL|
 | Video_Title  |      TEXT       |      NOT NULL      |
 | Upload_Date  |    TIMESTAMP    |      NOT NULL      |
 |  Duration    |      TIME       |      NOT NULL      |
 | Video_Type   |   VARCHAR(10)   |      NOT NULL      |
 | Video_Views  |      INT        |                    |
 | Likes_Count  |      INT        |                    |
 |Comments_Count|      INT        |                    |

### Function to create table:
```python
def create_table(schema):
    conn, cur = get_conn_cursor()
    if schema=="staging":
        table_sql = f"""
                CREATE TABLE IF NOT EXISTS {schema}.{table} (
                    "Video_ID" VARCHAR(11) PRIMARY KEY NOT NULL,
                    "Video_Title" TEXT NOT NULL,
                    "Upload_Date" TIMESTAMP NOT NULL,
                    "Duration" VARCHAR(20) NOT NULL,
                    "Video_Views" INT,
                    "Likes_Count" INT,
                    "Comments_Count" INT
                );"""
    else:
        table_sql = f"""
                CREATE TABLE IF NOT EXISTS {schema}.{table} (
                    "Video_ID" VARCHAR(11) PRIMARY KEY NOT NULL,
                    "Video_Title" TEXT NOT NULL,
                    "Upload_Date" TIMESTAMP NOT NULL,
                    "Duration" TIME NOT NULL,
                    "Video_Type" VARCHAR(10) NOT NULL,
                    "Video_Views" INT,
                    "Likes_Count" INT,
                    "Comments_Count" INT
                );"""
    cur.execute(table_sql)
    conn.commit()
    close_conn_cursor(conn,cur)
```
In the staging schema the column duration is taken as VARCHAR(20) because, the data which we get from the API is in the format `AAPBBTCCMDDS` which means it the duration of the video is AA days, BB hours, CC minutes and DD seconds.

<img width="1382" height="179" alt="image" src="https://github.com/user-attachments/assets/a03b0dcb-4031-447c-b74c-ffa9e5f0064e" />

The duration column in staging schema is a VARCHAR(20) which is hard to read hence in the core schema we are transforming that into time data type. Also, the column duration is used to derive a new column Video_Type that marks if the video is a short or a normal video. The condition goes this way- if the duration <= 60sec then it is a short else it is normal.

### Function to transform the table:
```python
def parse_duration(duration_str):
    duration_str = duration_str.replace("P","").replace("T","")
    components = ['D','H','M','S']
    values = {}
    values.setdefault('D',0)
    values.setdefault('H',0)
    values.setdefault('M',0)
    values.setdefault('S',0)
    for component in components:
        if component in duration_str:
            value, duration_str = duration_str.split(component)
            values[component] = int(value)
    total_duration = timedelta(
        days = values['D'],
        hours = values['H'],
        minutes = values['M'],
        seconds = values['S']
    )
    return total_duration

def transform_data(row):
    duration_td = parse_duration(row["Duration"])
    row["Duration"] = (datetime.min + duration_td).time()
    row["Video_Type"] = "Shorts" if duration_td.total_seconds() <= 60 else "Normal"
    return row
```
The function transform_data takes a row as an argument and returns the transformed row, hence to transform the complete table the function needs to be called iteratively.


