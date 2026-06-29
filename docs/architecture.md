# Multilingual ABSA — Architecture Document

## System Overview

Multilingual ABSA is a production-ready Aspect-Based Sentiment Analysis system supporting English, Hindi, and Hinglish. It extracts aspect terms from product reviews and classifies their sentiment using a dual-engine architecture: INT8-quantized ONNX models for production inference with a zero-download rule-based fallback.

## High-Level Architecture

```mermaid
graph TB
    Client[Client Browser / API Consumer]
    Vercel[Vercel CDN]
    Nginx[Nginx Reverse Proxy]
    API[FastAPI Server]
    Pipeline[ABSA Pipeline]
    Lang[Language Detection]
    Neural[ONNX Neural Engine<br/>INT8 Quantized]
    Fallback[Rule-Based Engine<br/>140+ Aspect Keywords]
    Celery[Celery Worker]
    Redis[(Redis)]
    PG[(PostgreSQL)]
    Prom[Prometheus]
    Graf[Grafana]
    MLflow[(MLflow<br/>Experiment Tracking)]

    Client --> Vercel
    Vercel --> Nginx
    Nginx --> API
    API --> Pipeline
    Pipeline --> Lang
    Pipeline --> Neural
    Pipeline --> Fallback
    API --> Celery
    Celery --> Redis
    API --> PG
    Prom -->|scrape /metrics| API
    Graf --> Prom
    MLflow --> Pipeline
```

## Component Architecture

```mermaid
graph LR
    subgraph "Presentation Layer"
        SPA[React SPA]
        T_TAIL[TailwindCSS Theme]
        RECH[Recharts Visualizations]
        RQ[React Query]
    end
    subgraph "API Layer"
        FAST[FastAPI]
        CORS[CORS Middleware]
        PROM[Prometheus Metrics]
        PYD[Pydantic Schemas]
    end
    subgraph "Service Layer"
        ABSA[ABSAPipeline]
        LANG[LanguageService]
        CEL[Celery Tasks]
    end
    subgraph "Data Layer"
        SQLA[SQLAlchemy ORM]
        PG[(PostgreSQL)]
        RED[(Redis)]
    end
    subgraph "ML Layer"
        ONNX_A[ORTModelFor<br/>TokenClassification]
        ONNX_S[ORTModelFor<br/>SequenceClassification]
        LEXICON[Aspect/Sentiment<br/>Lexicons]
    end
    subgraph "MLOps Layer"
        MLF[MLflow Tracking]
        DVC[DVC Versioning]
        EVI[Evidently Drift]
    end

    SPA --> FAST
    FAST --> CORS
    FAST --> PROM
    FAST --> PYD
    FAST --> ABSA
    FAST --> CEL
    ABSA --> LANG
    ABSA --> ONNX_A
    ABSA --> ONNX_S
    ABSA --> LEXICON
    CEL --> RED
    FAST --> SQLA
    SQLA --> PG
    ABSA --> MLF
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Docker Compose (Local)"
        DC_API[API Service<br/>uvicorn:8000]
        DC_WORKER[Celery Worker]
        DC_DASH[Dashboard<br/>Nginx:80]
        DC_PG[PostgreSQL:5432]
        DC_REDIS[Redis:6379]
        DC_PROM[Prometheus:9090]
        DC_GRAF[Grafana:3001]
    end
    subgraph "Railway (Production)"
        RW_API[API Service<br/>$PORT]
        RW_WORKER[Celery Worker]
        RW_PG[PostgreSQL]
        RW_REDIS[Redis]
    end
    subgraph "Vercel (Production)"
        VC_DASH[React SPA]
        VC_RW_ROUTE[rewrite /api/* -> Railway]
    end

    DC_DASH --> DC_API
    DC_API --> DC_PG
    DC_API --> DC_REDIS
    DC_WORKER --> DC_REDIS
    DC_WORKER --> DC_PG
    DC_PROM -->|scrape| DC_API
    DC_GRAF --> DC_PROM

    VC_DASH --> VC_RW_ROUTE
    VC_RW_ROUTE --> RW_API
    RW_API --> RW_PG
    RW_API --> RW_REDIS
    RW_WORKER --> RW_REDIS
```

## ML Pipeline Architecture

