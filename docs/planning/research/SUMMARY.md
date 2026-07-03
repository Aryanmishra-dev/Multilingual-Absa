# Project Research Summary

**Project:** Multilingual Aspect-Based Sentiment Analysis (ABSA)
**Domain:** Multilingual NLP — English, Hindi, Hinglish product review analysis
**Researched:** 2026-06-22
**Confidence:** HIGH

## Executive Summary

This project builds a production-grade multilingual ABSA system that extracts aspect terms and classifies their sentiment from product reviews in English, Hindi, and Hinglish (code-mixed). The canonical approach is a **two-stage pipeline**: (1) Aspect Term Extraction via BIO token classification, and (2) Per-Aspect Sentiment Classification into positive/negative/neutral/conflict, all powered by a shared XLM-RoBERTa encoder and exported to ONNX for inference. The key differentiator is combining multilingual support (handling code-mixed Hinglish) with production-grade deployment patterns (ONNX Runtime, FastAPI, async processing, MLOps).

**Recommended approach:** Start with `FacebookAI/xlm-roberta-base` as the backbone, fine-tune both stages separately using HuggingFace Transformers, export as **separate ONNX models** (not a combined graph for v1 — the dynamic-axis complexity for a two-stage combined graph is a known pitfall), and deploy via FastAPI with direct ONNX Runtime inference (skip Celery for v1). After establishing an English baseline, benchmark `ai4bharat/IndicBERT-v3-1B` for Hindi/Hinglish-specific improvements. Use `dhvani` for Hinglish spelling normalization as the only language-specific preprocessing — do NOT remove English stopwords from Hinglish text.

**Key risks:** (1) BIO label alignment with SentencePiece subword tokenization, especially for Romanized Hindi words — must be validated with unit tests before training. (2) Neutral class dominance in sentiment classification (up to 18× imbalance) — requires weighted loss functions and per-class F1 monitoring from day one. (3) ONNX export of two-stage models has dynamic-shape pitfalls — use separate ONNX models for v1. (4) Cross-lingual capacity dilution (curse of multilinguality) — evaluate per-language metrics separately and be prepared to use IndicBERT-v3-1B as a Hindi-specific backbone. (5) API serving complexity — avoid Celery overhead for v1; use FastAPI thread pool for synchronous inference.

## Key Findings

### Recommended Stack

**Core model:** Start with `FacebookAI/xlm-roberta-base` (0.3B params). After English baseline is solid, swap to `ai4bharat/IndicBERT-v3-1B` for Hindi/Hinglish-specific runs and compare Macro-F1. The `xlm-roberta-large` (0.55B) upgrade is only warranted if base underperforms by >3 Macro-F1 points on Hindi.

**Core ML stack:** Python 3.11+, PyTorch 2.12.x, HuggingFace Transformers 5.12.x, PEFT 0.19.x (only if fine-tuning large models on constrained GPU), Optimum + optimum-onnx for ONNX export, ONNX Runtime 1.27.x for production inference. Full fine-tuning of xlm-roberta-base fits on a 16GB GPU — no LoRA/QLoRA needed for the base model.

**Hinglish preprocessing:** `dhvani` (0.2.x) for phonetic normalization of Romanized Hindi spelling variants — pure lookup, <1ms per word, +1.2% Macro-F1 improvement observed. No transliteration to Devanagari — preserves Roman-script input. Do NOT use English stopword lists on Hinglish text (they strip valid Hindi content words like "to", "ka", "ki", "mein").

**MLOps:** MLflow 3.14.x (tracking + model registry), DVC 3.67.x (dataset versioning), Evidently AI 0.7.x (post-deployment drift monitoring).

**Infrastructure:** ONNX Runtime for production (no PyTorch in API image — reduces image size from ~3GB to ~200MB). FastAPI for REST endpoints. React 19 + Vite 6 + TailwindCSS 4 + Recharts 2 for dashboard. Docker 27.x for containerization.

> **Full detail in:** [STACK.md](STACK.md)

### Expected Features

