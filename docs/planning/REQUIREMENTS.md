# Requirements: Multilingual ABSA

**Defined:** 2026-06-22
**Core Value:** Accurately extract aspect terms and their sentiment from product reviews across English, Hindi, and Hinglish

## v1 Requirements

### Project Scaffold & Data Pipeline

- [ ] **SCAFF-01**: Project folder structure created (`src/data/`, `src/models/`, `src/evaluation/`, `src/utils/`, `api/`, `dashboard/`, `docker/`, `notebooks/`, `data/`)
- [ ] **SCAFF-02**: DVC initialized with remote storage configuration for dataset versioning
- [ ] **SCAFF-03**: Python dependency management with `pyproject.toml` pinning Python 3.11+
- [ ] **SCAFF-04**: Pre-commit hooks configured (black, ruff, mypy)
- [ ] **SCAFF-05**: Data download script for SemEval 2014 ABSA dataset (laptop + restaurant)
- [ ] **SCAFF-06**: EDA notebook skeleton exploring data structure, label distribution, language distribution
- [ ] **SCAFF-07**: Hinglish preprocessing with `dhvani` normalization for romanized Hindi variants
- [ ] **SCAFF-08**: BIO alignment unit tests verifying subword tokenization correctness
- [ ] **SCAFF-09**: Language detection module (English / Hindi / Hinglish routing)
- [ ] **SCAFF-10**: MLflow tracking server configured for experiment logging

### Aspect Term Extraction (ATE)

- [ ] **ATE-01**: Token classification model fine-tuned on SemEval 2014 with BIO tagging (B-ASP, I-ASP, O)
- [ ] **ATE-02**: Subword-aware BIO alignment using `word_ids()` for SentencePiece tokenization
- [ ] **ATE-03**: Training pipeline logged to MLflow with params, metrics, and model artifacts
- [ ] **ATE-04**: Evaluation with precision, recall, Macro-F1 per tag class

### Per-Aspect Sentiment Classification (ASC)

- [ ] **ASC-01**: Four-class sentiment model (positive, negative, neutral, conflict) per extracted aspect
- [ ] **ASC-02**: Weighted cross-entropy loss to handle neutral class imbalance (3-18x ratio)
- [ ] **ASC-03**: Joint training pipeline with ATE (shared XLM-RoBERTa encoder, two heads)
- [ ] **ASC-04**: Per-class and macro-averaged sentiment metrics logged to MLflow

### ONNX Export & API

- [ ] **ONNX-01**: Separate ONNX exports for ATE and ASC models using `optimum-onnx`
- [ ] **ONNX-02**: Numerical parity test between PyTorch and ONNX outputs (tolerance 1e-4)
- [ ] **ONNX-03**: FastAPI inference endpoint (`POST /predict`) accepting text, returning aspect-sentiment pairs
- [ ] **ONNX-04**: Input preprocessing pipeline (language detection → cleaning → tokenization)
- [ ] **ONNX-05**: Confidence scores included in API responses
- [ ] **ONNX-06**: Error handling for empty text, long inputs, unsupported languages

### Frontend Dashboard

- [ ] **DASH-01**: React + Vite + TailwindCSS dashboard scaffolded
- [ ] **DASH-02**: Aspect-sentiment distribution bar chart (Recharts)
- [ ] **DASH-03**: Per-review result display with highlighted aspect terms
- [ ] **DASH-04**: Summary statistics KPI cards
- [ ] **DASH-05**: CSV/JSON export of analysis results

### Docker & Deployment

- [ ] **DOCK-01**: Docker Compose for local development (API + ONNX runtime)
- [ ] **DOCK-02**: Multi-stage Dockerfile for API with ONNX Runtime
- [ ] **DOCK-03**: Railway deployment configuration
- [ ] **DOCK-04**: Vercel deployment for frontend

### Evaluation & Monitoring

- [ ] **EVAL-01**: Macro-F1 as primary metric for both ATE and ASC
- [ ] **EVAL-02**: Cross-lingual evaluation (train on English, evaluate on Hindi/Hinglish)
- [ ] **EVAL-03**: Confusion matrix per language for sentiment classification

## v2 Requirements

### Advanced Features

- **V2-01**: Combined ONNX graph (ATE + ASC in single graph) — deferred due to dynamic-axis fragility
- **V2-02**: Celery + Redis async batch processing — deferred, thread-pool sufficient for v1
- **V2-03**: Evidently AI drift monitoring — deferred until production traffic exists
- **V2-04**: Prometheus + Grafana operational metrics — deferred until deployment
- **V2-05**: PostgreSQL persistence for analysis history — deferred, in-memory sufficient for v1
- **V2-06**: IndicBERT-v3-1B comparison for Hindi/Hinglish optimization
- **V2-07**: Data augmentation for low-resource Hindi/Hinglish (back-translation, code-switching)
- **V2-08**: Aspect category detection (ACD) — structured aspect grouping

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time streaming inference | Kafka/PubSub too complex for v1 batch analysis |
| Mobile application | Web dashboard sufficient; mobile via responsive design |
| Additional languages beyond EN/HI/Hinglish | Each language needs annotation + validation — scope creep |
| Voice/audio review processing | ASR pipeline adds significant complexity |
| Multimodal ABSA (image + text) | Active research area, not production-ready |
| LLM-based ABSA (GPT/LLama) | Too expensive ($0.003-0.01/review), too slow, non-deterministic |
| User authentication / multi-tenant | Premature for single-user v1 deployment |
| Automated retraining pipeline | Needs production usage data first |
| WebSocket live updates | Poll-based refresh sufficient for batch analysis |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SCAFF-01 | Phase 1 | Pending |
| SCAFF-02 | Phase 1 | Pending |
| SCAFF-03 | Phase 1 | Pending |
| SCAFF-04 | Phase 1 | Pending |
| SCAFF-05 | Phase 1 | Pending |
| SCAFF-06 | Phase 1 | Pending |
| SCAFF-07 | Phase 1 | Pending |
| SCAFF-08 | Phase 1 | Pending |
| SCAFF-09 | Phase 1 | Pending |
| SCAFF-10 | Phase 1 | Pending |
| ATE-01 | Phase 2 | Pending |
| ATE-02 | Phase 2 | Pending |
| ATE-03 | Phase 2 | Pending |
| ATE-04 | Phase 2 | Pending |
| EVAL-01 | Phase 2 | Pending |
| ASC-01 | Phase 3 | Pending |
| ASC-02 | Phase 3 | Pending |
| ASC-03 | Phase 3 | Pending |
| ASC-04 | Phase 3 | Pending |
| EVAL-02 | Phase 3 | Pending |
| EVAL-03 | Phase 3 | Pending |
| ONNX-01 | Phase 4 | Pending |
| ONNX-02 | Phase 4 | Pending |
| ONNX-03 | Phase 4 | Pending |
| ONNX-04 | Phase 4 | Pending |
| ONNX-05 | Phase 4 | Pending |
| ONNX-06 | Phase 4 | Pending |
| DOCK-01 | Phase 5 | Pending |
| DOCK-02 | Phase 5 | Pending |
| DOCK-03 | Phase 5 | Pending |
| DOCK-04 | Phase 5 | Pending |
| DASH-01 | Phase 6 | Pending |
| DASH-02 | Phase 6 | Pending |
| DASH-03 | Phase 6 | Pending |
| DASH-04 | Phase 6 | Pending |
| DASH-05 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 36 total
- Mapped to phases: 36
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-22*
*Last updated: 2026-06-22 after roadmap creation*
