# 🐳 Docker Compose Setup for Apache Airflow

This document provides a **detailed explanation** of the `docker-compose.yaml` file used in this project to set up a **local Apache Airflow cluster** using **CeleryExecutor**, **Redis**, and **PostgreSQL**.

> ⚠️ **Note**: This setup is intended **only for local development and testing**. It is **not recommended for production** environments.

---

## 📦 Overview of the Architecture

The Docker Compose configuration provisions the following services:

- **Airflow Webserver** – Provides the UI
- **Airflow Scheduler** – Schedules and triggers DAGs
- **Airflow Workers (Celery)** – Executes tasks
- **Redis** – Acts as the Celery message broker
- **PostgreSQL** – Stores metadata, task results, and ELT data

---

## 🪪 Apache License Header

The file begins with the Apache Software Foundation (ASF) license header.  
This grants permission to use, modify, and distribute the software under the **Apache License 2.0**.

---

## 🔁 YAML Anchors (`x-airflow-common`)
```yaml
x-airflow-common: &airflow-common
```
This section defines a shared configuration template that is reused across multiple Airflow services (webserver, scheduler, worker, init, CLI).
It helps avoid duplication and ensures consistency.

## 🐳 Custom Airflow Docker Image
```yaml
image: ${DOCKERHUB_NAMESPACE}/${DOCKERHUB_REPOSITORY}:latest
```
- Uses a custom-built Airflow image
- Built on top of apache/airflow:2.9.2
- Allows pre-installation of Python dependencies
- Pulled from Docker Hub

## 🌱 Environment Configuration

All core Airflow configurations are defined via environment variables.

### Executor Configuration
```yaml
AIRFLOW__CORE__EXECUTOR: CeleryExecutor
```
- Enables distributed task execution
- Tasks are sent to workers via Redis

### Metadata Database (PostgreSQL)
```yaml
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN
```
**Stores:**
- DAG metadata
- Task states
- Run history

Uses the psycopg2 PostgreSQL driver

### Celery Result Backend
```yaml
AIRFLOW__CELERY__RESULT_BACKEND
```
- Stores task execution results
- Required for CeleryExecutor

### Redis Broker
```yaml
AIRFLOW__CELERY__BROKER_URL: redis://:@redis:6379/0
```
- Provides message brokerage service
- Communicates between the scheduler and the worker

### Security – Fernet Key
```yaml
AIRFLOW__CORE__FERNET_KEY
```
- Encrypts airflow variables and Connections
- Mandatory for secure setups

### DAG Defaults
```yaml
AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
```
- Newly created DAGs are paused by default
- Examples are not loaded

### API Authentication
```yaml
AIRFLOW__API__AUTH_BACKENDS
```
- Basic authentication
- Session based login for UI and API

## 🔐 Airflow Connections & Variables
### External PostgreSQL Connection
```yaml
AIRFLOW_CONN_POSTGRES_DB_YT_ELT
```
- Defines a reusable Airflow connection
- Used by DAGs to load ELT data into PostgreSQL

### Airflow Variables
```yaml
AIRFLOW_VAR_API_KEY
AIRFLOW_VAR_CHANNEL_HANDLE
```
- Variables defined in airflow for API_KEY and the Channel_Handle
- Variables should be prefixed with AIRFLOW_VAR_

## 📁 Volume Mounts
```yaml
volumes:
  - ./dags:/opt/airflow/dags
  - ./data:/opt/airflow/data
  - ./logs:/opt/airflow/logs
```
These mounts:
- Enable live DAG updates
- Persist logs across restarts
- Share extracted data between containers
- Maps the local directories to the airflow directories

## 👤 User Permissions
```yaml
user: "${AIRFLOW_UID}:0"
```
- Prevents permission issues on Linux systems
- Ensures files are owned by the host user


## 🔗 Service Dependencies
- Ensures Redis and PostgreSQL are healthy
- Prevents startup race conditions

## 🗄 PostgreSQL Service
Uses `postgres:13`

**Hosts:**
- Airflow metadata DB
- Celery backend DB
- ELT target database

## 🌐 Airflow Webserver

Runs the Airflow UI
- Exposed on http://localhost:8080
- Includes a health endpoint for monitoring

## ⏰ Airflow Scheduler

**Responsible for:**
- Triggering DAG runs
- Sending tasks to Redis
- Continuously monitors DAG schedules

## ⚙️ Airflow Worker

- Executes tasks pulled from Redis
- Reports task results to PostgreSQL
- Supports graceful shutdown

## 🧪 Airflow Init Container

**Runs once during startup and performs:**
- Database migrations
- Admin user creation
- Resource validation (CPU, RAM, disk)
- Directory permission fixes

After successful execution, other services start.

## 🧰 Airflow CLI (Debug Mode)
Allows manual Airflow commands for debugging, such as:
```bash
docker compose run airflow-cli airflow dags list
```

## 💾 Docker Volume
- Persists PostgreSQL data
- Prevents data loss on container restarts

