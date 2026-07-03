# Feature Landscape

**Domain:** Multilingual Aspect-Based Sentiment Analysis (ABSA) for product reviews
**Researched:** 2026-06-22

## Overview

This document maps the feature landscape for a multilingual ABSA system supporting English, Hindi, and Hinglish (code-mixed). It categorizes features into **table stakes** (must-have or product feels incomplete), **differentiators** (competitive advantage), **anti-features** (explicitly avoid), and identifies dependencies between features.

The primary ABSA pipeline consists of two stages:
1. **Stage 1 — Aspect Term Extraction (ATE):** Token classification using BIO tagging to identify aspect spans (e.g., "battery life", "camera quality")
2. **Stage 2 — Per-Aspect Sentiment Classification (ASC):** Classify sentiment (positive/negative/neutral/conflict) for each extracted aspect

Both stages compile into a single ONNX inference graph for production deployment.

---

## Table Stakes

Features that any production-grade ABSA system must provide.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Aspect Term Extraction (ATE) via BIO tagging** | Core ABSA function — identifies what is being talked about. Token-level classification with B-ASP/I-ASP/O tags. | High | Standard across all ABSA systems (PyABSA, HuggingFace, etc.). Cannot be omitted. |
| **Per-Aspect Sentiment Classification (ASC)** | Core ABSA function — determines sentiment polarity per aspect. Classes: positive, negative, neutral, conflict. | High | Standard four-class setup. Conflict class is ABSA-specific and may need special handling. |
| **REST API for single-text inference** | Required for any production NLP service. POST endpoint accepting text, returning structured aspect-sentiment pairs. | Medium | FastAPI is the standard. `POST /predict` returning `{"aspects": [{"term": "...", "sentiment": "..."}]}`. |
| **Input text preprocessing** | Raw review text needs cleaning: lowercasing, punctuation handling, encoding normalization, noise removal. | Low | Standard NLP preprocessing. For Hinglish, needs romanized text normalization (e.g., "acha" vs "accha" vs "achha"). |
| **Language detection** | Must detect whether input is English, Hindi, or Hinglish to route to appropriate model/pipeline. | Medium | Can use fastText language detector or character-level classifiers. Critical for multilingual routing. |
| **Model persistence and loading** | Trained models must be saveable, loadable, and versioned. Checkpoint format for HuggingFace + ONNX export. | Medium | Standard ML practice. ONNX export is the contract for production — no PyTorch in the API process. |
| **Evaluation metrics reporting** | Must report precision, recall, F1-score (per-class and macro) for both ATE and ASC tasks. | Low | Standard sklearn metrics. Macro-F1 is the primary metric for ABSA, not accuracy (due to class imbalance). |
| **Training pipeline** | Scripts to fine-tune XLM-RoBERTa on ABSA datasets. Must handle BIO-tagging format for ATE and multi-class for ASC. | High | HuggingFace Trainer + PEFT/QLoRA for efficient fine-tuning. Required for model iteration. |
| **Error handling for API** | Graceful handling of empty text, very long inputs, unsupported languages, model failures. Proper HTTP status codes. | Low | Standard FastAPI error handlers. Pydantic validation for input schemas. |
| **Batch inference endpoint** | Process multiple reviews in one request. Required for any non-trivial workload. | Medium | POST endpoint accepting array of texts. JSON response array. |
| **Confidence scores** | Each prediction should include a confidence/probability score. Users need to know when the model is uncertain. | Medium | Softmax probabilities from the classification head. Useful for dashboard filtering and threshold-based decisions. |
| **Configuration management** | Model paths, ONNX runtime settings, language configs, API settings via environment/config files. | Low | Standard practice. Pydantic Settings for configuration management. |

### Table Stakes — Visualization

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Aspect-sentiment distribution chart** | Bar chart showing sentiment counts per aspect. The primary visualization users expect. | Medium | Bar chart (Recharts). Filterable by aspect term. |
| **Per-review result display** | Show individual review with highlighted aspect terms and color-coded sentiment labels. | Medium | Inline annotation in the UI. Users need to inspect individual results. |
| **Summary statistics** | Total reviews analyzed, aspects found, sentiment breakdown percentages. | Low | KPI cards above charts. Quick overview of dataset. |
| **Export results** | Download analysis results as CSV/JSON for reporting. | Low | Standard feature. Users need to share findings. |

---

## Differentiators

