# Technology Stack — Multilingual ABSA

## Core Technologies

| Technology | Version | Purpose | Where Used |
|------------|---------|---------|------------|
| **Python** | 3.11+ | Runtime | All backend/ML code |
| **FastAPI** | 0.111.0 | REST API framework | `api/` routes and middleware |
| **Uvicorn** | 0.29.0 | ASGI server | API entry point |
| **React** | 18.2.0 | Frontend framework | `dashboard/src/` |
| **Vite** | 5.0.0 | Build tool | `dashboard/vite.config.js` |
| **TailwindCSS** | 3.3.5 | CSS framework | `dashboard/src/index.css` |
| **PostgreSQL** | 16 (alpine) | Production database | Docker Compose |
| **SQLite** | (built-in) | Development database | `absa.db` |
| **Redis** | 7 (alpine) | Celery broker + cache | `api/tasks/` |
| **Docker** | 27.x | Containerization | `config/docker/` |
| **Docker Compose** | 3.8+ | Orchestration | `config/docker/docker-compose.yml` |

## ML / AI Stack

| Technology | Version | Purpose | Where Used |
|------------|---------|---------|------------|
| **PyTorch** | 2.3.0 | Deep learning framework | `src/models/` training |
| **Transformers** | 4.39.3 | Model zoo, training, tokenization | All ML scripts |
| **XLM-RoBERTa** | base | Multilingual encoder | `FacebookAI/xlm-roberta-base` |
| **ONNX Runtime** | 1.18.0 | Production inference | `api/services/absa_pipeline.py` |
| **Optimum** | 1.19.0 | ONNX export bridge | `src/models/export_onnx.py` |
| **optimum-onnx** | (bundled) | ONNX runtime models | `ORTModelForTokenClassification`, `ORTModelForSequenceClassification` |
| **PEFT** | 0.10.0 | Parameter-efficient fine-tuning | `src/models/train_qlora.py` (LoRA) |
| **scikit-learn** | 1.4.2 | Metrics + baseline | `src/models/baseline.py`, `train_sentiment.py` |
| **Datasets** | 2.19.0 | Data loading | `src/data/hf_dataset.py` |
| **seqeval** | 1.2.2 | BIO tagging evaluation | `src/models/train_aspect_extraction.py` |
| **fasttext-predict** | 0.9.2.4 | Language identification | `src/data/lang_detect.py`, `api/services/lang_service.py` |
| **indic-nlp-library** | (git) | Devanagari transliteration | `src/data/transliterate.py` |
| **nlpaug** | 1.1.11 | Text augmentation | `src/data/augmentation.py` |

## MLOps Stack

| Technology | Version | Purpose | Where Used |
|------------|---------|---------|------------|
| **MLflow** | 2.13.0 | Experiment tracking | `src/training/mlflow_utils.py`, all `src/models/` |
| **DVC** | 3.51.1 | Data version control | `config/dvc.yaml`, `.dvc/` |
| **Evidently AI** | 0.4.30 | Data drift monitoring | `scripts/drift_monitor.py` |
| **Prometheus** | latest | Metrics collection | `monitoring/prometheus.yml` |
| **Grafana** | latest | Dashboard visualization | `monitoring/grafana/dashboards/` |
| **prometheus-fastapi-instrumentator** | 7.0.0 | Metrics middleware | `api/middleware/metrics.py` |

## API / Backend Libraries

| Technology | Version | Purpose |
|------------|---------|---------|
| **Pydantic** | 2.7.1 | Request/response schema validation |
| **SQLAlchemy** | (via psycopg2) | ORM |
| **psycopg2-binary** | 2.9.9 | PostgreSQL driver |
| **Celery** | 5.4.0 | Async task queue |
| **python-dotenv** | 1.0.1 | Environment variable loading |
| **python-multipart** | 0.0.9 | File upload parsing |
| **NumPy** | 1.26.4 | Numerical computing |
| **Pandas** | 2.2.2 | Data manipulation |

## Frontend Libraries

| Technology | Version | Purpose |
|------------|---------|---------|
| **@tanstack/react-query** | 5.0.0 | Server state, caching, polling |
| **react-router-dom** | 6.20.0 | Client routing |
| **react-hot-toast** | 2.4.1 | Toast notifications |
| **react-dropzone** | 14.2.3 | File upload drag-and-drop |
| **axios** | 1.6.0 | HTTP client with retry |
| **recharts** | 2.10.0 | Charts (line, bar, pie/donut) |
| **lucide-react** | 0.290.0 | Icons |
| **autoprefixer** | 10.4.16 | CSS vendor prefixes |
| **postcss** | 8.4.31 | CSS processor |

## Infrastructure / Deployment

| Technology | Purpose |
|------------|---------|
| **Docker** (multi-stage) | Build optimization |
| **Nginx (alpine)** | SPA serving + API proxy |
| **Railway** | API + worker cloud hosting |
| **Vercel** | Frontend SPA hosting |
| **HuggingFace Hub** | Model storage/pull |

## Version Compatibility Matrix

| Package | Python | PyTorch | ONNX Runtime |
|---------|--------|---------|--------------|
| transformers 4.39.3 | 3.8+ | 1.11+ | — |
| optimum 1.19.0 | 3.8+ | 1.13+ | 1.15+ |
| onnxruntime 1.18.0 | 3.8+ | — | — |
| peft 0.10.0 | 3.8+ | 2.0+ | — |
| mlflow 2.13.0 | 3.8+ | — | — |
| dvc 3.51.1 | 3.8+ | — | — |
| evidently 0.4.30 | 3.8+ | — | — |
| fastapi 0.111.0 | 3.8+ | — | — |
| celery 5.4.0 | 3.8+ | — | — |
