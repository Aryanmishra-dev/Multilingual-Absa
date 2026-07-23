# Changelog

## v2.0.0 - Streamlit → HTMX Migration

### Breaking Changes
- Streamlit frontend (`streamlit_app/`) has been removed entirely
- The separate Streamlit server on port 8501 no longer exists
- Plotly dependency removed (replaced by Chart.js for client-side charts)
- Streamlit dependency removed from `requirements.txt`
- Docker Compose file no longer includes the `streamlit` service
- `Dockerfile.streamlit` deleted

### What's New
- HTMX 2.0.3 + Jinja2 frontend served directly by FastAPI
- Alpine.js for reactive UI state management
- Tailwind CSS (Play CDN) for styling
- Chart.js for client-side chart rendering in batch results
- CSRF protection via `itsdangerous` for all HTMX form submissions
- SSE endpoint for live batch progress updates
- Server-Sent Events support via `sse-starlette`
- New dependencies: `sse-starlette`, `itsdangerous`, `pytest-asyncio`

### Notes
- Single server: `uvicorn app.main:app --reload` on port 8000
- JSON API endpoints at `/api/predict`, `/api/batch` are preserved
- Swagger UI at `/docs` is preserved
- All ML model code, Celery workers, DVC/MLflow integration is unchanged
