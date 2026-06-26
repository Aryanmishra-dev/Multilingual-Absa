# Multilingual-Absa

Aspect-Based Sentiment Analysis (ABSA) on multilingual product reviews. Supports English, Hindi, and Hinglish (code-mixed).

## Overview
Aspect-level sentiment analysis on multilingual product reviews. This project fine-tunes XLM-RoBERTa and IndicBERT models, exports them to ONNX for fast inference, and serves them via a FastAPI backend and a React dashboard.

## Tech Stack
- **Model:** XLM-RoBERTa (primary), IndicBERT (Hindi), exported to ONNX
- **Fine-tuning:** HuggingFace Transformers + PEFT/QLoRA
- **Backend:** FastAPI + Celery + Redis + PostgreSQL
- **Frontend:** React + Vite + Recharts + TailwindCSS
- **MLOps:** MLflow, DVC, Evidently AI, Prometheus + Grafana
- **Deploy:** Docker + Railway (API), Vercel (frontend), HuggingFace Hub (models)

## ABSA Task Definition
- **Stage 1:** Aspect term extraction (token classification, BIO tagging)
- **Stage 2:** Per-aspect sentiment classification (positive / negative / neutral / conflict)
- Both stages compiled into a single ONNX graph for efficient serving.

## Project Structure
```text
multilingual-absa/
├── data/               # Raw + processed datasets (DVC tracked)
├── notebooks/          # EDA, training experiments
├── src/
│   ├── data/           # Preprocessing, language detection, tokenization
│   ├── models/         # Fine-tuning scripts, ONNX export
│   ├── evaluation/     # Metrics, confusion matrix, cross-lingual eval
│   └── utils/          # Shared utilities
├── api/                # FastAPI app, Celery tasks, DB models
├── dashboard/          # React frontend
├── docker/             # Dockerfiles, docker-compose
└── mlflow/             # MLflow tracking config
```

## Setup & Installation
```bash
# Clone the repository
git clone https://github.com/your-org/multilingual-absa.git
cd multilingual-absa

# Install Python dependencies
pip install -r requirements.txt

# Pull DVC tracked data
dvc pull
```

## Coding Conventions
- Python 3.11+, type hints everywhere, Pydantic v2 for API schemas
- All training runs logged to MLflow with params, metrics, and artifacts
- Dataset versions tracked with DVC
- Macro-F1 is the primary evaluation metric (not accuracy)
- ONNX export required before any model goes to the API

## Current Phase
**Week 1** — Project scaffold, data collection, EDA
