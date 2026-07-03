# Stack Research

**Domain:** Multilingual Aspect-Based Sentiment Analysis (ABSA) — English, Hindi, Hinglish
**Researched:** 2026-06-22
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11+ | Runtime language | ONNX Runtime 1.27+ drops Python 3.10 support; PyTorch 2.12+ requires 3.10+. 3.11 is the safe floor for all dependencies. |
| HuggingFace Transformers | 5.12.x | Model loading, tokenization, training loop | The de facto standard. Provides `XLMRobertaForTokenClassification` and `AutoTokenizer` out of the box. v5.x is a major rearchitecture — test thoroughly before upgrading from 4.x. |
| PyTorch | 2.12.x | Deep learning framework | Required by Transformers. v2.12 is latest stable (June 2026). Ships CUDA 13.0 by default. Use `--index-url https://download.pytorch.org/whl/cu126` if on older drivers. |
| XLM-RoBERTa | base (0.3B params) | Multilingual encoder | Pre-trained on 100 languages including Hindi. Strong cross-lingual zero-shot transfer. No `lang` tensor needed — auto-detects language. `FacebookAI/xlm-roberta-base` scores 16M+ downloads/month. Use `xlm-roberta-large` (0.55B) only if Macro-F1 on Hindi/Hinglish is >3 points below English after tuning base. |
| HuggingFace PEFT | 0.19.x | Parameter-efficient fine-tuning (LoRA) | LoRA is the standard for efficient encoder fine-tuning. v0.19 adds GraLoRA and QALoRA. For XLM-RoBERTa base (0.3B), full fine-tuning is feasible on consumer GPUs — **do not default to LoRA for this model size**. Use PEFT only if you need to fine-tune xlm-roberta-large on a single 24GB GPU. |
| Optimum | 1.26.x / latest | ONNX export bridge | Required for ONNX export. `optimum-cli export onnx` handles the conversion with architecture-specific configuration objects. |
| optimum-onnx | 0.1.x | ONNX export + runtime | **Split from Optimum in late 2025.** Contains the actual ONNX export logic and `ORTModelForXXX` classes. Must install separately. |
| ONNX Runtime | 1.27.x | Production inference engine | Runs the exported ONNX model in the API. No PyTorch dependency in production. v1.27 (June 2026) requires Python 3.11+, ONNX 1.21. |
| seqeval | 1.2.2 | Sequence labeling evaluation | The standard for BIO-tagging evaluation (precision, recall, F1 per entity type). Last updated 2020 but stable — no better alternative exists. |
| scikit-learn | 1.9.x | Metrics (Macro-F1, classification_report) | `sklearn.metrics` for overall metrics. v1.9 (June 2026) adds narwhals and GPU support for some estimators. |

### Model Variants

| Model | Params | Best For | When to Use |
|-------|--------|----------|-------------|
| `FacebookAI/xlm-roberta-base` | 0.3B | Primary model for all 3 languages | Default choice. Good cross-lingual transfer. Fine-tunes on 16GB GPU. |
| `FacebookAI/xlm-roberta-large` | 0.55B | Higher accuracy target | Only if base underperforms on Hindi/Hinglish by >3 Macro-F1 points. Needs 24GB+ GPU or PEFT. |
| `ai4bharat/IndicBERT-v3-1B` | 1B | Hindi-focused runs | **Game-changer (Jan 2026):** Bidirectional Gemma-3 based encoder trained on 23 Indic languages + English. Trained with curriculum learning to prevent catastrophic forgetting. Likely beats XLM-R on Hindi/Hinglish specifically. |
| `ai4bharat/IndicBERT-v3-4B` | 4B | Max Hindi accuracy | 4B params — requires PEFT (LoRA). Overkill unless Hindi metrics are the primary concern. |
| `ai4bharat/indic-bert` | ~100M | (AVOID) | Original ALBERT-based IndicBERT. Too small, outdated architecture. **Do not use.** |

