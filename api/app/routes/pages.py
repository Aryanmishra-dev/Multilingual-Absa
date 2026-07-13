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

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from api.app.core.templates import templates

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
    """
    return {
        "request":      request,          # required by Jinja2Templates
        "page_title":   page_title,
        "nav_items":    _NAV_ITEMS,
        "current_path": request.url.path,
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


@router.get("/monitor", response_class=HTMLResponse)
async def monitor_page(request: Request) -> HTMLResponse:
    """
    Jinja2 System Monitor page.
    Phase 2: placeholder.
    Phase 5: live health status + performance metrics.
    """
    return templates.TemplateResponse(
        "pages/monitor.html",
        _base_ctx(request, "System Monitor"),
    )

# ── Phase 3 HTMX Endpoints ───────────────────────────────────────────────────

from fastapi import Depends, Form
from sqlalchemy.orm import Session
from api.app.middleware.dependencies import get_db
from api.app.schemas.schemas import ReviewInput
from api.app.routes.predict import predict as predict_json

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
    except Exception as e:
        return templates.TemplateResponse(
            "partials/predict_result.html",
            {"request": request, "result": None, "error": str(e)}
        )
