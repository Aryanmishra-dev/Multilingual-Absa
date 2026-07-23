"""
Page routes — Jinja2/HTMX web frontend.

WHY THIS FILE EXISTS
--------------------
All HTML-serving GET routes live here, completely separate from the JSON REST
routes in routes/predict.py and routes/results.py.  This boundary means:

  • REST routes never return HTML accidentally.
  • Page routes never appear in the OpenAPI schema (include_in_schema=False).
  • Future phases add HTMX fragment endpoints alongside these page routes
    without touching any existing API code.

WHAT THIS FILE DOES (Phase 2)
------------------------------
Registers four GET routes that render placeholder Jinja2 templates:
  GET /           → redirect to /predict
  GET /predict    → pages/predict.html
  GET /batch      → pages/batch.html
  GET /monitor    → pages/monitor.html

No business logic.  No inference.  No database queries.
The routes exist only to prove the template rendering infrastructure works.

HTMX fragment endpoints (POST /predict/fragment, GET /batch/progress/{id},
GET /monitor/health-partial) will be added in Phases 3-5.
"""
from __future__ import annotations

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.templates import templates
from app.middleware.csrf import generate_csrf_token
from app.middleware.dependencies import get_db

# include_in_schema=False keeps these HTML routes out of the OpenAPI / Swagger UI.
router = APIRouter(include_in_schema=False)

# ── Navigation structure ───────────────────────────────────────────────────────
# Mirrors the NAV constant in the React Sidebar.jsx so sidebar rendering is
# driven from a single Python list rather than hard-coded in every template.
_NAV_ITEMS: list[dict[str, str]] = [
    {"path": "/predict", "icon": "psychology",   "label": "Predictor"},
    {"path": "/batch",   "icon": "cloud_upload", "label": "Batch Analytics"},
    {"path": "/monitor", "icon": "monitoring",   "label": "System Health"},
]


