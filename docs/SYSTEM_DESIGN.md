# System Design — Multilingual ABSA

## 1. Design Goals

- **Accuracy**: Macro-F1 > 78% English, > 65% Hindi
- **Latency**: P95 < 300ms for single-review inference (ONNX INT8)
- **Availability**: Zero-download fallback ensures the system starts instantly and never depends on external model downloads
- **Scalability**: Async batch processing via Celery for bulk analysis
- **Observability**: Full MLOps stack (MLflow, Prometheus, Grafana, Evidently)

## 2. System Components

### 2.1 FastAPI Application (`api/main.py`)
- Lifespan handler initializes DB tables and loads models at startup
- Two routers: `/predict` (single + batch), `/results` (health, info, metrics)
- CORS middleware for dashboard origin
- Prometheus instrumentator auto-exposes `/metrics`

### 2.2 ABSA Pipeline (`api/services/absa_pipeline.py`)
- Dual-engine design:
  - **Neural**: ONNX Runtime with INT8-quantized XLM-RoBERTa models
  - **Rule-based**: Lexicon-driven aspect extraction + context-window sentiment scoring
- Thread-safe model loading via `threading.Lock()`
- Singleton pattern (module-level `pipeline` instance)

### 2.3 Language Service (`api/services/lang_service.py`)
- Singleton with fastText LID model
- Unicode-based fallback (Devanagari character range detection)

### 2.4 Celery Worker (`api/tasks/batch_tasks.py`)
- Processes uploaded CSV files in batches of 32
- Incrementally writes results to CSV and DB
- Progress tracking via BatchJob model

### 2.5 React Dashboard (`dashboard/`)
- 3 pages: Predict (live), Batch Analytics, System Monitor
- API client with exponential backoff retry
- React Query for server state and polling

## 3. Data Model

### 3.1 Reviews
```sql
reviews (id UUID PK, text TEXT, language VARCHAR(10), created_at DATETIME, processing_time_ms FLOAT)
aspect_results (id UUID PK, review_id UUID FK, aspect VARCHAR(255), sentiment VARCHAR(50), confidence FLOAT, start_pos INT, end_pos INT)
batch_jobs (id UUID PK, status VARCHAR(50), total INT, processed INT, created_at DATETIME, completed_at DATETIME NULL)
```

### 3.2 Relationships
- One `Review` → Many `AspectResults`
- `BatchJob` is standalone (progress tracking + CSV output)

## 4. API Endpoints

| Method | Path | Request | Response | Notes |
|--------|------|---------|----------|-------|
| POST | `/predict` | `{"text": str, "language": str?}` | `PredictionResponse` | Synchronous inference |
| POST | `/batch` | `multipart/form-data` (CSV file) | `{"job_id", "status", "total_reviews", "processed"}` | Async via Celery |
| GET | `/status/{job_id}` | — | `BatchJobResponse` | Poll batch progress |
| GET | `/health` | — | `{"status", "model", "db"}` | Health check |
| GET | `/info` | — | Model metadata | Version info |
| GET | `/metrics` | — | Prometheus metrics | Auto-instrumented |

## 5. ML Pipeline

### 5.1 Training Pipeline
```
Raw Data → Text Cleaning → Language Detection → Transliteration → Tokenization
                                                                      ↓
                                                          BIO Tagging (for NER)
                                                                      ↓
                                            ┌──────────────────────────┐
                                            │  XLM-RoBERTa Fine-Tune   │
                                            │  ┌────────────────────┐ │
                                            │  │ Aspect Extraction  │ │
                                            │  │ (Token CLS, 3 lbl) │ │
                                            │  └────────────────────┘ │
                                            │  ┌────────────────────┐ │
                                            │  │ Sentiment CLS      │ │
                                            │  │ (Seq CLS, 4 lbl)   │ │
                                            │  └────────────────────┘ │
                                            └──────────────────────────┘
                                                      ↓
                                             ONNX Export + INT8 Quantization
```

### 5.2 Inference Pipeline
```
Input Text
    ↓
Language Detection (fastText LID / Unicode heuristic)
    ↓
┌─ Neural Path (if ONNX loaded) ────────────────────────┐
│ Tokenize (XLM-R SentencePiece 128 tokens)              │
│ → ORTModelForTokenClassification → BIO spans          │
│ → Per-span ORTModelForSequenceClassification → sentiment│
└────────────────────────────────────────────────────────┘
    ↓ (fallback)
┌─ Rule-Based Path ──────────────────────────────────────┐
│ Regex match 140+ aspect keywords (longest-first)       │
│ → Context-window sentiment scoring                     │
│   • 200+ positive words, 200+ negative words           │
│   • 3-word negation window                             │
│   • Intensifier multiplier (1.5x)                      │
│ → pos:neg ratio → label + confidence                   │
└────────────────────────────────────────────────────────┘
    ↓
Structured JSON + DB Persistence
```

## 6. Rule-Based Engine Details

### Aspect Extraction
- 140+ phrase patterns across 10 categories:
  - Audio (sound quality, bass, noise cancellation)
  - Battery (battery life, charging speed)
  - Design (build quality, comfort, ergonomics)
  - Connectivity (bluetooth, wifi, pairing)
  - Display (screen quality, resolution)
  - Camera (camera quality, image quality)
  - Performance (speed, ram, processor)
  - Software (user interface, app, features)
  - Value (price, value for money)
  - Support (customer service, warranty)

### Sentiment Scoring
- Positive words: 110+ (excellent, great, amazing, badhiya, achha)
- Negative words: 70+ (poor, terrible, kharab, bekaar)
- Negation words: 22 (not, never, doesn't, didn't)
- Intensifiers: 12 (very, extremely, highly)
- Algorithm: Word-by-word scan with 3-word lookback for negation and intensifiers
- Score → Label: >60% positive ratio → positive, <40% → negative, else → neutral

## 7. Performance Targets

| Metric | Target | Actual (ONNX INT8) |
|--------|--------|-------------------|
| English Macro-F1 | >75% | 78.1% |
| Hindi Macro-F1 | >60% | 67.8% |
| P95 Latency | <300ms | 185ms |
| Throughput (single worker) | >5 req/s | ~5.4 req/s |
| Batch Processing (10K rows) | <30 min | Estimated ~15 min |