Features that set this project apart from basic ABSA implementations.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Multilingual support (English + Hindi + Hinglish)** | Most ABSA systems are English-only. Supporting Hindi and code-mixed Hinglish opens the Indian market — 600M+ internet users. Few production systems handle Hinglish. | High | XLM-RoBERTa handles multilingual by design. Hinglish needs romanized text and code-switch handling. Requires language-specific data augmentation. |
| **Combined ONNX inference graph (ATE + ASC)** | Compiling both stages into a single ONNX graph reduces latency and eliminates intermediate data serialization. Rare in open-source ABSA. | High | Custom ONNX export logic. PyABSA doesn't do this — it keeps stages separate. Combined graph is a meaningful architectural differentiator. |
| **ONNX-optimized production inference** | No PyTorch dependency in the API container. Smaller images, faster cold starts, GPU-friendly. ONNX Runtime is production-proven. | Medium | Standard practice for ML deployment but NOT standard in ABSA systems. Most ABSA demos run raw PyTorch in the API. |
| **Macro-F1 as primary metric** | Correct for imbalanced ABSA tasks where some sentiments (conflict) or aspects are rare. Most teams default to accuracy incorrectly. | Low | Easy to implement (sklearn), but requires team discipline to prioritize over accuracy. Standard in ABSA research but NOT in industry. |
| **Celery + Redis async inference** | Non-blocking inference for long-running batch jobs. Web server stays responsive under load. Task queue with retries and prioritization. | High | FastAPI + Celery + Redis is a proven production pattern. Not commonly seen in ABSA demos. |
| **MLflow experiment tracking** | Every training run logged with params, metrics, artifacts, and model registry. Enables reproducible research and model comparison. | Medium | Standard MLOps practice but rarely integrated into ABSA projects. Most ABSA repos have no tracking. |
| **DVC dataset versioning** | Track dataset versions alongside code. Reproducible training pipelines. | Medium | Important for multilingual datasets where annotation quality varies. SHA-pinned data prevents silent regressions. |
| **Evidently AI drift monitoring** | Monitor input distribution shifts (e.g., new product categories, language drift) and prediction distribution shifts over time. | Medium | Data drift + prediction drift detection. Triggers retraining alerts. Production MLOps differentiator. |
| **Prometheus + Grafana observability** | Request latency, error rates, inference throughput, queue depth. Operational visibility beyond model metrics. | Medium | Standard for production services but absent from most ABSA deployments. Enables SLA tracking. |
| **Hinglish code-mixed text handling** | Romanized Hindi-English mixing (e.g., "yeh phone ka battery life bahut acha hai"). Standard NLP pipelines fail on this. | High | Requires: (1) character-level lang detection per token, (2) normalization of variant spellings, (3) code-switch-aware tokenization. Research-grade capability. |
| **Cross-lingual transfer learning** | Fine-tune on English data and evaluate zero-shot on Hindi/Hinglish. Demonstrates XLM-RoBERTa's cross-lingual capability. | Medium | Train on SemEval English → evaluate on Hindi. Useful for low-resource scenarios. Shows multilingual capability. |
| **Per-aspect sentiment trend over time** | Track how sentiment for specific aspects evolves (e.g., "battery" sentiment trending down over months). | Medium | Time-series data from batch processing. Line charts in dashboard. |
| **Aspect category detection** | Beyond extracting terms, categorize aspects into predefined groups (e.g., "food quality", "service", "price", "ambiance"). | High | Standard subtask in ABSA research (ACD). Adds structured reporting but requires category taxonomy and additional training data. |
| **Model A/B comparison** | Compare two model versions side-by-side on the same input. Shows prediction differences. | Medium | Useful during model iteration. MLflow registry enables model version tracking. |
| **Docker Compose local dev environment** | One-command setup for full stack: API + Celery + Redis + PostgreSQL + Dashboard. Makes the project accessible. | Low | `docker compose up` for the entire system. Standard but not common in ABSA projects. |

### Differentiators — Dataset & Annotation

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Hindi ABSA dataset preparation** | Translate/extend SemEval ABSA datasets to Hindi. Very few Hindi ABSA datasets exist publicly. | High | M-ABSA (EMNLP 2025) is a new 21-language dataset. ABSA-Mix (2024) provides Hinglish data. Key resource. |
| **Hinglish code-mixed dataset** | Synthesize or collect Hinglish product reviews with aspect + sentiment annotations. Rare resource. | High | Use ABSA-Mix (restaurant/laptop domains). Augment with synthetic Hinglish via rule-based code-switching. |
| **Data augmentation for low-resource** | Back-translation, synonym replacement, code-switch augmentation to improve Hindi/Hinglish performance. | Medium | nlpaug library, text augmentation in PyABSA. Mitigates limited annotated data for Hindi. |

