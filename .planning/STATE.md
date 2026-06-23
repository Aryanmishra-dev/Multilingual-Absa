# STATE: Multilingual ABSA

**Last updated:** 2026-06-22

## Project Reference

**Core Value:** Accurately extract aspect terms and their sentiment from product reviews across English, Hindi, and Hinglish — enabling brands to understand what customers feel about specific product features in the languages their users actually write in.

**Current Focus:** Phase 1 (Project Scaffolding & Data Pipeline) — building folder structure, dependency management, dataset download, and DVC tracking.

## Current Position

| Field | Value |
|-------|-------|
| Current Phase | Phase 1 |
| Current Plan | — (direct execution) |
| Phase Status | Executing |
| Plans Complete | 0/0 |

```
Progress: [████      ] 40% — Phase 1 executing
```

## Performance Metrics

(No performance metrics yet — first phase not started.)

## Accumulated Context

### Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| XLM-RoBERTa as primary model | Multilingual by design, strong cross-lingual transfer | — Pending |
| ONNX for inference | Production-safe, no PyTorch dependency in API | — Pending |
| Macro-F1 as primary metric | Standard for imbalanced ABSA tasks | — Pending |
| Separate ONNX models for v1 | Combined graph has dynamic-axis export pitfalls | — Pending |
| Skip Celery for v1 | Thread-pool sufficient for single-review inference; Celery adds latency overhead | — Pending |

### Open Todos

- None yet

### Blockers

- None

## Session Continuity

**Session purpose:** Initial project roadmap creation
**ROADMAP.md written:** Yes (6 phases, 36/36 v1 requirements mapped)
**Milestone:** 1 (initial build)
**Next action:** Plan Phase 1 details via `/gsd-plan-phase 1`

---

*STATE.md is updated at phase transitions, plan creation, and plan completion.*