**Recommendation:** Start with `xlm-roberta-base`. After the English baseline is solid, swap the backbone to `ai4bharat/IndicBERT-v3-1B` for Hindi/Hinglish-specific runs and compare Macro-F1. The IndicBERT-v3-1B model uses Gemma-3 architecture with bidirectional attention — fundamentally stronger than the old IndicBERT.

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| datasets | 3.x | Data loading, preprocessing, train/test split | Use for loading SemEval 2014, M-ABSA, and custom datasets. Built-in caching and mapping functions. |
| tokenizers | 0.21.x | Fast tokenization | Backs Transformers' `AutoTokenizer`. Needed only if customizing tokenizer for Hinglish. |
| dhvani | 0.2.x | Hinglish phonetic normalization | **Primary tool for code-mixed Hinglish preprocessing.** Normalizes Romanized Hindi spelling variants ("bahut"/"bohot"/"boht" → canonical) using IPA as bridge. 1M+ lexicon, <1ms per word. Pure lookup + rules — no GPU needed. +1.2% Macro-F1 observed on Hindi sentiment. |
| akshar-32k | — | Custom BPE tokenizer for Hinglish | HuggingFace tokenizer trained on 40M tokens of Romanized Hinglish. Use **only if** XLM-RoBERTa's SentencePiece tokenizer fragments Hinglish words badly. Caveat: still struggles with spelling variation — pair with dhvani. |
| accelerate | 1.x | Training utilities | Required by Transformers `Trainer`. Handles device placement, mixed precision, gradient accumulation. |
| bitsandbytes | 0.45.x | 4-bit quantization for QLoRA | Only needed if you insist on QLoRA for xlm-roberta-large. **Not recommended** — XLM-R base fine-tunes fine on 16GB without quantization. |
| wandb | 0.19.x | Experiment logging (alternative to MLflow) | Use **only** if you prefer cloud logging over MLflow's self-hosted tracking. Both can coexist. |
| pydantic | 2.x | API schema validation | Already in project spec. Required for FastAPI request/response models. |
| celery | 5.4.x | Async task queue | For long-running inference jobs. Paired with Redis as broker. |
| redis | 5.x | Celery broker + cache | Required. Use `redis-py` (Python client). |
| psycopg2-binary | 2.9.x | PostgreSQL driver | Required by project spec. |
| sqlalchemy | 2.x | ORM for PostgreSQL | Required by project spec. |

### Development & MLOps Tools

| Tool | Version | Purpose | Notes |
|------|---------|---------|-------|
| MLflow | 3.14.x | Experiment tracking, model registry, metrics logging | Latest (June 2026). v3.x focus is LLM observability but experiment tracking works identically. Log params, metrics, artifacts per training run. **Pin to `mlflow-skinny==3.14.0` for minimal dependencies** on the training side. Use full MLflow for the tracking server. |
| DVC | 3.67.x | Data and model version control | DVC tracks dataset versions and model files outside Git. v3.67.1 latest (Mar 2026). Use `dvc init` at project root, `dvc add data/` to track datasets. |
| Evidently AI | 0.7.x | Model monitoring, data drift detection | v0.7.21 latest (Mar 2026). Use for **data quality monitoring** after deployment — detecting distribution shifts in review text. Not needed during training. |
| Prometheus + Grafana | — | API metrics, request monitoring | Standard for FastAPI production monitoring. Not research-critical — standard setup. |
| Docker | 27.x | Containerization | Required for reproducible deployments. |

### Frontend Stack

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| React | 19.x | UI framework | Standard choice. v19 stable. |
| Vite | 6.x | Build tool | Faster than CRA. Standard for new React projects. |
| Recharts | 2.x | Charting library | Built on D3. Good for confusion matrices, F1 trends, sentiment distributions. |
| TailwindCSS | 4.x | Utility CSS | v4 uses CSS-first config (no tailwind.config.js needed). Faster build times. |

## Installation