---

## Anti-Features

Features to explicitly NOT build in v1 (valid reasons).

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Real-time streaming inference** | Requires Kafka/PubSub infrastructure, exactly-once semantics, stateful processing. Not needed for batch review analysis. | Use Celery async batch processing. Poll-based results for the dashboard. |
| **Mobile application** | Adds another platform to maintain (React Native/Flutter). Core value is in the analysis engine, not the device. | Build a responsive web dashboard. Mobile-friendly via TailwindCSS responsive design. |
| **Additional languages beyond EN/HI/Hinglish** | Each language requires dataset annotation, model validation, and language-specific preprocessing. Scope creep. | Defer to v2. The architecture (XLM-RoBERTa) supports expansion. Add per-language modules. |
| **Voice/audio review processing** | ASR pipeline adds significant complexity. Speech-to-text errors cascade into ABSA errors. | Text-only input in v1. Audio processing can be a separate ingestion pipeline in v2. |
| **Multimodal ABSA (image + text)** | Requires image encoding, cross-modal attention, multimodal datasets. Active research area, not production-ready. | Text-only ABSA. Paper-thin value for product reviews. |
| **LLM-based ABSA (GPT/LLama in-context learning)** | ~$0.003-0.01 per review via API, 2-5s latency, non-deterministic outputs. Too expensive and slow for batch product reviews. | Fine-tuned XLM-RoBERTa provides deterministic, sub-100ms inference at a fraction of the cost. |
| **User authentication / multi-tenant** | Adds auth infrastructure, user management, data isolation. Premature for v1. | Single-user deployment. Auth can be added when multi-tenant is needed. |
| **Custom design system / component library** | Building from scratch is expensive. TailwindCSS + Recharts covers all needs. | Use TailwindCSS utility classes + Recharts + Radix UI primitives. No custom components. |
| **Automated retraining pipeline** | Requires ground-truth collection, label delay handling, A/B evaluation, manual approval gates. Premature without production usage data. | Manual retraining triggered by drift alerts. Automate after v1 proves value. |
| **WebSocket-based live updates** | Real-time push requires stateful connections. Adds complexity without payoff for batch analysis. | Poll-based refresh (every N seconds). Adequate for batch processing results. |

---

## Feature Dependencies

```
Aspect Term Extraction (ATE)
  ├── Requires: Language detection → Per-language tokenizer → BIO-tagged training data
  ├── Requires: Fine-tuned XLM-RoBERTa model (or IndicBERT for Hindi)
  └── Blocked by: Dataset preparation (EN + HI + Hinglish)

Per-Aspect Sentiment Classification (ASC)
  ├── Requires: Extracted aspect terms from ATE
  ├── Requires: Per-aspect sentiment training data
  └── Note: Can be joint model with ATE (shared encoder) or separate

Combined ONNX Graph
  ├── Requires: Both ATE and ASC models trained and validated
  ├── Requires: Custom ONNX export script merging both graphs
  └── Blocked by: Both model training phases

REST API
  ├── Requires: ONNX runtime inference engine
  ├── Requires: Preprocessing pipeline (language detection + cleaning)
  └── Dependency: Models exported to ONNX

Celery Batch Processing
  ├── Requires: Redis instance
  ├── Requires: Task definitions for batch inference
  └── Dependency: REST API core logic

Dashboard
  ├── Requires: API endpoints for results + history
  ├── Requires: PostgreSQL schema for storing results
  └── Dependency: Working API

MLflow Tracking
  ├── Requires: MLflow server instance
  ├── Requires: Training scripts instrumented with mlflow.* calls
  └── Note: Independent of API — parallel track

Evidently AI Monitoring
  ├── Requires: Reference dataset (training data distribution)
  ├── Requires: Production inference data feed
  └── Dependency: Deployed API with traffic

DVC Dataset Versioning
  ├── Requires: DVC remote storage (S3/GCS)
  ├── Requires: Data directory structured as DVC-tracked
  └── Note: Setup independent from model training
```

### Dependency Graph (simplified)

```
Data Collection → DVC Tracking
     ↓
Data Preprocessing (cleaning, language detection, tokenization)
     ↓
Dataset Annotation (BIO for ATE, polarity for ASC)
     ↓
Model Training (XLM-RoBERTa fine-tuning)
     ├── MLflow: log params, metrics, artifacts
     └── Evaluation: Macro-F1, precision, recall
     ↓
ONNX Export (combined ATE + ASC graph)
     ↓
API (FastAPI + ONNX Runtime)
     ├── Single inference endpoint
     └── Celery batch processing → Redis → PostgreSQL
     ↓
Dashboard (React + Recharts)
     └── Visualize results, trends, export
```

