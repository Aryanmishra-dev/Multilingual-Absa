# Architecture Research

**Domain:** Multilingual Aspect-Based Sentiment Analysis (ABSA)
**Researched:** 2026-06-22
**Confidence:** HIGH

## Standard Architecture

### System Overview

The canonical multilingual ABSA system uses a **two-stage pipeline** with a transformer backbone, separated training/inference workflows, and an async web serving layer.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                    │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────────┐   │
│  │  Raw Reviews   │  │  Labeled ABSA  │  │  Preprocessed / Tokenized  │   │
│  │  (JSON/CSV)    │  │  Datasets      │  │  Datasets (DVC-tracked)    │   │
│  └───────┬────────┘  │  (SemEval,     │  └──────────────┬─────────────┘   │
│          │           │   M-ABSA,      │                 │                   │
│          │           │   custom)      │                 │                   │
│          │           └───────┬────────┘                 │                   │
│          └───────────────────┼──────────────────────────┘                   │
│                              ▼                                              │
│                    ┌──────────────────┐                                     │
│                    │  Language        │                                     │
│                    │  Detection       │  (auto-detect EN/HI/Hinglish)       │
│                    └──────────────────┘                                     │
├──────────────────────────────────────────────────────────────────────────┤
│                           TRAINING LAYER                                    │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  Fine-Tuning Pipeline (HuggingFace Transformers + PEFT/QLoRA)      │    │
│  │                                                                    │    │
│  │  ┌─────────────────────┐    ┌─────────────────────────────┐        │    │
│  │  │ Stage 1: ASE Model  │    │ Stage 2: ABSC Model         │        │    │
│  │  │ XLMRobertaForToken  │    │ XLMRobertaForSequence       │        │    │
│  │  │ Classification      │    │ Classification              │        │    │
│  │  │ (BIO tagging)       │    │ (sentiment per aspect)      │        │    │
│  │  └──────────┬──────────┘    └──────────────┬──────────────┘        │    │
│  │             │                              │                        │    │
│  │             ▼                              ▼                        │    │
│  │  ┌────────────────────────────────────────────────────────────┐    │    │
│  │  │              Combined ONNX Graph Export                     │    │    │
│  │  │  (single .onnx file with both heads)                       │    │    │
│  │  └──────────────────────────┬─────────────────────────────────┘    │    │
│  │                             │                                       │    │
│  │                             ▼                                       │    │
│  │  ┌────────────────────────────────────────────────────────────┐    │    │
│  │  │  MLflow Tracking + Model Registry                          │    │    │
│  │  │  (params, metrics, artifacts, model versioning)            │    │    │
│  │  └────────────────────────────────────────────────────────────┘    │    │
│  └────────────────────────────────────────────────────────────────────┘    │
├──────────────────────────────────────────────────────────────────────────┤
│                           INFERENCE LAYER                                  │
│  ┌─────────┐     ┌──────────┐     ┌──────────────┐     ┌──────────────┐   │
│  │ FastAPI │────▶│  Celery  │────▶│  ONNX Runtime │────▶│  PostgreSQL  │   │
│  │ Gateway │     │  Worker  │     │  Inference    │     │  (results)   │   │
│  └────┬────┘     │ (Redis   │     └──────────────┘     └──────────────┘   │
│       │          │  Broker) │                                              │
│       │          └──────────┘                                              │
│       │                                                                     │
│       │          ┌──────────┐                                              │
│       └──────────│  Celery  │                                              │
│                  │  Beat    │  (scheduled maintenance tasks)               │
│                  └──────────┘                                              │
├──────────────────────────────────────────────────────────────────────────┤
│                           MONITORING LAYER                                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────────┐   │
│  │  Prometheus│  │  Grafana   │  │  Evidently │  │  MLflow UI         │   │
│  │  (metrics) │  │ (dashboards)│  │  AI (drift)│  │  (experiments)     │   │
│  └────────────┘  └────────────┘  └────────────┘  └────────────────────┘   │
├──────────────────────────────────────────────────────────────────────────┤
│                           PRESENTATION LAYER                               │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  React + Vite + TailwindCSS + Recharts                             │    │
│  │  (dashboard with per-aspect sentiment breakdowns,                  │    │
│  │   trend analysis, batch inference UI)                              │    │
│  └────────────────────────────────────────────────────────────────────┘    │
├──────────────────────────────────────────────────────────────────────────┤
│                           DEPLOYMENT LAYER                                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │  Docker    │  │  Railway   │  │  Vercel        │  │  HuggingFace   │   │
│  │  Compose   │  │  (API)     │  │  (Frontend)    │  │  Hub (models)  │   │
│  └────────────┘  └────────────┘  └────────────────┘  └────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

