#!/usr/bin/env bash
# Script to launch MLflow UI
# Use sqlite backend as specified

# Ensure the directory exists
mkdir -p mlflow

echo "Starting MLflow UI with SQLite backend..."
echo "Access the UI at http://localhost:5000"
mlflow ui --backend-store-uri sqlite:///mlflow/mlflow.db --host 0.0.0.0 --port 5000