---

## MVP Recommendation

### Phase 1 (Foundation): Ship
1. **Aspect Term Extraction** — BIO-based token classification (XLM-RoBERTa)
2. **Per-Aspect Sentiment Classification** — Four-class sentiment per aspect
3. **Combined ONNX inference graph** — Single export for both stages
4. **FastAPI inference API** — `POST /predict` endpoint with JSON response
5. **Input preprocessing** — Language detection, text cleaning, tokenization
6. **Basic evaluation** — Macro-F1, precision, recall for both stages
7. **MLflow tracking** — Log all training runs

### Phase 2 (Dashboard & Data): Ship
1. **React dashboard** — Aspect-sentiment distribution, per-review view, summary stats
2. **Hindi dataset preparation** — Extend SemEval/ABSA-Mix for Hindi
3. **Hinglish dataset preparation** — ABSA-Mix dataset + augmentation
4. **Cross-lingual evaluation** — Zero-shot transfer results
5. **Batch inference** — Celery + Redis for async processing
6. **PostgreSQL storage** — Persist analysis results
7. **CSV/JSON export** — Downloadable reports

### Phase 3 (Production Hardening): Ship
1. **Evidently AI drift monitoring** — Data drift + prediction drift
2. **Prometheus + Grafana** — Operational metrics
3. **Docker Compose** — Full stack local deployment
4. **DVC dataset versioning** — Reproducible data
5. **Error handling + input validation** — Production-grade API

### Defer
- **Real-time streaming:** Kafka/PubSub integration (Phase 4+)
- **Additional languages:** Expand beyond EN/HI/Hinglish (v2)
- **Automated retraining:** Trigger-based retraining pipeline (v2)
- **Multi-tenant / auth:** User management (v2)
- **Mobile app:** Web-only for v1 (not planned)
- **LLM-based ABSA:** Not recommended — cost vs. fine-tuned model gap

### What to Skip Entirely
- Multimodal ABSA (image + text)
- Voice/audio processing
- Custom UI design system
- WebSocket live updates

---

## Related Research & Open Source

### Notable ABSA Frameworks (for reference)
| Framework | Language | Multilingual? | ONNX Support? | Production Features? |
|-----------|----------|---------------|---------------|---------------------|
| **PyABSA** | Python | Yes (multilingual checkpoint) | No (raw PyTorch) | Flask demos only |
| **absa-pipeline** | Python | No (English BERT) | No | Inference script only |
| **amazon-science (instruction-tuning)** | Python | No | No | Research only |
| **HuggingFace + custom** | Python | Yes (XLM-R) | Manual | Custom per project |

**Key insight:** No open-source ABSA framework provides combined ONNX export, multilingual Hinglish support, and production-grade API/dashboard. This project fills that gap.

### Key Datasets
| Dataset | Languages | Domains | Format | Source |
|---------|-----------|---------|--------|--------|
| **SemEval-2014/2015/2016** | EN | Restaurant, Laptop | ATE + ASC | Standard benchmark |
| **M-ABSA** (EMNLP 2025) | 21 langs (incl. HI) | 7 domains | Triplet extraction | `Multilingual-NLP/M-ABSA` |
| **ABSA-Mix** (CSL 2024) | Hinglish | Restaurant, Laptop | ATE + ASC | `20118/ABSA-MIX` GitHub |
| **MAMS** | EN | Restaurant | ATE + ASC | Multi-aspect, harder task |

---

## Sources

- PyABSA framework documentation (`pyabsa.readthedocs.io`) — Confidence: HIGH
- M-ABSA dataset paper (arXiv 2502.11824, EMNLP 2025) — Confidence: HIGH
- ABSA-Mix: Code-mixed Hinglish ABSA (Computer Speech & Language, 2024) — Confidence: HIGH
- ABSA systematic review (Knowledge and Information Systems, 2024) — Confidence: HIGH
- FastAPI production architecture patterns (Markaicode, 2026) — Confidence: MEDIUM
- Evidently AI model monitoring guide (evidentlyai.com, 2025) — Confidence: HIGH
- Hinglish sentiment analysis projects (GitHub aiwithkd/hinglish-sentiment-analysis) — Confidence: MEDIUM
- Semantic Scholar / ScienceDirect ABSA survey papers — Confidence: HIGH