def _base_ctx(request: Request, page_title: str, **extra: object) -> dict:
    """
    Build the Jinja2 template context that base.html expects.

    Every page renderer calls this so the sidebar and header always receive
    the nav items and the current path (for active-link highlighting).
    Also includes CSRF token for HTMX form submissions.
    """
    from app.middleware.csrf import generate_csrf_token
    return {
        "request":      request,          # required by Jinja2Templates
        "page_title":   page_title,
        "nav_items":    _NAV_ITEMS,
        "current_path": request.url.path,
        "csrf_token":   generate_csrf_token(),
        **extra,
    }


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Root → serve the Predict page (same behaviour as React's Navigate redirect)."""
    return templates.TemplateResponse(
        "pages/predict.html",
        _base_ctx(request, "Live Predictor"),
    )


@router.get("/predict", response_class=HTMLResponse)
async def predict_page(request: Request) -> HTMLResponse:
    """
    Jinja2 Live Predictor page.
    Phase 2: renders the layout shell with a placeholder content block.
    Phase 3: the content block will contain the HTMX predict form + result panel.
    """
    return templates.TemplateResponse(
        "pages/predict.html",
        _base_ctx(request, "Live Predictor"),
    )


@router.get("/batch", response_class=HTMLResponse)
async def batch_page(request: Request) -> HTMLResponse:
    """
    Jinja2 Batch Analytics page.
    Phase 2: placeholder.
    Phase 4: file upload form + progress polling.
    """
    return templates.TemplateResponse(
        "pages/batch.html",
        _base_ctx(request, "Batch Analytics"),
    )


from app.routes.results import health_check

@router.get("/monitor", response_class=HTMLResponse)
async def monitor_page(request: Request) -> HTMLResponse:
    """
    Jinja2 System Monitor page.
    Phase 5: live health status + performance metrics.
    """
    try:
        health = await health_check()
        ctx = _base_ctx(request, "System Monitor", health=health, error=None)
    except Exception:
        ctx = _base_ctx(request, "System Monitor", health=None, error="Service temporarily unavailable")
        
    return templates.TemplateResponse("pages/monitor.html", ctx)
# ── SSE Endpoint for batch progress ──────────────────────────────────────────

import asyncio
import json
from sse_starlette.sse import EventSourceResponse

@router.get("/api/batch/progress/{job_id}")
async def batch_progress_sse(job_id: str, db: Session = Depends(get_db)):
    """
    SSE endpoint for live batch progress updates.
    Clients connect via EventSource and receive progress events every 2 seconds.
    """
    async def event_generator():
        try:
            import re
            if not re.match(r'^[a-fA-F0-9\-]{36}$', job_id):
                yield {"event": "error", "data": json.dumps({"detail": "Invalid job ID"})}
                return

            while True:
                job = await get_batch_status(job_id, db)
                data = {
                    "job_id": job.job_id,
                    "status": job.status,
                    "total_reviews": job.total_reviews,
                    "processed": job.processed,
                    "result_url": job.result_url,
                }
                yield {"event": "progress", "data": json.dumps(data)}

                if job.status in ("completed", "failed"):
                    yield {"event": job.status, "data": json.dumps(data)}
                    break

                await asyncio.sleep(2)
        except Exception:
            yield {"event": "error", "data": json.dumps({"detail": "Failed to fetch job progress"})}

    return EventSourceResponse(event_generator())

# ── Phase 3 HTMX Endpoints ───────────────────────────────────────────────────

from app.schemas.schemas import ReviewInput
from app.routes.predict import predict as predict_json

@router.post("/predict/fragment", response_class=HTMLResponse)
async def predict_fragment(
    request: Request,
    text: str = Form(...),
    language: str = Form("auto"),
    db: Session = Depends(get_db)
) -> HTMLResponse:
    """
    Phase 3: HTMX partial for the Predict page.
    Calls the EXACT SAME prediction logic as the JSON API.
    """
    try:
        if language == "auto":
            language = None
            
        prediction = await predict_json(ReviewInput(text=text, language=language), db)
        return templates.TemplateResponse(
            "partials/predict_result.html",
            {"request": request, "result": prediction, "error": None}
        )
    except Exception:
        return templates.TemplateResponse(
            "partials/predict_result.html",
            {"request": request, "result": None, "error": "Analysis failed. Please try again."}
        )

# ── Phase 4 HTMX Endpoints ───────────────────────────────────────────────────

from fastapi import UploadFile, File
from app.routes.predict import predict_batch, get_batch_status

@router.post("/batch/fragment", response_class=HTMLResponse)
async def batch_fragment(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> HTMLResponse:
    """
    Phase 4: HTMX partial for starting a batch job.
    """
    try:
        response = await predict_batch(file, db)
        return templates.TemplateResponse(
            "partials/batch_progress.html",
            {"request": request, "job": response, "error": None}
        )
    except Exception:
        return templates.TemplateResponse(
            "partials/batch_progress.html",
            {"request": request, "job": None, "error": "Batch processing failed. Please try again."}
        )

@router.get("/batch/progress/{job_id}", response_class=HTMLResponse)
async def batch_progress_fragment(
    request: Request,
    job_id: str,
    db: Session = Depends(get_db)
) -> HTMLResponse:
    """
    Phase 4: HTMX partial for polling batch job status.
    """
    try:
        job = await get_batch_status(job_id, db)
        return templates.TemplateResponse(
            "partials/batch_progress.html",
            {"request": request, "job": job, "error": None}
        )
    except Exception:
        return templates.TemplateResponse(
            "partials/batch_progress.html",
            {"request": request, "job": None, "error": "Failed to retrieve job status."}
        )

# ── Phase 5 HTMX Endpoints ───────────────────────────────────────────────────

@router.get("/monitor/health-partial", response_class=HTMLResponse)
async def monitor_health_fragment(request: Request) -> HTMLResponse:
    """
    Phase 5: HTMX partial for polling the system health status.
    Uses the exact same health logic as the JSON API.
    """
    try:
        health = await health_check()
        return templates.TemplateResponse(
            "partials/monitor_health.html",
            {"request": request, "health": health, "error": None}
        )
    except Exception:
        return templates.TemplateResponse(
            "partials/monitor_health.html",
            {"request": request, "health": None, "error": "Health check failed. Service may be unavailable."}
        )

import pandas as pd
from pathlib import Path
import json

@router.get("/batch/charts/{job_id}", response_class=HTMLResponse)
async def batch_charts_fragment(request: Request, job_id: str) -> HTMLResponse:
    """
    Phase 5.6: HTMX partial for rendering charts.
    Parses the generated CSV and passes JSON directly to the template for Chart.js.
    """
    try:
        file_path = Path(f"data/results/{job_id}.csv")
        if not file_path.exists():
            return templates.TemplateResponse("partials/batch_charts.html", {"request": request, "error": "CSV not found"})

        df = pd.read_csv(file_path)

        lang_pie = []
        if "language" in df.columns:
            counts = df["language"].value_counts().to_dict()
            lang_pie = [{"name": str(k), "value": int(v)} for k, v in counts.items()]

        aspect_heat = []
        if "aspect" in df.columns and "sentiment" in df.columns:
            # Group by aspect and sentiment
            grouped = df.groupby(["aspect", "sentiment"]).size().unstack(fill_value=0)
            for aspect, row in grouped.iterrows():
                if pd.isna(aspect) or not aspect:
                    continue
                aspect_heat.append({
                    "aspect": str(aspect),
                    "positive": int(row.get("positive", 0)),
                    "negative": int(row.get("negative", 0)),
                    "neutral": int(row.get("neutral", 0)),
                    "conflict": int(row.get("conflict", 0))
                })

        sent_line = []
        if "sentiment" in df.columns:
            df_sent = df[df["sentiment"].notna()]
            n = len(df_sent)
            # Create 7 chunks for the line chart
            chunk_size = max(1, n // 7) if n > 0 else 1
            for i in range(7):
                chunk = df_sent.iloc[i*chunk_size : (i+1)*chunk_size]
                if chunk.empty:
                    break
                counts = chunk["sentiment"].value_counts().to_dict()
                sent_line.append({
                    "name": f"Batch {i+1}",
                    "positive": int(counts.get("positive", 0)),
                    "negative": int(counts.get("negative", 0)),
                    "neutral": int(counts.get("neutral", 0)),
                    "conflict": int(counts.get("conflict", 0))
                })

        return templates.TemplateResponse(
            "partials/batch_charts.html",
            {
                "request": request,
                "language_pie": json.dumps(lang_pie),
                "aspect_heatmap": json.dumps(aspect_heat),
                "sentiment_chart": json.dumps(sent_line),
                "error": None
            }
        )
    except Exception:
        return templates.TemplateResponse("partials/batch_charts.html", {"request": request, "error": "An unexpected error occurred while generating charts."})
