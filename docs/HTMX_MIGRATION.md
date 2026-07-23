# HTMX Migration

## Summary

The Streamlit frontend (`streamlit_app/`) has been fully replaced with an HTMX + Jinja2 frontend served directly by the FastAPI backend. This eliminates the separate Streamlit server, reduces resource usage, and provides a single unified server for both UI and API.

## What Changed

| Before | After |
|--------|-------|
| Streamlit frontend at `streamlit_app/` | HTMX + Jinja2 at `api/app/templates/` |
| Two servers: FastAPI (8000) + Streamlit (8501) | Single FastAPI server (8000) |
| `streamlit run streamlit_app/Home.py` | `uvicorn app.main:app --reload` |
| Plotly for charts | Chart.js (client-side rendering) |
| Streamlit state management | Alpine.js + HTMX for interactivity |

## Architecture

```
User Browser
    ↕ HTMX / Alpine.js
FastAPI (port 8000)
    ├── /predict          → Predict page (HTML via Jinja2)
    ├── /batch             → Batch upload page (HTML)
    ├── /monitor           → System monitor page (HTML)
    ├── /docs              → Swagger UI (unchanged)
    ├── /api/predict       → JSON API (unchanged)
    ├── /api/batch         → JSON API (unchanged)
    ├── /predict/fragment  → HTMX fragment (HTML partial)
    ├── /batch/fragment    → HTMX fragment (HTML partial)
    └── /api/batch/progress/{job_id} → SSE endpoint
```

## Frontend Stack

- **HTMX 2.0.3** - AJAX, CSS transitions, WebSocket/SSE
- **Alpine.js 3.14** - Reactive UI state (toasts, sidebar)
- **Tailwind CSS (Play CDN)** - Utility-first CSS
- **Chart.js** - Client-side charts (batch results)
- **Material Symbols** - Icon font
- **itsdangerous** - CSRF protection

## CSRF Protection

All HTMX form endpoints require a CSRF token. The token is:
- Set as an `HttpOnly` cookie on every GET response
- Injected into `<meta name="csrf-token">` in `base.html`
- Automatically attached to HTMX requests via `htmx:configRequest` event handler
- Validated by `CSRFMiddleware` for all non-GET, non-API requests

## File Structure

```
api/app/
├── templates/
│   ├── base.html              # Base layout with nav, sidebar, toast system
│   ├── pages/
│   │   ├── predict.html       # Single review prediction form
│   │   ├── batch.html         # CSV upload + progress + results
│   │   └── monitor.html       # Health stats + performance metrics
│   ├── partials/
│   │   ├── predict_result.html     # Prediction result card
│   │   ├── batch_progress.html     # Batch job progress bar
│   │   ├── batch_charts.html       # Chart.js charts
│   │   └── monitor_health.html     # Health status chip
│   └── macros/
│       └── ui.html            # Reusable components (badges, icons, etc.)
├── static/
│   └── css/
│       └── app.css            # Design system components
├── core/
│   └── templates.py           # Centralized Jinja2Templates instance
├── middleware/
│   └── csrf.py                # CSRF protection middleware
└── main.py                    # FastAPI app entry point
```

## Deleted Files

- `streamlit_app/` (entire directory)
- `config/docker/Dockerfile.streamlit`
- Streamlit service in `config/docker/docker-compose.yml`
- Streamlit dependency from `requirements.txt`
- Plotly dependency from `requirements.txt`

## Verification

- All page routes return HTML at `/predict`, `/batch`, `/monitor`
- JSON API endpoints remain at `/api/predict`, `/api/batch`
- Swagger UI at `/docs` is unchanged
- HTMX endpoints return HTML fragments (no page reload)
- SSE endpoint for live batch progress at `/api/batch/progress/{job_id}`