```mermaid
graph TB
    subgraph "Data Ingestion"
        RAW[Raw Data<br/>SemEval 2014<br/>Amazon Hindi]
        FAST[f astText LID<br/>lid.176.ftz]
    end
    subgraph "Preprocessing"
        CLEAN[Text Cleaning<br/>Lowercase, URLs, Mentions]
        TRANS[Transliteration<br/>Devanagari→Roman]
        LANG_DET[Language Detection<br/>EN / HI / Hinglish]
        BIO[BIO Tagging<br/>B-ASP / I-ASP / O]
        TOK[XLM-R Tokenizer<br/>SentencePiece 128 tokens]
    end
    subgraph "Training"
        ATE[Aspect Extraction<br/>Token Classification<br/>3 labels]
        ASC[Sentiment Classification<br/>Sequence Classification<br/>4 labels]
        BASELINE[Baseline<br/>TF-IDF + LR]
        QLORA[QLoRA<br/>4-bit + LoRA]
        JOINT[Joint ABSA<br/>Shared Encoder<br/>2 Heads]
    end
    subgraph "Optimization"
        ONNX_EXP[ONNX Export<br/>optimum-onnx]
        QUANT[INT8 Quantization<br/>Dynamic]
    end
    subgraph "Production"
        INFERENCE[Dual-Engine<br/>Inference]
        BATCH[Batch Processing<br/>Celery Worker]
    end
    subgraph "Evaluation"
        EVAL_METRICS[Macro-F1<br/>Per-class F1<br/>Confusion Matrix]
        LATENCY[Latency Benchmark<br/>P95 < 300ms]
        CROSS[Cross-Lingual Eval<br/>EN→HI Zero-Shot]
    end

    RAW --> CLEAN
    FAST --> LANG_DET
    CLEAN --> LANG_DET
    LANG_DET --> TRANS
    TRANS --> TOK
    TOK --> ATE
    TOK --> ASC
    BIO --> ATE
    ATE --> JOINT
    ASC --> JOINT
    ATE --> ONNX_EXP
    ASC --> ONNX_EXP
    ONNX_EXP --> QUANT
    QUANT --> INFERENCE
    INFERENCE --> BATCH
    ATE --> EVAL_METRICS
    ASC --> EVAL_METRICS
    BASELINE --> EVAL_METRICS
    INFERENCE --> LATENCY
    JOINT --> CROSS
```

## Data Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant F as FastAPI
    participant P as ABSAPipeline
    participant L as LangService
    participant N as ONNX Runtime
    participant R as Rule Engine
    participant D as PostgreSQL
    participant M as Prometheus

    C->>F: POST /predict {text, language?}
    F->>P: pipeline.predict(text, lang)
    P->>L: detect_language(text)
    L-->>P: "en" | "hi" | "hinglish"
    alt ONNX Models Available
        P->>N: Tokenize text
        N-->>P: Token IDs + Attention Mask
        P->>N: ORTModelForTokenClassification
        N-->>P: BIO Logits → Argmax → Spans
        P->>N: Per-aspect ORTModelForSequenceClassification
        N-->>P: Sentiment Logits → Softmax
    else Rule-Based Fallback
        P->>R: _extract_aspects(text)
        R-->>P: [(aspect, start, end)]
        P->>R: _score_sentence(context)
        R-->>P: (pos_score, neg_score)
        P->>R: _score_to_label(pos, neg)
        R-->>P: (sentiment, confidence)
    end
    P-->>F: PredictionResponse
    F->>D: INSERT Review + AspectResults
    D-->>F: IDs
    F-->>C: JSON Response
    F->>M: Record latency + status
```

## Infrastructure

```mermaid
graph TB
    subgraph "Edge"
        DNS[DNS: Vercel]
        SSL[TLS Termination]
    end
    subgraph "Frontend Hosting"
        FE[Vercel<br/>Static SPA]
        FE_CDN[Global CDN]
    end
    subgraph "Backend Hosting"
        BE[Railway<br/>Docker Container]
        HEALTH[Health Check<br/>/health]
        AUTO[Auto-Restart<br/>On Failure]
    end
    subgraph "Data Services"
        PG[PostgreSQL<br/>Railway Managed]
        RD[Redis<br/>Railway Managed]
    end
    subgraph "Observability"
        PROM[Prometheus<br/>15-day Retention]
        GRAF[Grafana<br/>Pre-provisioned Dashboard]
        MLFLOW[MLflow<br/>SQLite Backend]
    end

    DNS --> SSL
    SSL --> FE
    FE --> FE_CDN
    FE_CDN --> BE
    BE --> HEALTH
    BE --> AUTO
    BE --> PG
    BE --> RD
    PROM -->|scrape| BE
    GRAF --> PROM
```

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Separate ONNX models** for ATE and ASC | Combined graph has dynamic-axis export fragility in optimum-onnx |
| **Rule-based fallback** with no downloads | Zero startup time, works offline, graceful degradation |
| **Lexicon-based sentiment** with negation handling | 3-word window for "not good" → negative reversal |
| **XLM-RoBERTa base** (not large) | 0.3B params fine-tunes on 16GB GPU, adequate cross-lingual transfer |
| **ONNX INT8 dynamic quantization** | 4x smaller, 4.6x faster than PyTorch with only 1% F1 drop |
| **SQLite for dev, PostgreSQL for prod** | Zero-config local dev, production-grade concurrency |
| **Celery for batch only** | Single-review inference is fast enough for synchronous response |
| **Mock data in dashboard charts** | Decoupled frontend/backend development; real integration deferred |
