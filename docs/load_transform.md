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

<img width="1382" height="179" alt="image" src="https://github.com/user-attachments/assets/a03b0dcb-4031-447c-b74c-ffa9e5f0064e" />


