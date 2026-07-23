"""
Centralized Jinja2Templates instance.

Kept in api/app/core/ so every page-rendering router imports from one place,
avoiding multiple conflicting Template objects pointing at the same directory.

WHY THIS FILE EXISTS
--------------------
FastAPI's Jinja2Templates must be initialised with a directory path.
Centralising it here means that when Phase 3-5 routers add fragment endpoints
they import `templates` from here — no duplication, no divergence.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

# Resolve relative to this file:
#   api/app/core/templates.py  →  api/app/templates/
_TEMPLATE_DIR: Path = Path(__file__).parent.parent / "templates"

templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))


# ── Global template context processor ─────────────────────────────────────────
# Ensures every template rendered via this instance always has access to
# csrf_token — even partial/fragment templates that don't go through _base_ctx.

def _csrf_processor(request: Request) -> dict:  # type: ignore[no-redef]
    from app.middleware.csrf import generate_csrf_token
    return {"csrf_token": generate_csrf_token()}


templates.context_processors.append(_csrf_processor)  # type: ignore[arg-type]
