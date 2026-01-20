# 🚀 CI/CD Pipeline – GitHub Actions

This repository uses GitHub Actions to implement a complete CI/CD pipeline that automates:
- Docker image builds and publishing
- Unit, integration, and end-to-end (E2E) testing
- Conditional execution based on code changes
- Secure secret handling using GitHub Secrets and Variables

## 📌 Workflow Triggers
```yaml
on:
  push:
    branches:
      - main
      - 'feature/*'
  pull_request:
    branches:
      - main
  workflow_dispatch:
```

When does the pipeline run?
|     Trigger     |                      Description                          |
| --------------- | --------------------------------------------------------- | 
|      push	      |  Runs when code is pushed to main or any feature/* branch |
| pull_request    |	Runs when a PR is raised against main                     |
|workflow_dispatch|	Allows manual execution from GitHub UI                    |    

## 🧱 Jobs Overview
This workflow has two jobs, executed sequentially:
- Build & Push Docker Image
- Run Unit, Integration, and End-to-End Tests

### 🐳 Job 1: Build and Push Docker Image
```yaml
build-and-push-image:
        runs-on: ubuntu-latest
        steps: 
            - name: Checkout code
              uses: actions/checkout@v4
            - name: Get changed files
              id: changed-files-build
              uses: tj-actions/changed-files@v45
              with:
                files: |
                    Dockerfile
                    requirements.txt
            - name: Set up Docker Buildx
              if: steps.changed-files-build.outputs.any_changed == 'true'  || github.event_name == 'workflow_dispatch'
              uses: docker/setup-buildx-action@v3
            - name: Login to DockerHub
              if: steps.changed-files-build.outputs.any_changed == 'true'  || github.event_name == 'workflow_dispatch'
              uses: docker/login-action@v3
              with:
                username: ${{ vars.DOCKERHUB_USERNAME }}
                password: ${{ secrets.DOCKERHUB_PASSWORD }}
            - name: Build and push Docker image
              if: steps.changed-files-build.outputs.any_changed == 'true'  || github.event_name == 'workflow_dispatch'
              run: |
                      docker buildx build --push \
                        --tag ${{ vars.DOCKERHUB_NAMESPACE }}/${{ vars.DOCKERHUB_REPOSITORY }}:latest \
                        --tag ${{ vars.DOCKERHUB_NAMESPACE }}/${{ vars.DOCKERHUB_REPOSITORY }}:${{ github.sha }} \
                        .
```
Fetches the file names where changes are made and if the changes are made in either dockerfile or the requirements.txt where the versions of the soda and pytest are specified then an immutable docker image is build with the latest comitted dockerfile and the requirements.txt file and is pushed to the dockerhub. 
The docker image that is built is given with two tags.
- latest
- github.sha
If neither of the dockerfile nor requirements.txt files changes, Docker build is skipped.

### 🧪 Job 2: Unit, Integration & E2E Tests
Monitors:
- dags/**
- include/**
- docker-compose.yaml
Tests only run if relevant code changes.

```bash
airflow dags test <dag_id>
```
✔ Executes all tasks in the DAG sequentially
✔ Ignores the schedule
✔ Does not write DAG run metadata permanently
✔ Uses local executor logic

So, we pass the list of existing dags and we iterate the list through a for loop and run the dag test for each dag.
```yaml
unit-and-integration-and-e2e-tests:
      runs-on: ubuntu-latest
      needs: build-and-push-image
      env:
        AIRFLOW_WWW_USER_PASSWORD: ${{ secrets.AIRFLOW_WWW_USER_PASSWORD }}
        AIRFLOW_WWW_USER_USERNAME: ${{ secrets.AIRFLOW_WWW_USER_USERNAME }}
        API_KEY: ${{ secrets.API_KEY }}
        CELERY_BACKEND_NAME: ${{ secrets.CELERY_BACKEND_NAME }}
        CELERY_BACKEND_PASSWORD: ${{ secrets.CELERY_BACKEND_PASSWORD }}
        CELERY_BACKEND_USERNAME: ${{ secrets.CELERY_BACKEND_USERNAME }}
        ELT_DATABASE_NAME: ${{ secrets.ELT_DATABASE_NAME }}
        ELT_DATABASE_PASSWORD: ${{ secrets.ELT_DATABASE_PASSWORD }}
        ELT_DATABASE_USERNAME: ${{ secrets.ELT_DATABASE_USERNAME }}
        FERNET_KEY: ${{ secrets.FERNET_KEY }}
        METADATA_DATABASE_NAME: ${{ secrets.METADATA_DATABASE_NAME }}
        METADATA_DATABASE_PASSWORD: ${{ secrets.METADATA_DATABASE_PASSWORD }}
        METADATA_DATABASE_USERNAME: ${{ secrets.METADATA_DATABASE_USERNAME }}
        POSTGRES_USER: ${{ secrets.POSTGRES_CONN_USERNAME }}
        POSTGRES_PASSWORD: ${{ secrets.POSTGRES_CONN_PASSWORD }}
        POSTGRES_CONN_HOST: ${{ secrets.POSTGRES_CONN_HOST }}
        POSTGRES_CONN_PASSWORD: ${{ secrets.POSTGRES_CONN_PASSWORD }}
        POSTGRES_CONN_PORT: ${{ secrets.POSTGRES_CONN_PORT }}
        POSTGRES_CONN_USERNAME: ${{ secrets.POSTGRES_CONN_USERNAME }}
        AIRFLOW_UID: ${{ vars.AIRFLOW_UID }}
        CHANNEL_HANDLE: ${{ vars.CHANNEL_HANDLE }}
        DOCKERHUB_NAMESPACE: ${{ vars.DOCKERHUB_NAMESPACE }}
        DOCKERHUB_REPOSITORY: ${{ vars.DOCKERHUB_REPOSITORY }}
        DOCKERHUB_USERNAME: ${{ vars.DOCKERHUB_USERNAME }}
      steps:
        - name: Checkout code
          uses: actions/checkout@v4
        - name: Get changed files
          id: changed-files-tests
          uses: tj-actions/changed-files@v45
          with:
            files: |
                dags/**
                include/**
                docker-compose.yaml
        - name: Set up Docker Compose
          if: steps.changed-files-tests.outputs.any_changed == 'true' || github.event_name == 'workflow_dispatch'
          run: docker compose up -d
        - name: Run Unit and Integration Tests
          if: steps.changed-files-tests.outputs.any_changed == 'true' || github.event_name == 'workflow_dispatch'
          run: docker exec -t airflow-worker sh -c "pytest tests/ -v"
        - name: Run End-to-End DAG Tests
          if: steps.changed-files-tests.outputs.any_changed == 'true' || github.event_name == 'workflow_dispatch'
          run: |
            DAG_NAMES=("produce_json")
            for DAG in "${DAG_NAMES[@]}"; do 
              docker exec -t airflow-worker sh -c "airflow dags test $DAG"
            done
        - name: Tear down Docker Compose
          if: steps.changed-files-tests.outputs.any_changed == 'true' || github.event_name == 'workflow_dispatch'
          run: docker compose down
```

### 🔐 Environment Variables
All sensitive values are injected using:
- GitHub Secrets (passwords, keys)
- GitHub Variables (non-sensitive configs)

## 🏁 Summary
This CI/CD pipeline ensures:
🔒 Secure secret handling
🧪 Strong test coverage
🐳 Reliable Docker builds
🚀 Safe and repeatable deployments

Any change merged into main is guaranteed to be tested, reproducible, and production-ready.
