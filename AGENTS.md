# Multilingual-Absa — Agent Instructions

## Project
Aspect-Based Sentiment Analysis (ABSA) on multilingual product reviews.
Supports English, Hindi, and Hinglish (code-mixed).

## Stack
- Model: XLM-RoBERTa (primary), IndicBERT (Hindi), exported to ONNX
- Fine-tuning: HuggingFace Transformers + PEFT/QLoRA
- Backend: FastAPI + Celery + Redis + PostgreSQL
- Frontend: React + Vite + Recharts + TailwindCSS
- MLOps: MLflow, DVC, Evidently AI, Prometheus + Grafana
- Deploy: Docker + Railway (API), Vercel (frontend), HuggingFace Hub (models)

## Project structure
multilingual-absa/
├── data/               # Raw + processed datasets (DVC tracked)
├── notebooks/          # EDA, training experiments
├── src/
│   ├── data/           # Preprocessing, language detection, tokenization
│   ├── models/         # Fine-tuning scripts, ONNX export
│   ├── evaluation/     # Metrics, confusion matrix, cross-lingual eval
│   └── utils/
├── api/                # FastAPI app, Celery tasks, DB models
├── dashboard/          # React frontend
├── docker/             # Dockerfiles, docker-compose
└── mlflow/             # MLflow tracking config

## Coding conventions
- Python 3.11+, type hints everywhere, Pydantic v2 for API schemas
- All training runs logged to MLflow with params + metrics + artifacts
- Dataset versions tracked with DVC
- Macro-F1 is the primary evaluation metric (not accuracy)
- ONNX export required before any model goes to the API

## ABSA task definition
- Stage 1: Aspect term extraction (token classification, BIO tagging)
- Stage 2: Per-aspect sentiment classification (positive / negative / neutral / conflict)
- Both stages compiled into a single ONNX graph

## Current phase
Week 1 — Project scaffold, data collection, EDA