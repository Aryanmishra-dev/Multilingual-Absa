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

from fastapi.templating import Jinja2Templates

# Resolve relative to this file:
#   api/app/core/templates.py  →  api/app/templates/
_TEMPLATE_DIR: Path = Path(__file__).parent.parent / "templates"

templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))