### Two-Stage ABSA Pipeline (The Core Pattern)

This is the canonical decomposition of ABSA into two sequential sub-tasks:

```
Raw Review Text
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 1: Aspect Term Extraction (ASE)                       │
│                                                             │
│ Token Classification with XLM-RoBERTa                        │
│ Scheme: BIO tagging (B-ASP, I-ASP, O)                       │
│                                                             │
│ Input:  "The battery life is great but the screen is dim"    │
│ Output: [O] [B-ASP] [I-ASP] [O] [O] [O] [O] [B-ASP] [O]    │
│                                                             │
│ Extracted: "battery life", "screen"                          │
└───────────────────────┬─────────────────────────────────────┘
                        │ (text + list of aspect spans)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 2: Per-Aspect Sentiment Classification (ABSC)         │
│                                                             │
│ Sequence Classification with XLM-RoBERTa                    │
│                                                             │
│ For each (review_text, aspect_term) pair:                   │
│   "The battery life is great but the screen is dim" +        │
│   "battery life" → {label: "positive", score: 0.95}         │
│   "The battery life is great but the screen is dim" +        │
│   "screen"      → {label: "negative", score: 0.88}          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Structured JSON Output                                      │
│ {                                                           │
│   "review_id": "r123",                                      │
│   "language": "en",                                         │
│   "aspects": [                                              │
│     {"term": "battery life", "sentiment": "positive",       │
│      "score": 0.95, "span": [4, 6]},                        │
│     {"term": "screen", "sentiment": "negative",             │
│      "score": 0.88, "span": [11, 11]}                       │
│   ]                                                         │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Language Detector | Detect review language (EN/HI/Hinglish) to route/flag | FastText language detection or XLM-RoBERTa-based lang ID |
| Data Preprocessor | Tokenize, align BIO labels, handle subword splitting | HuggingFace `XLMRobertaTokenizerFast`, custom alignment logic |
| ASE Model (Stage 1) | Token-level BIO tagging → extract aspect spans | `XLMRobertaForTokenClassification` with linear classification head |
| ABSC Model (Stage 2) | Sequence classification per (text, aspect) pair | `XLMRobertaForSequenceClassification` with 4 output classes |
| Combined ONNX Graph | Both stages merged into single ONNX model file | `torch.onnx.export` with custom wrapper exporting both heads |
| ONNX Runtime Session | Inference execution using ONNX Runtime | `onnxruntime.InferenceSession` with CPU/CUDA providers |
| FastAPI Gateway | REST API, validation, auth, request routing | FastAPI app with Pydantic v2 schemas |
| Celery Worker | Async model inference task execution | Celery worker process loading ONNX model into memory |
| Redis Broker | Task queue between FastAPI and Celery | Redis instance (Celery broker + result backend) |
| PostgreSQL | Persist inference results, user data, model metadata | SQLAlchemy + asyncpg |
| MLflow Tracker | Log parameters, metrics, artifacts per training run | `mlflow.transformers.autolog()`, custom callbacks |
| DVC | Version datasets and preprocessing outputs | `dvc add`, `dvc push` to remote storage |
| React Dashboard | Visualize per-aspect sentiment breakdowns, trends | React + Vite + Recharts + TailwindCSS |
| Prometheus + Grafana | API performance metrics, request rates, latency | prometheus_fastapi_instrumentator |
| Evidently AI | Model performance monitoring, data drift detection | Evidently AI reports (tabular + NLP features) |
| Docker Compose | Local development orchestration | docker-compose.yml with all services |

### Multilingual Considerations

**Language handling strategy:**

1. **No separate `lang` tensors** — XLM-RoBERTa auto-detects language from input IDs. Unlike some XLM models, it doesn't need `lang` tokens.
2. **Code-mixed input (Hinglish)** — Use the same tokenizer; XLM-RoBERTa handles mixed scripts via SentencePiece BPE. No special pre-segmentation needed.
3. **IndicBERT fallback** — For Hindi-only runs, IndicBERT (from AI4Bharat) may capture Indic script patterns better. Train as `AutoModelForTokenClassification` / `AutoModelForSequenceClassification`, same interface.
4. **Translation-based data augmentation** — For Hindi/Hinglish where labeled data is scarce, use machine translation of English ABSA datasets (SemEval, M-ABSA) with bilingual lexicon alignment for aspect terms.

## Recommended Project Structure

```
multilingual-absa/
│
├── data/                            # DVC-tracked data
│   ├── raw/                         # Original datasets (SemEval, M-ABSA, custom)
│   │   ├── semeval2014/             # English: restaurant, laptop
│   │   ├── m-absa/                  # Multilingual (21 languages)
│   │   └── custom/                  # Hindi/Hinglish scraped data
│   ├── processed/                   # Preprocessed, tokenized, ready for training
│   │   ├── ase/                     # Token classification format
│   │   └── absa/                    # Sequence pair classification format
│   └── external/                    # Downloaded reference data
│
├── notebooks/                       # Jupyter notebooks for exploration
│   ├── 01-eda.ipynb                 # Exploratory data analysis
│   ├── 02-data-prep.ipynb           # Data preprocessing and alignment
│   ├── 03-finetune-ase.ipynb        # ASE model fine-tuning
│   ├── 04-finetune-absa.ipynb       # ABSC model fine-tuning
│   └── 05-onnx-export.ipynb         # ONNX export and validation
│
├── src/
│   ├── data/                        # Data processing pipeline
│   │   ├── __init__.py
│   │   ├── loader.py                # Dataset loading (SemEval, M-ABSA, custom)
│   │   ├── preprocessor.py          # Tokenization, BIO alignment, subword handling
│   │   ├── language_detector.py     # Language detection for routing
│   │   ├── augmenter.py             # Translation-based augmentation
│   │   └── splitter.py              # Train/val/test splitting with stratification
│   │
│   ├── models/                      # Model training and export
│   │   ├── __init__.py
│   │   ├── ase_trainer.py           # Aspect extraction training loop
│   │   ├── absa_trainer.py          # Sentiment classification training loop
│   │   ├── combined_graph.py        # ONNX combined graph builder
│   │   ├── onnx_export.py           # ONNX export utilities
│   │   └── inference.py             # ONNX Runtime inference session wrapper
│   │
│   ├── evaluation/                  # Metrics and evaluation
│   │   ├── __init__.py
│   │   ├── metrics.py               # Macro-F1, precision, recall, confusion matrix
│   │   ├── cross_lingual_eval.py     # Per-language evaluation breakdown
│   │   └── error_analysis.py         # Error categorization for model debugging
│   │
│   └── utils/                       # Shared utilities
│       ├── __init__.py
│       ├── config.py                # Central configuration (Pydantic Settings)
│       ├── logging.py               # Logging setup
│       └── mlflow_utils.py          # MLflow integration helpers
│
├── api/                             # FastAPI inference API + Celery
│   ├── __init__.py
│   ├── main.py                      # FastAPI app, routes, middleware
│   ├── config.py                    # API configuration
│   ├── models/                      # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── request.py               # Inference request schemas
│   │   └── response.py              # Inference response schemas
│   ├── routers/                     # API route handlers
│   │   ├── __init__.py
│   │   ├── inference.py             # POST /predict, /predict-batch
│   │   ├── health.py                # GET /health, /ready
│   │   └── feedback.py              # POST /feedback (human-in-the-loop)
│   ├── services/                    # Business logic
│   │   ├── __init__.py
│   │   ├── inference_service.py     # Orchestrates ASE → ABSC pipeline
│   │   ├── model_cache.py           # ONNX model lifecycle management
│   │   └── feedback_service.py      # Human feedback collection
│   ├── workers/                     # Celery task definitions
│   │   ├── __init__.py
│   │   ├── celery_app.py            # Celery app configuration
│   │   └── tasks.py                 # async_inference, batch_inference tasks
│   ├── db/                          # Database layer
│   │   ├── __init__.py
│   │   ├── session.py               # SQLAlchemy async session
│   │   ├── models.py                # ORM models (InferenceResult, Feedback, etc.)
│   │   └── migrations/              # Alembic migrations
│   └── monitoring/                  # Observability
│       ├── __init__.py
│       └── metrics.py               # Prometheus metrics setup
│
├── dashboard/                       # React frontend
│   ├── src/
│   │   ├── components/              # Reusable UI components
│   │   │   ├── Layout/
│   │   │   ├── SentimentChart/      # Recharts-based visualizations
│   │   │   ├── AspectBreakdown/     # Per-aspect sentiment table
│   │   │   ├── BatchUpload/         # CSV batch inference upload
│   │   │   └── ModelSelector/       # Model version picker
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx        # Main analytics dashboard
│   │   │   ├── SingleInference.tsx  # Single review analysis
│   │   │   ├── BatchInference.tsx   # Batch upload and results
│   │   │   └── ModelComparison.tsx  # Compare model versions
│   │   ├── hooks/                   # Custom React hooks
│   │   ├── services/                # API client layer
│   │   └── App.tsx                  # Root component
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── docker/                          # Container definitions
│   ├── Dockerfile.api               # FastAPI + Celery worker image
│   ├── Dockerfile.frontend          # Vercel-compatible React build
│   └── docker-compose.yml           # Local dev: all services
│
├── mlflow/                          # MLflow config
│   └── config.yaml                  # MLflow tracking server config
│
├── dvc.yaml                         # DVC pipeline definition
├── dvc.lock                         # DVC lockfile
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Project metadata
└── setup.cfg
```

### Structure Rationale

- **`src/data/` separated from `src/models/`:** Data preprocessing is computationally independent from model training. This split lets you preprocess once and train many model variants. DVC tracks data/ directory, not src/.
- **`api/` as top-level package:** The API is the production entrypoint. It has its own dependencies and lifecycle (Docker image, health checks, scaling) separate from training. Keeping it at the top level avoids importing training code into production.
- **`api/models/` (Pydantic) vs `src/models/` (ML):** The two are completely separate. Pydantic schemas define the HTTP contract; src/models/ defines the neural architecture. This prevents accidental import of torch/transformers into the API process.
- **`api/workers/` separated from `api/routers/`:** Celery workers are separate processes with their own lifecycle. The boundary between HTTP handler and task producer is explicit. Workers load the ONNX model once at startup — never in the FastAPI process.
- **`notebooks/` is linear, numbered:** Each notebook maps to one pipeline step. This enforces a reproducible sequence: EDA → prep → train ASE → train ABSC → export. Notebooks are not for production code, but for exploration and visualization during development.

## Data Flow

### Request Flow (Inference Path)

```
HTTP Request
    │
    ▼