**Must have (table stakes):**
- **BIO-based Aspect Term Extraction** — token classification (B-ASP, I-ASP, O tags). The foundation of any ABSA system.
- **Per-Aspect Sentiment Classification** — 4-class polarity (positive/negative/neutral/conflict). Standard ABSC output.
- **REST API with single and batch inference** — `POST /predict` and `POST /predict-batch` endpoints returning structured JSON.
- **Input preprocessing** — text cleaning, language detection (EN/HI/Hinglish), Hinglish normalization via dhvani.
- **Evaluation metrics** — Macro-F1 as the primary metric, with per-class and per-language breakdowns. Seqeval for span-level ATE evaluation.
- **Confidence scores** — softmax probabilities per prediction so users can gauge uncertainty.

**Should have (competitive differentiators):**
- **Multilingual EN+HI+Hinglish support** — XLM-RoBERTa handles all three in a single model. Few production ABSA systems handle Hinglish.
- **ONNX-optimized inference** — no PyTorch in production. Smaller images, faster cold starts.
- **Combined ONNX inference graph** — both stages in a single ONNX graph (v2 goal — v1 uses separate models due to dynamic-axis export pitfalls).
- **Celery + Redis async batch inference** — for CSV uploads and bulk processing (v2+ feature — v1 uses direct inference).
- **MLflow experiment tracking** — every training run logged with params, metrics, artifacts.
- **DVC dataset versioning** — SHA-pinned data versions for reproducible training.
- **Evidently AI drift monitoring** — detect input distribution shifts in production.
- **Prometheus + Grafana observability** — operational metrics beyond model accuracy.

**Defer (v2+):**
- Real-time streaming / Kafka integration
- Additional languages beyond EN/HI/Hinglish
- Automated retraining pipeline (replace with manual retraining triggered by drift alerts)
- User authentication / multi-tenant support
- LLM-based ABSA (too expensive and slow — $0.003-0.01/review, 2-5s latency)

**Skip entirely:**
- Mobile application (responsive web is sufficient for v1)
- Multimodal ABSA (image + text)
- Voice/audio processing
- Custom UI design system

> **Full detail in:** [FEATURES.md](FEATURES.md)

### Architecture Approach

The architecture follows a **two-stage pipeline** with a shared transformer backbone, separated training/inference workflows, and async web serving. Stage 1 (ATE) uses `XLMRobertaForTokenClassification` with BIO tagging to extract aspect spans. Stage 2 (ASC) takes each (review_text, aspect_span) pair through `XLMRobertaForSequenceClassification` for 4-class sentiment. Both stages share the XLM-RoBERTa encoder but have separate classification heads. For v1, stages are exported as **separate ONNX models** and chained in the application layer. For v2+, a combined ONNX graph is the target.

**Major components:**
1. **Data Pipeline** — Language detection, text preprocessing, BIO alignment with subword handling (`word_ids()`), Hinglish normalization (dhvani). DVC-tracked processed datasets with review-level stratified splitting to prevent data leakage.
2. **Training Pipeline** — HuggingFace Trainer with per-language and per-class F1 callbacks logged to MLflow. Stage 1 and Stage 2 trained independently with shared encoder weights.
3. **ONNX Export** — Separate exports per stage using `optimum-cli export onnx` with dynamic axes for variable-length inputs. Numerical validation against PyTorch (atol < 1e-4).
4. **Inference API** — FastAPI with ONNX Runtime `InferenceSession` loaded once at startup. Thread pool for non-blocking inference. Language detection routes through the same model.
5. **Monitoring & Observability** — Prometheus + Grafana for API metrics, Evidently AI for data drift, MLflow UI for experiment review.
6. **Frontend Dashboard** — React + Recharts for per-aspect sentiment distribution, per-review result display, CSV/JSON export, batch upload interface.

**Key patterns:**
- **Subword-aware BIO alignment** — first subword gets original label, subsequent subwords get I- prefix. Validated with round-trip unit tests.
- **Review-level data splitting** — all aspects from one review go to the same split (GroupShuffleSplit) to prevent data leakage.
- **Model-as-cache (warm start)** — ONNX model loaded once per Celery/worker process at startup.
- **Metric-driven evaluation** — Macro-F1 primary, with per-class, per-language, span-level, and end-to-end metrics tracked separately.

> **Full detail in:** [ARCHITECTURE.md](ARCHITECTURE.md)

### Critical Pitfalls

