# Multilingual ABSA

## What This Is

Aspect-based sentiment analysis (ABSA) system that extracts aspect terms and classifies their sentiment from multilingual product reviews. Supports English, Hindi, and Hinglish (code-mixed) — fine-tuned on XLM-RoBERTa with an ONNX-exported inference pipeline, served via FastAPI with a React dashboard.

## Core Value

Accurately extract aspect terms and their sentiment from product reviews across English, Hindi, and Hinglish — enabling brands to understand what customers feel about specific product features in the languages their users actually write in.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Project scaffold with folder structure, DVC, and tooling
- [ ] Data pipeline for SemEval 2014 ABSA dataset (English) + multilingual equivalents
- [ ] Aspect term extraction model (token classification, BIO tagging)
- [ ] Per-aspect sentiment classification (positive/negative/neutral/conflict)
- [ ] Combined ONNX inference graph for both stages
- [ ] FastAPI inference API with Celery + Redis
- [ ] React dashboard with Recharts visualizations
- [ ] MLflow experiment tracking for all training runs
- [ ] Docker compose for local development
- [ ] Railway/Vercel deployment config

### Out of Scope

- Real-time streaming inference — batch/on-demand only for v1
- Mobile app — web dashboard only
- Languages beyond English/Hindi/Hinglish — defer to v2
- Voice/audio reviews — text-only input

## Context

- Built from scratch as an NLP research + engineering project
- Uses state-of-the-art multilingual transformers (XLM-RoBERTa)
- ONNX export required for production inference (no PyTorch in prod)
- Evaluation-driven: Macro-F1 is the primary metric, not accuracy
- Dataset versions tracked with DVC

## Constraints

- **Model**: XLM-RoBERTa base (primary), IndicBERT for Hindi-focused runs
- **Export**: ONNX required before any model reaches the API
- **Metric**: Macro-F1 is the evaluation standard (not accuracy)
- **Stack**: FastAPI + Celery + Redis + PostgreSQL backend; React + Vite + Recharts frontend

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| XLM-RoBERTa as primary model | Multilingual by design, strong cross-lingual transfer | — Pending |
| ONNX for inference | Production-safe, no PyTorch dependency in API | — Pending |
| Macro-F1 as primary metric | Standard for imbalanced ABSA tasks | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-22 after initialization*
