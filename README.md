# Multilingual Aspect-Based Sentiment Analysis (ABSA)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-00a393.svg)
![HTMX](https://img.shields.io/badge/HTMX-1.9-3d72d4.svg)
![DVC](https://img.shields.io/badge/DVC-3.51.1-945dd6.svg)
![MLflow](https://img.shields.io/badge/MLflow-2.13.0-0194E2.svg)

This repository contains a multilingual Aspect-Based Sentiment Analysis system for English, Hindi, and Hinglish product reviews. It provides both a FastAPI JSON API and a server-rendered web UI backed by Jinja2 templates and HTMX interactions.

The inference stack is centered on ONNX Runtime models, with a fallback pipeline for environments where the custom artifacts are not available. The project also includes DVC pipelines, MLflow tracking, Redis/Celery workers, PostgreSQL, and Prometheus/Grafana monitoring.

## What’s Included

- Multilingual review processing for English, Hindi, and Hinglish.
- FastAPI application with prediction, results, and monitoring routes.
- Server-rendered UI available at `/predict`, `/batch`, and `/monitor`.
- Batch processing, async task execution, and database-backed persistence.
- DVC, MLflow, and monitoring assets for experiment and system tracking.

## Repository Layout

```text
api/          FastAPI app, routes, middleware, schemas, services, templates
config/       Docker and deployment configuration
data/         Raw and processed datasets
docs/         Architecture, API, deployment, and design notes
ml/           Training notebooks and experimentation assets
models/       Model artifacts, including ONNX assets
monitoring/   Prometheus and Grafana configuration
scripts/      Utility scripts for data, models, and monitoring
src/          Core data, training, and evaluation code
tests/        Test suite
dashboard_backup/  Legacy React dashboard preserved as a backup
```

## Getting Started

### Prerequisites

- Python 3.10+
- Docker and Docker Compose if you want the full stack

### Local Setup

```bash
git clone <repository-url>
cd Multilingual-Absa

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If you use environment variables, create a local `.env` file before starting the app.

### Run the App Locally

```bash
PYTHONPATH=. uvicorn api.app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:

- `http://localhost:8000/predict`
- `http://localhost:8000/batch`
- `http://localhost:8000/monitor`
- `http://localhost:8000/docs`

### Run with Docker

```bash
docker compose -f config/docker/docker-compose.yml up --build
```

That compose file starts the API, worker, PostgreSQL, Redis, Prometheus, Grafana, and the dashboard service.

### Reproduce the ML Pipeline

```bash
dvc pull
dvc repro
dvc push
```

## How It Works

1. A review is submitted through the API or web UI.
2. The app detects or accepts the language and routes the request through the ABSA pipeline.
3. The pipeline uses the available ONNX-backed models when present.
4. If the model artifacts are missing, the system falls back to the rule-based path so inference can still continue.
5. Predictions and runtime signals can be observed through the app, metrics endpoint, and monitoring stack.

## Notes

- The active web UI is served by the FastAPI app. `dashboard_backup/` is kept only as a legacy reference.
- The main application entrypoint is `api.app.main:app`.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