1. **BIO Alignment with Subword Tokenization (Critical)** — SentencePiece can split Hindi words into multiple subwords. Naive label assignment (repeating B-ASP for all subwords) creates spurious entity starts. **Mitigation:** Write a robust `align_labels_with_tokens()` function using `word_ids()`. Validate with a unit test on multilingual toy examples before training. *Phase: Data Pipeline.*

2. **Hinglish Preprocessing Gotchas (Critical)** — English stopword removal destroys Hinglish text ("to", "do", "ka", "ki" are valid Hindi words). No standard spelling for Romanized Hindi. **Mitigation:** Do NOT use English stopword lists. Use `dhvani` for spelling normalization. Token-level language identification. Validate on 100 held-out Hinglish samples manually. *Phase: Data Pipeline.*

3. **ONNX Dynamic Axes for Two-Stage Graph (Critical)** — Attempting to export both stages as a single ONNX graph fails because Stage 2's input (extracted aspects) has variable cardinality that ONNX opsets don't handle natively. Shape inference errors during tracing. **Mitigation:** Export as **separate ONNX models** for v1. Chain them in the application layer. Target combined graph for v2 only after validating with shape inference tests. *Phase: Architecture Decision (now) + ONNX Export (later).*

4. **Neutral Sentiment Class Dominance (Critical)** — Neutral examples outnumber positive/negative by 3-18×. Standard cross-entropy optimizes for always-predict-neutral. **Mitigation:** Use weighted cross-entropy (inverse class frequency weights) or focal loss. Monitor per-class F1 every epoch, not just Macro-F1. *Phase: Model Training.*

5. **Cross-Lingual Capacity Dilution (Critical)** — XLM-RoBERTa's fixed capacity is spread across 100 languages. Hindi token-level tasks may underperform by 5-10 points vs. a monolingual Hindi model. **Mitigation:** Evaluate per-language F1 from day one. Benchmark IndicBERT-v3-1B as an alternative for Hindi/Hinglish. Consider language-adversarial training if gaps exceed 10 points. *Phase: Model Training + Evaluation.*

6. **Data Leakage in Two-Stage Pipeline (Critical)** — Same-review aspects leaking across train/test splits. Stage 2 using gold spans during training but predicted spans during inference. **Mitigation:** Always split at the review level (GroupShuffleSplit). Use predicted spans for end-to-end evaluation. Add aspect span dropout during Stage 2 training. *Phase: Data Pipeline.*

7. **Celery Overhead (Moderate)** — Celery adds 40-60% latency for single-review inference vs. direct ONNX in a thread pool. **Mitigation:** Skip Celery for v1. Use FastAPI + `run_in_executor` with ONNX Runtime. Add Celery only when batch CSV uploads or high throughput (>100 req/min) is required. *Phase: Architecture Decision.*

> **Full detail in:** [PITFALLS.md](PITFALLS.md)

## Implications for Roadmap

Based on the combined research, the following phase structure is recommended. Dependencies and pitfalls strongly suggest this ordering.

### Phase 1: Project Scaffolding & Data Pipeline
**Rationale:** Everything depends on data. Setting up the data pipeline first ensures clean, versioned, correctly-processed data that all subsequent phases consume. BIO alignment and Hinglish preprocessing must be validated before any training begins.
**Delivers:** Project structure, DVC setup with remote storage and `.dvcignore`, MLflow tracking server, raw dataset acquisition (SemEval 2014, M-ABSA, ABSA-Mix), data preprocessing pipeline, Hinglish normalization (dhvani integration), BIO alignment function with unit tests, review-level stratified splits.
**Addresses from FEATURES.md:** Input preprocessing, Language detection, DVC dataset versioning, MLflow experiment tracking.
**Avoids from PITFALLS.md:** P1 (BIO alignment), P2 (Hinglish preprocessing), P7 (Data leakage), P10 (DVC management mistakes).
**Stack used:** DVC, MLflow, dhvani, HuggingFace datasets, tokenizers.
**Research flag:** Standard patterns — skip research-phase.