```bash
# Core ML stack
pip install torch==2.12.0 --index-url https://download.pytorch.org/whl/cu126
pip install transformers==5.12.1 datasets tokenizers accelerate
pip install peft==0.19.1
pip install optimum optimum-onnx onnxruntime==1.27.0
pip install seqeval==1.2.2 scikit-learn==1.9.0

# Hinglish preprocessing
pip install dhvani==0.2.5

# MLOps
pip install "mlflow-skinny==3.14.0" dvc==3.67.1

# API
pip install "fastapi[standard]" celery[redis] redis psycopg2-binary sqlalchemy pydantic==2

# Dev
pip install wandb black ruff pytest pytest-cov mypy types-python-dateutil

# Frontend
npm install react@19 react-dom@19 recharts@2
npm install -D vite@6 tailwindcss@4
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| XLM-RoBERTa base | mBERT (BERT-base-multilingual-cased) | mBERT is smaller (0.18B vs 0.3B). Use **only** if inference latency is critical and you can accept 2-5 point F1 drop. XLM-RoBERTa is stronger on code-mixed and low-resource languages. |
| XLM-RoBERTa base | IndicBERT-v3-1B | Use IndicBERT-v3-1B when you pivot to Hindi/Hinglish-only evaluation. Its curriculum training (English → Indic) prevents catastrophic forgetting better than XLM-R's generic multilingual pretraining. |
| LoRA for large models | QLoRA (4-bit) | QLoRA only needed for xlm-roberta-large on a 16GB GPU. For base models, full fine-tuning is simpler and more accurate. |
| optimum-onnx export | torch.onnx.export (manual) | Manual `torch.onnx.export` gives finer control over dynamic axes and opset version. Use **only** if optimum's config doesn't support XLM-RoBERTa's architecture (unlikely — it's well-supported). |
| seqeval | evaluate (HuggingFace) | HuggingFace's `evaluate` library wraps seqeval. Use `evaluate` if you want a unified metrics API. Either works — seqeval is the underlying engine. |
| MLflow | wandb | MLflow is self-hosted (data stays private), wandb is SaaS with a free tier. Use wandb if you prefer cloud dashboards. This project spec already requires MLflow. |
| DVC | Git LFS | DVC is more flexible (any cloud storage as remote) and integrates with ML pipelines. Git LFS is simpler but doesn't handle dataset versioning workflows as well. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Original `ai4bharat/indic-bert` | ALBERT-based, ~100M params, outdated (2020). Significantly weaker than XLM-R or IndicBERT-v3. | `ai4bharat/IndicBERT-v3-1B` or `FacebookAI/xlm-roberta-base` |
| `ai4bharat/IndicBERTv2-*` | ALBERT-based, still inferior to XLM-R. v2 (2023) is better than v1 but v3 (Jan 2026) is a completely new architecture (Gemma-3). | `ai4bharat/IndicBERT-v3-1B` |
| Older `optimum` ONNX path (optimum<1.15) | ONNX export was split to `optimum-onnx` in late 2025. Early 2025 versions may have path resolution bugs. | `optimum-onnx>=0.1.0` |
| `bert-base-multilingual-cased` (mBERT) | Weaker cross-lingual transfer than XLM-RoBERTa. Trained on Wikipedia only (vs CommonCrawl for XLM-R). | `FacebookAI/xlm-roberta-base` |
| PyABSA as a dependency | PyABSA is a full framework that abstracts away the training loop. This project is building from scratch for learning + custom ONNX export. Using PyABSA would hide the architecture decisions. | Build custom pipeline: Transformers `Trainer` + custom model class |
| IndicTrans2 for Hinglish → Hindi | Translating Hinglish to Hindi removes the code-mixed signal. Romanized Hindi + English mixed text is the actual distribution. Translating loses information. | `dhvani` normalization (keeps English, normalizes Romanized Hindi spellings) |
| SentencePiece from scratch for Hinglish | XLM-RoBERTa's tokenizer already handles multilingual text adequately. Training a custom SentencePiece is expensive and rarely improves F1 by >1 point. | `dhvani` normalization + XLM-RoBERTa tokenizer. Only reach for `akshar-32k` if word fragmentation is severe. |

## ABSA Architecture Choices

### Stage 1: Aspect Term Extraction
- **Approach:** Token classification with BIO tagging (B-Aspect, I-Aspect, O)
- **Model head:** `XLMRobertaForTokenClassification` with 3 output labels
- **Context:** Standard approach in all cross-lingual ABSA literature (2025 survey: Smíd et al.)

### Stage 2: Aspect Sentiment Classification
- **Approach:** Extract each aspect span's pooled embedding → classify into {Positive, Negative, Neutral, Conflict}
- **Model head:** Linear classifier on top of pooled aspect span representations
- **Alternative (merged):** Single token classification head with merged labels (e.g., `B-ASP-Positive`, `I-ASP-Negative`, `O`) as demonstrated by `yangheng/deberta-v3-base-end2end-absa`
- **Recommendation for this project:** Use **separate heads on a shared encoder** for Stage 1 and Stage 2, compiled into a single ONNX graph. This allows different optimization for each task while sharing the multilingual encoder. The merged-label approach is simpler but couples the two tasks rigidly.

### ONNX Export Strategy
1. Export the full model (XLMRoBERTa backbone + token classification head + sentiment head) as a single ONNX graph
2. Use `optimum-cli export onnx` with a custom `OnnxConfig` subclass
3. Set dynamic axes for `input_ids` and `attention_mask` (variable-length inputs)
4. Validate with ONNX Runtime — output tensors must match PyTorch output within `atol=1e-4`

## Hinglish Preprocessing Pipeline

```
Raw Hinglish text → dhvani.phonetic_normalize() → XLM-RoBERTa tokenizer → model
```

**Why dhvani for Hinglish:**
- XLM-RoBERTa's SentencePiece tokenizer was trained on clean text. Hinglish has extreme spelling variation ("kaise" / "kese" / "kayse").
- dhvani normalizes all Romanized Hindi variants to a canonical IPA-based form **without** transliterating to Devanagari — preserving the Roman-script input that the model was fine-tuned on.
- English words pass through untouched.
- <1ms per word — negligible latency cost.

**Only if dhvani is insufficient:**
- Add `akshar-32k` tokenizer as a pre-tokenization step. But benchmark first — it may not improve F1 over using XLM-R's tokenizer directly after dhvani normalization.

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| transformers 5.x | PyTorch 2.10+ | v5.x is a major restructure. `Trainer`, `AutoModel`, and pipeline APIs are backward-compatible but some internals changed. Pin carefully. |
| optimum-onnx 0.1.x | optimum 1.26+, transformers 5.x | Split from optimum. Must install both. |
| onnxruntime 1.27.x | Python 3.11+ | Python 3.10 wheels no longer published. |
| PEFT 0.19.x | transformers 5.x, accelerate 1.x | Check `get_peft_model` compatibility with XLMRobertaForTokenClassification. |
| dhvani 0.2.x | Python 3.10+ | No external model dependencies. Pure Python. |
| MLflow 3.14.x | Python 3.10+ | `mlflow-skinny` for minimal deps, `mlflow[extras]` for full. |
| DVC 3.67.x | Python 3.10+ | Works with any Git remote. |

## Sources

- HuggingFace Transformers docs (v5.12.1) — XLM-RoBERTa model card, export guide, token classification tutorial — HIGH confidence
- `huggingface.co/facebookai/xlm-roberta-base` — 16M+ monthly downloads, confirmed active — HIGH confidence
- `huggingface.co/ai4bharat/IndicBERT-v3-4B` — IndicBERT v3 model card, curriculum training strategy — HIGH confidence
- PEFT GitHub releases (v0.19.0, 2026-04-14) — feature list, LoRA/QLoRA/GraLoRA support — HIGH confidence
- optimum-onnx GitHub (v0.1.0, 2025-12-23) — split from optimum, export CLI — HIGH confidence
- onnxruntime PyPI (v1.27.0, 2026-06-15) — version history, Python requirement — HIGH confidence
- seqeval PyPI (v1.2.2, latest) — stable, last updated 2020 — MEDIUM confidence (no updates needed but inactive)
- dhvani PyPI + GitHub — Hinglish normalization documentation — HIGH confidence
- akshar-32k HuggingFace — custom Hinglish BPE tokenizer — MEDIUM confidence (niche, unproven at scale)
- Cross-lingual ABSA survey (Smíd et al., 2025) — token-classification paradigm for ATE, pipeline for compound tasks — HIGH confidence
- M-ABSA dataset paper (Wu et al., EMNLP 2025) — multilingual ABSA benchmark, 21 languages — HIGH confidence
- LACA: Cross-lingual ABSA with LLM augmentation (Šmíd et al., ACL 2025) — state-of-the-art cross-lingual methods — HIGH confidence

---

*Stack research for: Multilingual ABSA (English, Hindi, Hinglish)*
*Researched: 2026-06-22*
*Confidence: HIGH — all versions verified against official package registries and documentation*