---

# 🐳 Dockerfile Explanation

The Dockerfile is responsible for building a **custom Apache Airflow image** with a fixed Airflow and Python version along with all project-specific dependencies.

## 1️⃣ Build Arguments – Airflow & Python Versions
```dockerfile
ARG AIRFLOW_VERSION=2.9.2
ARG PYTHON_VERSION=3.10
```

Defines build-time variables
Allows flexibility to:
- Upgrade/downgrade Airflow
- Change Python versions

## 2️⃣ Base Image
```dockerfile
FROM apache/airflow:${AIRFLOW_VERSION}-python${PYTHON_VERSION}
```
Uses the official Apache Airflow Docker image

Ensures:
- Correct Airflow version
- Compatible Python runtime
- Provides a stable and production-tested base

## 3️⃣ Airflow Home Directory
```dockerfile
ENV AIRFLOW_HOME=/opt/airflow
```
Sets the default Airflow home directory

This is where Airflow stores:
- DAGs
- Logs
- Plugins
- Configurations

This matches the directory structure used by Airflow’s official images.

## 4️⃣ Copy Python Dependencies
```dockerfile
COPY requirements.txt /
```
Copies the project’s requirements.txt file into the container root

Contains all Python dependencies required for:
- Testing (pytest)
- Data quality checks (Soda)

## 5️⃣ Install Python Dependencies
```dockerfile
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt
```
**Installs:**
- The exact Airflow version defined by AIRFLOW_VERSION
- All project-specific dependencies

**--no-cache-dir:**
- Reduces image size
- Avoids retaining pip cache

## 📌 Reinstalling Airflow ensures:
- Version consistency
- Dependency resolution compatibility

## 🐘 PostgreSQL Initialization Script
This Bash script is executed automatically when the PostgreSQL container starts.
Its purpose is to create multiple databases and users required by the Airflow ecosystem and the ELT pipeline.

This script is mounted into:
```yaml
volumes:
      - postgres-db-volume:/var/lib/postgresql/data
      - ./docker/postgres/init-multiple-databases.sh:/docker-entrypoint-initdb.d/init-multiple-databases.sh
```

### 📌 Script Content
```bash
#!/bin/bash
```
**Shebang**
- Tells the system to execute the script using Bash

### ⚠️ Strict Mode
```bash
set -e
set -u
```
What these do:
- set -e → Exit immediately if any command fails
- set -u → Treat unset variables as an error

✔ Prevents silent failures
✔ Makes script safer and predictable

### 🔧 Function: `create_user_and_database`
**Function Parameters**
```bash
local database=$1
local username=$2
local password=$3
```

| Argument | Meaning       |
| -------- | ------------- |
| `$1`     | Database name |
| `$2`     | Username      |
| `$3`     | Password      |

### PostgreSQL Commands Execution
```bash
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
```
**Explanation:**
- psql → PostgreSQL command-line client
- ON_ERROR_STOP=1 → Stop execution if any SQL command fails
- --username "$POSTGRES_USER" → Connects using the default superuser
- <<-EOSQL → Here-document to execute multiple SQL statements

**SQL Statements**
```bash
CREATE USER $username WITH PASSWORD '$password';
CREATE DATABASE $database;
GRANT ALL PRIVILEGES ON DATABASE $database TO $username;
```

What each line does:
- Creates a new PostgreSQL user
- Creates a new database
- Grants full access of the database to the user
This ensures role-based isolation.

### 🗄 Database Creation Calls
**Metadata Database**
```bash
create_user_and_database  $METADATA_DATABASE_NAME  $METADATA_DATABASE_USERNAME  $METADATA_DATABASE_PASSWORD
```
Used by:
- Airflow scheduler
- Airflow webserver
- Stores DAG metadata and task states

**Celery Result Backend Database**
```bash
create_user_and_database  $CELERY_BACKEND_NAME  $CELERY_BACKEND_USERNAME  $CELERY_BACKEND_PASSWORD
```
Used by:
- CeleryExecutor
- Stores task execution results

**ELT Target Database**
```bash
create_user_and_database  $ELT_DATABASE_NAME  $ELT_DATABASE_USERNAME  $ELT_DATABASE_PASSWORD
```
Used by:
- YouTube ELT pipeline
- Stores transformed analytics data

### 🧠 Why This Script Is Important
✔ Avoids manual database setup
✔ Ensures repeatable environments
✔ Supports CI/CD pipelines
✔ Enforces database separation
✔ Executes only once during container initialization

## ✅ Summary

The Docker Compose configuration provides:
- A fully distributed Airflow CeleryExecutor setup
- Clean separation of services
- CI/CD compatibility
- A scalable foundation for ELT pipelines
- All Airflow orchestration in this project runs on top of this environment.

The Dockerfile helps to:
- Ensures consistent Airflow & Python versions
- Avoids dependency drift across environments
- CI/CD friendly (immutable images)
- Faster container startup (dependencies baked into image)