┌─────────────────────────────────────────────────┐
│ 1. FastAPI Router (/predict)                     │
│    • Validate request (Pydantic)                  │
│    • Detect language                              │
│    • Rate limiting check                          │
│    • Return task_id immediately                   │
│    • Enqueue Celery task with review text          │
└──────────────────────┬──────────────────────────┘
                       │ task_id
                       ▼
┌─────────────────────────────────────────────────┐
│ 2. Redis Broker                                  │
│    • Persists task in queue                       │
│    • Celery worker picks it up asynchronously     │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│ 3. Celery Worker Process                         │
│    • Load ONNX model into memory (once)           │
│    • Create ONNX Runtime session                  │
│    • Tokenize input text                          │
│    • Run Stage 1: ASE inference (token tags)      │
│    • Decode BIO tags → extract aspect spans       │
│    • For each aspect span:                        │
│        • Create (text, aspect) sentence pair      │
│        • Run Stage 2: ABSC inference              │
│        • Get sentiment + confidence score          │
│    • Aggregate results                            │
│    • Store result in PostgreSQL                    │
│    • Return result to Redis result backend         │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│ 4. Client Polls /result/{task_id}                │
│    • FastAPI checks Celery AsyncResult            │
│    • Returns structured JSON when ready           │
│    • Response:                                    │
│      {                                            │
│        "status": "SUCCESS",                       │
│        "language": "hi",                          │
│        "aspects": [...],                          │
│        "processing_time_ms": 487                  │
│      }                                            │
└─────────────────────────────────────────────────┘
```

### Training Data Flow

```
Raw Datasets (SemEval, M-ABSA, Custom)
    │
    ▼
