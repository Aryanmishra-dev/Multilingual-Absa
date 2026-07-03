# Multilingual Aspect-Based Sentiment Analysis (ABSA)

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-00a393.svg)
![React](https://img.shields.io/badge/React-18-61dafb.svg)
![DVC](https://img.shields.io/badge/DVC-3.51.1-945dd6.svg)
![MLflow](https://img.shields.io/badge/MLflow-2.13.0-0194E2.svg)

A production-ready, highly optimized Aspect-Based Sentiment Analysis (ABSA) system designed to process multilingual product reviews in **English, Hindi, and Hinglish**. It accurately extracts aspects and classifies their underlying sentiments.

The system leverages state-of-the-art models like **XLM-RoBERTa** and **IndicBERT**, optimized using ONNX runtime, and includes a highly robust, zero-download, pure-Python rule-based fallback engine for instant inference.

## Key Features

- **Multilingual Support**: First-class support for English, Hindi, and code-mixed Hinglish.
- **Dual Inference Engine**:
  - **Neural Path**: Uses custom fine-tuned, INT8-quantized ONNX models (XLM-RoBERTa based) for extremely fast and accurate token classification and sequence classification.
  - **Rule-Based Fallback**: An instantaneous, pure-Python fallback leveraging a curated multi-lingual lexicon to handle aspect extraction and sentiment scoring without any heavy downloads.
- **Modern Tech Stack**: 
  - **Backend**: Asynchronous, high-performance API built with FastAPI.
  - **Frontend**: A responsive dashboard built with React and TailwindCSS. Features real-time predictions, batch analytics, and system monitoring.
- **MLOps Integrated**: Complete integration with DVC (Data Version Control) for pipeline reproducibility, MLflow for experiment tracking, and Evidently AI for data drift monitoring.
- **Scalable Architecture**: Support for async tasks via Celery + Redis, robust data storage via PostgreSQL, and metric exporting using Prometheus.

## Python-First Architecture

This repository is designed following a **Python-first paradigm**:
- **Python (67.5%)**: Handling all business logic, data processing, configuration, API routing, ML inference, and utility functions using FastAPI and Python data science libraries.
- **JavaScript/TypeScript (32.5%)**: Strictly limited to the frontend `dashboard/` directory, used *only* for the React UI, component rendering, browser events, and client-side state. 
- *Note: There is no backend or ML logic written in JavaScript.*

## Repository Structure

```text
Multilingual-Absa/
├── api/app/                # FastAPI backend and inference services
├── config/                 # Docker and application configuration files
├── dashboard/              # React frontend for inference & monitoring
├── data/                   # Dataset directory (DVC-tracked)
├── docs/                   # Extended documentation (architecture, ml, api)
├── ml/                     # ML training, notebooks, MLflow, and tracking
├── models/                 # Model artifacts (DVC-tracked)
├── monitoring/             # Monitoring configurations (Prometheus, Evidently)
├── scripts/                # Utility and automation scripts
├── src/                    # Core Machine Learning pipeline source code
├── tests/                  # Unit and integration test suite
├── dvc.yaml                # DVC pipeline orchestration
└── requirements.txt        # Python dependencies
```

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js (for Dashboard)
- Docker & Docker Compose (Optional, but recommended)

### 1. Local Setup

Clone the repository and install the backend dependencies:
```bash
git clone <repository-url>
cd Multilingual-Absa

# Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
pip install -r requirements.txt
```

Set up your environment variables:
```bash
cp .env.example .env
# Edit .env with your specific configurations
```

### 2. Run with Docker (Recommended)

The easiest way to get the entire stack (API, Dashboard, Redis, Postgres) running is via Docker Compose:
```bash
docker-compose -f deployment/docker/docker-compose.yml up --build
```

### 3. Manual ML Pipeline Execution (DVC)

To reproduce the ML pipeline or sync artifacts:
```bash
dvc pull         # Pull data/models from remote storage
dvc repro        # Run the full end-to-end ML training pipeline
dvc push         # Push newly generated artifacts to remote
```

### 4. Running the Application Locally

**Start the API Server:**
```bash
PYTHONPATH=. uvicorn api.app.main:app --reload --host 0.0.0.0 --port 8000
```
*API Documentation will be available at `http://localhost:8000/docs`.*

**Start the Dashboard:**
```bash
cd dashboard
npm install
npm run dev
```
*Access the dashboard at `http://localhost:5173`.*

## How it Works

1. **Prediction API**: When a review is submitted, the language is auto-detected.
2. **Inference**: The `ABSAPipeline` attempts to load INT8 quantized ONNX models for extraction and sentiment scoring. 
3. **Fallback Mechanism**: If the custom models are not downloaded, the engine automatically falls back to a dictionary/rule-based engine tailored for product reviews, guaranteeing zero downtime and instant availability.
4. **Monitoring**: All predictions are logged. Performance metrics and data drift are tracked via Evidently and Prometheus.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