### Phase 2: Model Training — Stage 1 (Aspect Term Extraction)
**Rationale:** ATE is the foundation of the pipeline. Stage 2 depends on extracted aspects. Train and validate the token classification model first, establishing both evaluation infrastructure and a baseline English F1.
**Delivers:** Fine-tuned XLM-RoBERTa base for BIO tagging, MLflow-logged training runs with per-class and per-language metrics, span-level F1 evaluation, seqeval metrics pipeline.
**Addresses from FEATURES.md:** Aspect Term Extraction (table stakes), Evaluation metrics, MLflow tracking.
**Avoids from PITFALLS.md:** P5 (cross-lingual degradation — set up per-language metrics), P6 (metric selection — use span-level F1 + macro-F1).
**Stack used:** HuggingFace Transformers, PyTorch, seqeval, scikit-learn, MLflow.
**Research flag:** Well-documented — skip research-phase. Standard HuggingFace token classification training loop.

### Phase 3: Model Training — Stage 2 (Aspect Sentiment Classification)
**Rationale:** Depends on having a working ATE model to provide aspect spans for training data. Must be trained with awareness of Stage 1's error patterns.
**Delivers:** Fine-tuned XLM-RoBERTa base for 4-class sentiment classification, weighted loss function (inverse class frequency), per-class and per-language F1 monitoring, end-to-end evaluation pipeline (ATE + ASC jointly).
**Addresses from FEATURES.md:** Per-Aspect Sentiment Classification (table stakes), Confidence scores, Macro-F1 as primary metric.
**Avoids from PITFALLS.md:** P4 (neutral class dominance with weighted loss), P6 (metric dashboard with per-class F1).
**Stack used:** HuggingFace Transformers, PyTorch, scikit-learn, MLflow.
**Research flag:** Standard patterns — skip research-phase. Standard sequence classification training.

### Phase 4: ONNX Export & API v1
**Rationale:** The trained models must be operationalized. This phase builds the production inference path. Key decision: export as separate ONNX models (not combined graph) per PITFALLS P3.
**Delivers:** Separate ONNX exports for ATE and ASC, numerical validation against PyTorch (atol < 1e-4), FastAPI inference endpoint (`POST /predict`), language detection, direct ONNX Runtime inference with thread pool (no Celery), Pydantic v2 schemas for request/response.
**Addresses from FEATURES.md:** REST API for single-text inference, Input preprocessing, Language detection, Error handling, ONNX-optimized inference.
**Avoids from PITFALLS.md:** P3 (separate ONNX models avoids dynamic axes), P8 (benchmark and optimize latency), P11 (numerical validation between PyTorch and ONNX), P12 (skip Celery for v1).
**Stack used:** ONNX Runtime, FastAPI, Pydantic v2, Optimum + optimum-onnx.
**Research flag:** Needs moderate research during planning — ONNX Runtime configuration (execution providers, graph optimization levels, thread counts) and CPU vs GPU benchmarking.

### Phase 5: Docker & Deployment
**Rationale:** After the API works locally, containerize and deploy. Docker setup must match the export environment to avoid version mismatches (P9).
**Delivers:** Multi-stage Dockerfiles (export stage with PyTorch, serving stage with ONNX Runtime only), docker-compose.yml for local dev (API + PostgreSQL), Railway deployment configuration, CI smoke test that builds image and runs inference.
**Addresses from FEATURES.md:** Docker Compose local dev environment, Model persistence.
**Avoids from PITFALLS.md:** P9 (Docker/version compatibility — pin everything, use same base for export and serving).
**Stack used:** Docker, Railway, GitHub Actions.
**Research flag:** Standard patterns — skip research-phase. Docker multi-stage builds are well-documented.

### Phase 6: Frontend Dashboard
**Rationale:** The Dashboard depends on a working API with structured JSON output. UI design decisions (layout, charts, interaction patterns) are standard and don't need research.
**Delivers:** React + Vite + TailwindCSS + Recharts dashboard with: aspect-sentiment distribution charts, per-review result display with highlighted aspects, summary statistics KPI cards, CSV/JSON export, batch upload interface.
**Addresses from FEATURES.md:** Aspect-sentiment distribution chart, Per-review result display, Summary statistics, Export results.
**Stack used:** React 19, Vite 6, Recharts 2, TailwindCSS 4.
**Research flag:** Standard patterns — skip research-phase. Recharts bar charts and TailwindCSS layouts are well-documented.