┌─────────────────────────────────────────────────┐
│ Data Preprocessing Pipeline (src/data/)          │
│                                                   │
│ 1. Load raw XML/JSON/CSV                          │
│ 2. Normalize to unified schema                    │
│ 3. Translate augmentation (EN→HI/Hinglish)         │
│ 4. Language detection & tagging                   │
│ 5. Tokenization + BIO label alignment             │
│    (handle subword splits: "battery" → "batter"   │
│     + "##y" → both get B-ASP/I-ASP)               │
│ 6. Create train/val/test splits                   │
│    (stratified by language + aspect category)      │
│ 7. Save as DVC-tracked processed datasets          │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│ Stage 1 Training: ASE Model                      │
│                                                   │
│ Model: XLMRobertaForTokenClassification           │
│ Labels: BIO tags (O, B-ASP, I-ASP)                │
│ Loss: CrossEntropyLoss (ignore index=-100)         │
│ Metrics: Token-level F1, Span-level F1             │
│ Tracking: MLflow (params, metrics, model artifact)  │
│ Output: Fine-tuned ASE checkpoint                  │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│ Stage 2 Training: ABSC Model                     │
│                                                   │
│ Model: XLMRobertaForSequenceClassification        │
│ Input: [CLS] review text [SEP] aspect term [SEP]  │
│ Classes: positive, negative, neutral, conflict     │
│ Loss: CrossEntropyLoss                            │
│ Metrics: Macro-F1, per-class F1                   │
│ Tracking: MLflow (params, metrics, model artifact)  │
│ Output: Fine-tuned ABSC checkpoint                │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│ Combined ONNX Export                              │
│                                                   │
│ 1. Load both fine-tuned checkpoints               │
│ 2. Create combined graph:                          │
│    - Shared XLM-RoBERTa encoder                    │
│    - Two output heads (token + sequence)            │
│ 3. torch.onnx.export with dynamic axes             │
│ 4. Validate with ONNX Runtime                      │
│ 5. Compare inference output parity with PyTorch     │
│ 6. Register in MLflow Model Registry               │
│ 7. Push to HuggingFace Hub (optional)               │
└─────────────────────────────────────────────────┘
```

### ONNX Combined Graph Architecture

The key architectural decision is compiling both stages into **a single ONNX graph**. This is what separates a research pipeline from a production system.

```
┌─────────────────────────────────────────────────────────┐
│              Combined ONNX Graph                          │
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │          XLM-RoBERTa Encoder (shared)            │   │
│  │  (12 transformer layers, 768 hidden, 12 heads)    │   │
│  └──────────────┬───────────────────┬───────────────┘   │
│                 │                   │                     │
│                 ▼                   ▼                     │
│  ┌──────────────────────┐  ┌──────────────────┐         │
│  │  Token Classification │  │  Sequence Class.  │         │
│  │  Head                 │  │  Head              │         │
│  │                       │  │                    │         │
│  │  Linear(768, 3)       │  │  Linear(768, 4)    │         │
│  │  softmax per token    │  │  softmax per seq   │         │
│  │  → BIO tag probs      │  │  → sentiment probs │         │
│  └──────────┬───────────┘  └──────────┬───────────┘         │
│             │                          │                     │
└─────────────┼──────────────────────────┼─────────────────────┘
              │                          │
              ▼                          ▼
        Token-level tags           Sentence-level
        (BIO scheme)               sentiment per aspect
