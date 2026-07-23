# Multilingual Aspect-Based Sentiment Analysis (ABSA)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-00a393.svg)](https://fastapi.tiangolo.com)
[![HTMX](https://img.shields.io/badge/HTMX-2.0-3d72d4.svg)](https://htmx.org)
[![DVC](https://img.shields.io/badge/DVC-3.51-945dd6.svg)](https://dvc.org)
[![MLflow](https://img.shields.io/badge/MLflow-2.15-0194E2.svg)](https://mlflow.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Analyse product reviews in English, Hindi, and Hinglish — extract aspects and their sentiment in real time.**

---

## Quick Start

```bash
git clone <repo-url> && cd multilingual-absa
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:
- **Web UI** → [`http://localhost:8000/predict`](http://localhost:8000/predict)
- **Batch upload** → [`http://localhost:8000/batch`](http://localhost:8000/batch)
- **API docs** → [`http://localhost:8000/docs`](http://localhost:8000/docs)

---

## What This Does

The system identifies **aspects** (specific features like "battery life", "sound quality") and their **sentiment** (positive, negative, neutral) from product reviews. It supports three languages:

| Language | Aspect Extraction | Sentiment |
|----------|:-:|:-:|
| English   | ✅ | ✅ |
| Hindi     | ✅ | ✅ |
| Hinglish  | ✅ | ✅ |

**Production performance** (ONNX INT8 quantised):

| Language | F1 Score | Latency p95 |
|----------|:--------:|:-----------:|
| English  | 78.1%    | 185 ms      |
| Hindi    | 67.8%    | 185 ms      |

---

## Project Structure

```
.
├── app/                        # FastAPI web application
│   ├── main.py                 # Entry point — uvicorn app.main:app
│   ├── core/                   # App configuration (templates, settings)
│   ├── middleware/              # CSRF, rate limiting, metrics, DB deps
│   ├── routes/                 # API endpoints (predict, batch, health) + HTMX pages
│   ├── schemas/                # Pydantic models + SQLAlchemy ORM
│   ├── services/               # ABSA inference pipeline, language detection
│   ├── tasks/                  # Celery batch processing workers
│   ├── static/                 # CSS design system
│   └── templates/              # Jinja2 + HTMX frontend
│       ├── base.html           # Layout with Alpine.js, Tailwind, HTMX
│       ├── pages/              # Page templates (predict, batch, monitor)
│       ├── partials/           # HTMX fragment partials
│       └── macros/             # Reusable UI macros (badges, icons)
├── absa/                       # Core ML library (pure Python)
│   ├── data/                   # Data loading, preprocessing, augmentation
│   ├── models/                 # Training scripts (ONNX, Transformers, baselines)
│   ├── evaluation/             # Cross-lingual eval, latency benchmarking
│   ├── training/               # MLflow experiment tracking
│   └── utils/                  # Path configuration
├── docker/                     # Containerisation
│   ├── Dockerfile              # Production app image
│   ├── Dockerfile.prod         # Production image (HuggingFace Hub model source)
│   ├── docker-compose.yml      # Full stack: API + worker + DB + Redis + monitoring
│   └── docker-compose.prod.yml # Production overrides
├── tests/                      # Test suite
│   ├── api/                    # API endpoint tests
│   ├── web/                    # Page rendering + HTMX fragment tests
│   └── unit/                   # Unit tests (bio tagger, lang detect)
├── scripts/                    # Utility scripts
├── docs/                       # Documentation
├── .env.example                # Environment variable template
├── dvc.yaml                    # DVC data pipeline
└── pyproject.toml              # Project metadata
```

---

## Architecture

```
┌─────────┐    HTMX / Alpine.js     ┌──────────────────┐
│ Browser │◄───────────────────────►│   FastAPI (8000)  │
└─────────┘                         │   app/main.py     │
                                    │                   │
                                    │  ┌─────────────┐  │
                                    │  │ Jinja2       │  │
                                    │  │ Templates    │  │
                                    │  └─────────────┘  │
                                    │  ┌─────────────┐  │
                                    │  │ JSON REST    │  │
                                    │  │ API          │  │
                                    │  └─────────────┘  │
                                    └────────┬──────────┘
                                             │
                    ┌────────────────────────┼────────────────────┐
                    │                        │                    │
              ┌─────▼─────┐          ┌───────▼──────┐    ┌───────▼──────┐
              │ PostgreSQL │          │  Redis/Celery │    │  Prometheus  │
              │ (results)  │          │ (batch jobs)  │    │  + Grafana   │
              └───────────┘          └──────────────┘    └──────────────┘
```

### Inference Stack

| Component | Layer | Notes |
|-----------|-------|-------|
| ONNX INT8 | Primary | Production — 185 ms p95 latency |
| ONNX FP32 | Fallback | Same model, no quantisation — 520 ms |
| Rule-based | Fallback | Keyword lexicon + context-window scoring — zero download |

The pipeline auto-selects: **ONNX INT8** → **ONNX FP32** → **Rule-based**. No external model downloads required.

---

## Features

### Web UI (HTMX + Jinja2)

- **Single Prediction** — Real-time aspect/sentiment analysis with inline text highlighting
- **Batch Processing** — CSV upload with drag-and-drop, progress bar, Chart.js visualisations
- **System Monitor** — Live health checks, performance metrics, endpoint activity log
- **CSRF Protected** — All form submissions protected via itsdangerous tokens
- **Dark Theme** — Material Design 3 colour system, responsive layout

### API (RESTful JSON)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/predict` | POST | Analyse a single review |
| `/batch` | POST | Upload CSV for bulk analysis |
| `/status/{job_id}` | GET | Check batch job progress |
| `/health` | GET | API health check |
| `/info` | GET | Model metadata |
| `/metrics` | GET | Prometheus metrics |
| `/docs` | GET | Swagger UI |

### ML Pipeline (DVC)

```bash
dvc pull       # Download datasets
dvc repro      # Reproduce preprocessing
dvc push       # Upload to remote storage
```

### Monitoring

- **Prometheus** metrics at `/metrics`
- **Grafana** dashboards for request volume, latency, error rate
- **Evidently** drift detection (`scripts/drift_monitor.py`)
- **MLflow** experiment tracking (`scripts/mlflow_ui.sh`)

---

## Development

### Run Tests

```bash
PYTHONPATH=. pytest tests/ -v
```

### Run Full Stack (Docker)

```bash
docker compose -f docker/docker-compose.yml up --build
```

Starts: API (8000), PostgreSQL, Redis, Celery worker, Prometheus (9090), Grafana (3001).

### Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Required | Description |
|----------|:--------:|-------------|
| `DATABASE_URL` | ✅ | PostgreSQL or SQLite connection string |
| `REDIS_URL` | ✅ | Redis connection for Celery |
| `CORS_ORIGINS` | ❌ | Allowed CORS origins (default: localhost) |
| `CSRF_SECRET` | ❌ | Secret for CSRF token signing |
| `MODEL_PATH` | ❌ | Path to ONNX model directory |
| `MODEL_SOURCE` | ❌ | `local` or `huggingface_hub` |

---

## Documentation

| Document | Contents |
|----------|----------|
| [API](docs/API.md) | Full API reference with schemas and examples |
| [Architecture](docs/ARCHITECTURE.md) | System design, data flow, deployment |
| [Deployment](docs/DEPLOYMENT.md) | Production setup, Docker, Railway |
| [Database](docs/DATABASE.md) | Schema, migrations, query patterns |
| [Security](docs/SECURITY.md) | Threat model, audit results, mitigations |
| [Tech Stack](docs/TECH_STACK.md) | Framework versions, rationale, trade-offs |
| [HTMX Migration](docs/HTMX_MIGRATION.md) | Notes on Streamlit → HTMX transition |

---

## License

MIT License. See [LICENSE](LICENSE) for details.