### Phase 7: Hinglish/Hindi Optimization & Cross-Lingual Evaluation
**Rationale:** After English baseline is solid, push Hindi and Hinglish performance. This benefits from all earlier infrastructure being in place. Can be done in parallel with Phase 6.
**Delivers:** IndicBERT-v3-1B fine-tuning comparison vs XLM-RoBERTa, Hinglish data augmentation (translation-based, back-translation), language-adversarial training if cross-lingual gap > 10 points, per-language evaluation dashboard in MLflow.
**Addresses from FEATURES.md:** Multilingual support (differentiator), Hinglish code-mixed text handling, Cross-lingual transfer learning, Hindi dataset preparation.
**Avoids from PITFALLS.md:** P5 (cross-lingual degradation — benchmark IndicBERT-v3), P2 (Hinglish preprocessing — refine with augmentation).
**Stack used:** IndicBERT-v3-1B, HuggingFace Transformers, dhvani, nlpaug.
**Research flag:** **Needs research-phase during planning.** IndicBERT-v3-1B is a new model (Jan 2026) — training recipes, optimal hyperparameters, and PEFT needs for this specific architecture should be validated.

### Phase 8: Production Hardening & Monitoring
**Rationale:** After the system is deployed and has traffic, add monitoring and optimization. This phase completes the MLOps cycle.
**Delivers:** Evidently AI drift monitoring (data drift + prediction drift), Prometheus + Grafana dashboards, ONNX INT8 quantization for latency optimization, model versioning and A/B comparison in API.
**Addresses from FEATURES.md:** Evidently AI drift monitoring, Prometheus + Grafana observability, Model A/B comparison.
**Avoids from PITFALLS.md:** P8 (ONNX latency — quantize to INT8), P9 (Docker version stability — verify in CI).
**Stack used:** Evidently AI, Prometheus, Grafana, ONNX Runtime quantization tools.
**Research flag:** Standard patterns — skip research-phase. Evidently AI and Prometheus setups are well-documented.

### Phase 9: Combined ONNX Graph (v2 Feature)
**Rationale:** Combined graph reduces latency and simplifies deployment. Deferred until after v1 ships because the dynamic-axis complexity requires careful validation (P3).
**Delivers:** Single combined ONNX graph (shared XLM-RoBERTa encoder + both heads), shape inference validation, latency benchmark vs. two-model pipeline, MLflow model registry update.
**Addresses from FEATURES.md:** Combined ONNX inference graph (differentiator).
**Avoids from PITFALLS.md:** P3 (addressed now with proper testing), P8 (latency benchmark).
**Research flag:** **Needs research-phase during planning.** Custom ONNX graph construction with two heads requires understanding optimum-onnx's custom `OnnxConfig` API.

### Phase 10: Celery Batch Processing (v2 Feature)
**Rationale:** Celery adds infrastructure complexity and is only justified when batch processing or high throughput is a proven need.
**Delivers:** Celery worker pool with ONNX model warm-start, Redis broker, batch inference endpoint (`POST /predict-batch` with CSV/JSON input), task progress polling, result persistence in PostgreSQL.
**Addresses from FEATURES.md:** Celery + Redis async inference, Batch inference endpoint.
**Avoids from PITFALLS.md:** P12 (Celery overhead — only add when proven needed).
**Stack used:** Celery, Redis, PostgreSQL.
**Research flag:** Standard patterns — skip research-phase.

### Phase Ordering Rationale

- **Data before training.** Phases 1→2→3: Without clean, correctly-aligned, leakage-free data (Phase 1), model training produces unreliable results. The BIO alignment function must be validated before any training run.
- **Training before serving.** Phases 2→3→4: Models must be trained and validated before they can be exported and served. Stage 1 must work before Stage 2 can be trained (Stage 2 needs extracted aspect spans).
- **Local before deployed.** Phases 4→5: API should work locally first. Docker containers must match the export environment exactly to avoid version mismatch.
- **English before Hindi.** Phases 2-3→7: Baseline on English data first. Add Hindi/Hinglish optimization after the English pipeline is stable and metrics infrastructure is proven.
- **Simple serving before complex serving.** Phase 4 (direct inference) before Phase 10 (Celery). Avoid Celery overhead until batch processing is a proven requirement.
- **Two models before combined graph.** Phase 4 (separate ONNX models) before Phase 9 (combined graph). Avoid the dynamic-axis pitfall until the combined graph can be properly validated.
- **Basic before production.** Phases 1-6→8: Monitoring and drift detection are valuable only after the system is deployed and has traffic.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified against official PyPI/HuggingFace registries and documentation. XLM-RoBERTa and supporting libraries are mature and well-documented. |
| Features | HIGH | ABSA domain is well-researched with consistent feature expectations across literature. Feature categorization validated against multiple surveys and production systems. |
| Architecture | HIGH | Two-stage pipeline with BIO tagging is the field-standard approach. Patterns are documented in peer-reviewed papers (M-ABSA, LACA, Smíd et al. 2025). |
| Pitfalls | HIGH | Pitfalls are grounded in documented failure modes from literature, GitHub issues, and production experience. BIO alignment, class imbalance, and ONNX export issues are well-attested. |