```

**Why combined graph?**
- Single `model.onnx` file to deploy, version, and monitor
- No coordination between separate ASE/ABSC ONNX files
- Shared encoder computation (tokenize once, encode once per stage 1 pass)
- Lower latency than two separate ONNX sessions
- Simpler Docker image (one model to download, not two)

**Nuance:** The combined graph is used for **single-aspect** inference where you know the aspect at graph-input time (used during stage 2 of pipeline). For batch/demo, you can also run just the token head separately and call the sequence head in a loop.

### Inference Data Transformations

```
Text Input: "बैटरी लाइफ बहुत अच्छी है"
    │
    ▼ Tokenize (XLMRobertaTokenizerFast)
tokenized: [0, 392, 12345, 6789, 23456, 7890, 34567, 2]
           [CLS] बैटरी  लाइफ   बहुत   अच्   ##छी   है    [SEP]
    │
    ▼ Stage 1: Token Classification Head
logits:    [0.1, 0.8, 0.9, 0.1, 0.1, 0.1, 0.1, 0.1]  (B-ASP scores)
           [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]  (I-ASP scores)
           [0.8, 0.1, 0.1, 0.8, 0.8, 0.8, 0.8, 0.8]  (O scores)
    │
    ▼ Decode BIO tags
tags:      [O, B-ASP, I-ASP, O, O, O, O, O]
    │
    ▼ Merge subwords, extract spans
aspects: ["बैटरी लाइफ"]  (battery life)
    │
    ▼ For each aspect, create sentence pair:
pair: "[CLS] बैटरी लाइफ बहुत अच्छी है [SEP] बैटरी लाइफ [SEP]"
    │
    ▼ Stage 2: Sequence Classification Head
logits: [0.02, 0.95, 0.01, 0.02]  →  positive (label 1)
    │
    ▼ Package result
{"aspects": [{"term": "बैटरी लाइफ", "sentiment": "positive", "score": 0.95}]}
```

### Feedback Loop (Human-in-the-Loop)

```
User sees prediction → User corrects via UI → Feedback stored in PostgreSQL
    │
    ▼
Periodic retraining dataset enriched with corrected labels
    │
    ▼
Model v2 fine-tuned with augmented training data
    │
    ▼
New ONNX exported, registered in MLflow, promoted to production
```

## Architectural Patterns

### Pattern 1: Two-Stage Pipeline with Cascading Errors

**What:** Decompose ABSA into (1) aspect extraction via token classification and (2) per-aspect sentiment via sequence classification. Stage 1 output feeds Stage 2 input.

**When to use:** Always. This is the canonical ABSA decomposition. Joint models exist (unified tagging schemes like ASTE-RE), but they're harder to train, harder to export to ONNX, and don't usually outperform the two-stage pipeline in multilingual settings.

**Trade-offs:**
- **Pro:** Each stage can be independently fine-tuned, evaluated, and improved
- **Pro:** Stage 2 can use different architectures per aspect type
- **Con:** Errors from Stage 1 cascade to Stage 2 (missed aspect → no sentiment predicted)
- **Con:** Higher total inference latency than a joint model

**Mitigation for cascading errors:**
- Add `[NONE]` class with higher threshold in Stage 1 to reduce false negatives
- Train Stage 1 with strict span-level F1 monitoring (not token-level)
- Consider top-K aspect extraction (extract more candidates, let Stage 2 filter)

### Pattern 2: API Gateway + Worker Pool Decoupling

**What:** FastAPI handles HTTP concerns (validation, auth, routing) and immediately returns a task ID. Celery workers asynchronously run inference. Client polls for result.

**When to use:** When inference latency exceeds acceptable API response time (>1-2s for transformer models, especially on CPU). Essential for ONNX Runtime inference on CPU or when GPU is shared among workers.

**Trade-offs:**
- **Pro:** API remains responsive under load — never blocks on inference
- **Pro:** Workers can scale independently (GPU pool, CPU pool)
- **Pro:** Retry logic and dead-letter queues for failed inferences
- **Con:** Client must poll or use webhooks — not suitable for synchronous use cases
- **Con:** Extra infrastructure (Redis, worker processes)

**Implementation pattern (FastAPI → Celery bridge):**

```python
# api/routers/inference.py
@router.post("/predict", status_code=202)
async def predict(request: InferenceRequest, background_tasks: BackgroundTasks):
    # Validate, then enqueue
    task = infer_review.delay(request.text, request.model_version)
    return {
        "task_id": task.id,
        "status": "PENDING",
        "poll_url": f"/result/{task.id}"
    }