**Overall confidence:** HIGH

### Gaps to Address

1. **IndicBERT-v3-1B training recipes:** This model was released January 2026 and the architecture (Gemma-3 bidirectional) is new. Optimal learning rates, batch sizes, and PEFT configurations for ABSA fine-tuning are not yet documented. Will need empirical validation in Phase 7.
2. **dhvani effectiveness for Hinglish ABSA specifically:** The +1.2% Macro-F1 improvement cited is from sentiment analysis, not ABSA. Performance on BIO tagging with Romanized Hindi needs in-project benchmarking.
3. **Combined ONNX graph export path:** While `optimum-onnx` supports standard architectures, exporting a custom two-headed model requires writing a custom `OnnxConfig` subclass. No published reference exists for this specific pattern — needs validation in Phase 9.
4. **Exact CPU inference latency baseline for XLM-RoBERTa base:** Published benchmarks vary. Actual latency depends on CPU model, ONNX Runtime config, and sequence length distribution. Must be measured empirically in Phase 4.
5. **Railway free tier RAM for ONNX model:** XLM-RoBERTa base ONNX model is ~440MB in FP32. Railway's free tier offers 512MB RAM, which may be insufficient. Quantization to INT8 (~150MB) may be required. Verify during Phase 5.

## Sources

### Primary (HIGH confidence)
- HuggingFace Transformers v5.12.x documentation — XLM-RoBERTa model card, ONNX export guide, token classification tutorial
- `huggingface.co/facebookai/xlm-roberta-base` — model usage stats (16M+ monthly downloads)
- `huggingface.co/ai4bharat/IndicBERT-v3-4B` — model card, curriculum training strategy
- optimum-onnx GitHub (v0.1.0, 2025-12-23) — ONNX export utilities, split from optimum
- onnxruntime PyPI (v1.27.0, 2026-06-15) — version history, Python requirement
- M-ABSA dataset paper (Wu et al., EMNLP 2025) — multilingual ABSA benchmark, 21 languages
- LACA: Cross-lingual ABSA with LLM augmentation (Šmíd et al., ACL 2025) — state-of-the-art methods
- Šmíd & Král (2025) "Cross-lingual aspect-based sentiment analysis: A survey" — Information Fusion Vol 120
- SemEval 2014-2016 Task 4 ABSA datasets — standard benchmark, documented class imbalance ratios
- seqeval PyPI (v1.2.2) — standard for BIO sequence labeling evaluation
- dhvani PyPI + GitHub — Hinglish phonetic normalization
- PyABSA framework documentation — reference ABSA architecture
- GLUECoS benchmark (Khanuja et al.) — evaluation benchmark for code-switched English-Hindi
- FastAPI + Celery Architecture Guide — production async inference patterns

### Secondary (MEDIUM confidence)
- akshar-32k HuggingFace tokenizer — custom Hinglish BPE, niche and unproven at scale
- ABSA-Mix (CSL 2024) — Hinglish ABSA dataset, only publicly available Hinglish resource
- "Hinglish helps users engage with a wider audience..." — ETGovernment, June 2024
- IndicTrans2 documentation — machine translation for data augmentation

### Tertiary (LOW confidence)
- Single combined ONNX graph for two-stage ABSA — no published reference for this specific export pattern. Will need custom implementation and validation.
- IndicBERT-v3-1B optimal hyperparameters for ABSA — model too new for community best practices. Must be empirically determined.

---

*Research completed: 2026-06-22*
*Ready for roadmap: yes*