@router.get("/result/{task_id}")
async def get_result(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    if result.state == "PENDING":
        return {"status": "PENDING"}
    elif result.state == "FAILURE":
        return {"status": "FAILURE", "error": str(result.info)}
    return {"status": "SUCCESS", "result": result.result}
```

### Pattern 3: Model-as-Cache (Warm Start)

**What:** ONNX model loaded once into process memory at Celery worker startup. Each worker holds the model for its lifetime. Model version is controlled via environment variable or MLflow registry lookup.

**When to use:** Always for production. Avoids loading model per-request (order-of-magnitude latency improvement).

**Trade-offs:**
- **Pro:** ~2-3s startup cost once, then ~100-500ms per inference
- **Pro:** Version pinning via environment means canary deploys (some workers with v2, some with v1)
- **Con:** Rolling model updates require worker restarts

```python
# api/workers/tasks.py
from celery import Celery
from src.models.inference import ONNXInferenceEngine

celery_app = Celery("absa", broker="redis://redis:6379/0")

# Global singleton — loaded once per worker process
_model_engine = None

def get_engine():
    global _model_engine
    if _model_engine is None:
        model_path = os.environ.get("MODEL_PATH", "/models/combined.onnx")
        _model_engine = ONNXInferenceEngine(model_path)
    return _model_engine

@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def infer_review(self, text: str, model_version: str = "latest"):
    engine = get_engine()
    try:
        result = engine.predict(text)
        return result
    except Exception as exc:
        raise self.retry(exc=exc)
```

### Pattern 4: Subword-Aware BIO Alignment

**What:** XLM-RoBERTa uses SentencePiece BPE, which can split a word into multiple subword tokens. The BIO labeling must be aligned: if "battery" is split into "batter" + "##y", both subword tokens should carry B-ASP and I-ASP respectively (not both B-ASP).

**When to use:** Required for any token classification task with subword tokenizers. Not optional.

```python
# src/data/preprocessor.py
def align_labels_with_tokens(labels, word_ids):
    """
    word_ids maps each token to the original word index.
    Labels are per original word. Align to per-token.
    For subwords of an aspect word, first subword = B-ASP, rest = I-ASP.
    """
    aligned = []
    previous_word_idx = None
    for word_idx in word_ids:
        if word_idx is None:
            aligned.append(-100)  # special tokens ignored in loss
        elif word_idx != previous_word_idx:
            aligned.append(labels[word_idx])  # B-ASP or O
        else:
            # Same word — if label is B-ASP, subsequent subwords become I-ASP
            label = labels[word_idx]
            if label == "B-ASP":
                aligned.append("I-ASP")
            else:
                aligned.append(label)
        previous_word_idx = word_idx
    return aligned
```

### Pattern 5: Metric-Driven Evaluation

**What:** Macro-F1 is the primary metric, computed as span-level F1 for ASE (exact boundary match required) and per-class F1 for ABSC. Evaluate per-language to detect cross-lingual performance gaps.

**When to use:** Always. ABSA datasets are imbalanced (more positive/negative than neutral/conflict). Accuracy is misleading. Span-level metrics are stricter than token-level.

**Trade-offs:**
- **Pro:** Macro-F1 treats all classes equally regardless of frequency
- **Pro:** Span-level F1 catches boundary errors (partial matches don't count)
- **Con:** Harder to optimize for in training (need to monitor early stopping on macro-F1, not loss)
- **Con:** Span-level metrics require exact match — might be too strict for valid partial matches

## Anti-Patterns

### Anti-Pattern 1: PyTorch in Production

**What people do:** Deploy the raw PyTorch model into the FastAPI service, calling `model.generate()` or `model(**inputs)` directly.

**Why it's wrong:** PyTorch is a training framework, not an inference runtime. Issues: (1) 2-5x slower than ONNX Runtime on CPU, (2) requires CUDA/cuDNN in the production image (3GB+), (3) harder to version, (4) security surface area (arbitrary code execution via pickle), (5) memory fragmentation over time.

**Do this instead:** Export to ONNX once, validate output parity with PyTorch, deploy only `onnxruntime` in production. The ONNX Runtime image is ~200MB vs PyTorch's ~3GB.

### Anti-Pattern 2: Loading Model Per Request

**What people do:** `torch.load()` or `InferenceSession()` inside each request handler.

**Why it's wrong:** Model loading is 2-10s per request. Completely destroys throughput. Also wastes memory (each request gets a fresh copy).

**Do this instead:** Load once at worker startup (singleton or module-level initialization). Use Celery process-per-worker so each process holds exactly one model instance.

### Anti-Pattern 3: Training ASE and ABSC Independently (in silos)

**What people do:** Fine-tune ASE and ABSC separately without considering the combined pipeline performance.

**Why it's wrong:** A great ASE model that misses 5% of aspects will cap your end-to-end performance regardless of how good your ABSC model is. The pipeline is only as strong as its weakest stage.

**Do this instead:** Evaluate end-to-end span-level F1 + sentiment accuracy jointly. Track a combined "end-to-end Macro-F1" metric. Set ASE accuracy targets before optimizing ABSC.

### Anti-Pattern 4: Ignoring Subword Tokenization in BIO Labels

**What people do:** Assign the same label to all subword tokens of a word (e.g., both "batter" and "##y" get B-ASP).

**Why it's wrong:** The model learns wrong boundary patterns. During inference, it might predict B-ASP for any subword, leading to duplicated or overlapping aspect spans. Evaluation metrics break.

**Do this instead:** Always use the alignment function (Pattern 4 above). Validate alignment by reconstructing spans from predictions and checking against ground truth.

### Anti-Pattern 5: Using Accuracy for ABSA

**What people do:** Report accuracy on the 4-class sentiment (positive/negative/neutral/conflict).

**Why it's wrong:** The "neutral" class typically has <5% of examples. A model predicting "positive" for everything gets 60%+ accuracy but is useless. "Conflict" is even rarer (<1%). Accuracy hides model failure on minority classes.

**Do this instead:** Macro-F1 (unweighted average of per-class F1). Also report per-class precision/recall. For multilingual systems, compute per-language macro-F1 separately.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-1K inferences/day | Single Celery worker on CPU. ONNX Runtime with CPU provider. Railway hobby tier. No GPU needed. |
| 1K-10K inferences/day | 2-3 Celery workers. Redis + PostgreSQL on managed services. GPU for batch training (not inference). |
| 10K-100K inferences/day | GPU-backed Celery workers (1 GPU per 3-4 workers). Model quantization (INT8 via ONNX Runtime). Autoscaling workers. CDN for frontend assets. |
| 100K+ inferences/day | Multi-GPU inference with request batching. ONNX Runtime with TensorRT or OpenVINO. Horizontal worker scaling. Read replicas for PostgreSQL. Redis Cluster. |

### Scaling Priorities

1. **First bottleneck: Model inference latency.** On CPU, XLM-RoBERTa base takes ~200-500ms per inference. At high concurrency, the worker pool saturates. Solution: scale Celery workers horizontally, or switch to GPU workers with ONNX Runtime CUDA provider.

2. **Second bottleneck: Redis queue depth.** If inference is slower than ingestion rate, the Redis queue grows unbounded. Solution: set Celery worker concurrency limits, implement queue backpressure (return 503 if queue depth > threshold), add more workers.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| HuggingFace Hub | Download model checkpoints, push fine-tuned models | `huggingface_hub` Python library. Model versioning via Git LFS. |
| MLflow Tracking Server | Log params/metrics/artifacts via REST API | Local server for dev, managed service for prod. |
| DVC Remote Storage | Push/pull dataset versions | S3/GCS/AWS-compatible storage. |
| Railway | App deployment via Docker | Private networking between API + Redis + PostgreSQL services. |
| Vercel | Frontend deployment via Git integration | Serverless React app, connects to Railway API via public URL. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| FastAPI ↔ Celery | Redis (task queue + result backend) | Task serialization via JSON. `@app.task(bind=True)` for retry. |
| Celery Worker ↔ ONNX Runtime | In-process (Python binding) | Model loaded once at worker init. No IPC overhead. |
| Celery Worker ↔ PostgreSQL | SQLAlchemy async session | Write inference results asynchronously. |
| Frontend ↔ FastAPI API | HTTP REST (JSON) over HTTPS | CORS from Vercel domain. Bearer token auth. |
| FastAPI ↔ Redis | aioredis (async) | Rate limiting, session cache, task status checks. |

## Sources

- [HuggingFace XLM-RoBERTa Documentation](https://huggingface.co/docs/transformers/main/en/model_doc/xlm-roberta) — Official model docs, tokenizer behavior, model classes
- [absa-pipeline (GitHub)](https://github.com/logmoon/absa-pipeline) — Reference ABSA two-stage pipeline with BIO tagging and sentence pair classification
- [XLM-RoBERTa + CRF for Aspect Extraction](https://github.com/nikitashvarts/scimdix_aspect_extraction) — XLM-RoBERTa token classification with transfer learning
- [M-ABSA Dataset & Baseline](https://github.com/swaggy66/M-ABSA) — Multilingual ABSA dataset spanning 21 languages, mT5 baselines
- [FastAPI + Celery Architecture Guide](https://markaicode.com/architecture/fastapi-llm-architecture) — Production async inference architecture patterns (FastAPI v0.115.14, Celery v5.4.0)
- [MLflow + HuggingFace Integration](https://mlflow.org/docs/latest/python_api/mlflow.transformers.html) — Official autolog support for HuggingFace Transformers
- [ONNX Runtime + XLM-RoBERTa Export](https://medium.com/@keruchen/export-fine-tuned-bert-model-to-onnx-and-inference-using-onnxruntime-bb1ab568b354) — Reference for exporting XLM-RoBERTa to ONNX
- [XLM-RoBERTa Sentiment Analysis on Amazon Reviews](https://www.sciencedirect.com/science/article/pii/S1877050925026213) — Two-stage ABSA with XLM-RoBERTa for multilingual product reviews

---

*Architecture research for: Multilingual Aspect-Based Sentiment Analysis (ABSA)*
*Researched: 2026-06-22*
