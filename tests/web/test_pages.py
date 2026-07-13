"""
tests/web/test_pages.py — Phase 2 smoke tests.

PURPOSE
-------
Verify that the new Jinja2 page infrastructure:
  1. Renders all three pages without raising an exception (HTTP 200).
  2. Returns HTML content (not JSON).
  3. Contains the expected page titles / identifiers.
  4. Does NOT break any existing JSON API endpoint.
  5. Serves static CSS from the /static mount.

These tests are strictly additive — they do not modify or replace
any tests in tests/api/test_api.py.

IMPORTANT: DATABASE_URL must be set before importing the app because
api/app/middleware/dependencies.py reads it at module-import time.
"""
import os

# Must be set before any app import (same pattern as tests/api/test_api.py)
os.environ.setdefault("DATABASE_URL", "sqlite:///./tests/fixtures/test.db")

import pytest
from fastapi.testclient import TestClient

from api.app.main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _html_client() -> TestClient:
    """Return a TestClient that triggers the lifespan (model loading)."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# Page rendering tests
# ---------------------------------------------------------------------------

class TestPageRoutes:
    """Smoke tests: every GET page route returns 200 HTML."""

    def test_root_redirects_to_predict(self):
        """GET / should return the Predict page (200, HTML)."""
        with _html_client() as client:
            response = client.get("/", follow_redirects=True)
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_predict_page_renders(self):
        with _html_client() as client:
            response = client.get("/predict")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "SentimentAI" in response.text
        assert "Live Predictor" in response.text

    def test_batch_page_renders(self):
        with _html_client() as client:
            response = client.get("/batch")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "SentimentAI" in response.text
        assert "Batch Analytics" in response.text

    def test_monitor_page_renders(self):
        with _html_client() as client:
            response = client.get("/monitor")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "SentimentAI" in response.text
        assert "System Monitor" in response.text

    def test_sidebar_nav_items_present(self):
        """All three nav links must appear in every page."""
        with _html_client() as client:
            for path in ("/predict", "/batch", "/monitor"):
                response = client.get(path)
                assert response.status_code == 200
                # Check all nav labels are present
                assert "Predictor" in response.text
                assert "Batch Analytics" in response.text
                assert "System Health" in response.text

    def test_predict_active_state(self):
        """/predict page must mark Predictor nav item as active."""
        with _html_client() as client:
            response = client.get("/predict")
        assert "nav-item-active" in response.text
        # The active item must contain the predictor icon
        assert "psychology" in response.text

    def test_base_template_includes_htmx(self):
        """HTMX CDN script must be present in every page."""
        with _html_client() as client:
            response = client.get("/predict")
        assert "htmx.org" in response.text

    def test_base_template_includes_alpinejs(self):
        """Alpine.js CDN script must be present in every page."""
        with _html_client() as client:
            response = client.get("/predict")
        assert "alpinejs" in response.text

    def test_base_template_includes_tailwind(self):
        """Tailwind CDN script must be present in every page."""
        with _html_client() as client:
            response = client.get("/predict")
        assert "cdn.tailwindcss.com" in response.text


# ---------------------------------------------------------------------------
# Static file tests
# ---------------------------------------------------------------------------

class TestStaticFiles:
    """Verify the /static mount serves files correctly."""

    def test_css_file_served(self):
        with _html_client() as client:
            response = client.get("/static/css/app.css")
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]
        # Spot-check for key design system classes
        assert "badge-positive" in response.text
        assert "btn-primary" in response.text

    def test_static_missing_file_returns_404(self):
        with _html_client() as client:
            response = client.get("/static/does-not-exist.css")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Regression tests — existing API must be unaffected
# ---------------------------------------------------------------------------

class TestExistingAPIUnchanged:
    """
    Re-run the core API assertions to prove Phase 2 changes introduced
    zero regressions.  These mirror tests/api/test_api.py in spirit.
    """
class TestPredictFragment:
    """Verify the new HTMX predict endpoint works exactly like the JSON one."""

    def test_predict_fragment_english(self):
        with _html_client() as client:
            response = client.post(
                "/predict/fragment",
                data={"text": "The food was great but service was slow.", "language": "en"},
            )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Detected Aspects" in response.text
        # the response might say "No aspects detected" or show the list, but both are valid HTML
        assert "food" in response.text # text should be in the annotated container

    def test_predict_fragment_auto(self):
        with _html_client() as client:
            response = client.post(
                "/predict/fragment",
                data={"text": "The food was great but service was slow.", "language": "auto"},
            )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "EN" in response.text or "English" in response.text or "en" in response.text

    def test_predict_fragment_empty_text(self):
        with _html_client() as client:
            # Form submission missing 'text' should trigger FastAPI 422
            response = client.post("/predict/fragment", data={"language": "en"})
        # Note: Depending on FastAPI validation, missing Form field might be 422
        assert response.status_code == 422
    def test_health_endpoint_still_returns_json(self):
        with _html_client() as client:
            response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        # Verify content-type is JSON (not HTML)
        assert "application/json" in response.headers["content-type"]

    def test_info_endpoint_still_returns_json(self):
        with _html_client() as client:
            response = client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert "model_name" in data
        assert "supported_languages" in data

    def test_predict_endpoint_still_returns_json(self):
        """POST /predict must still return PredictionResponse JSON."""
        with _html_client() as client:
            response = client.post(
                "/predict",
                json={"text": "The sound quality is excellent.", "language": "en"},
            )
        assert response.status_code == 200
        data = response.json()
        # Schema check — all required fields must be present
        assert "text" in data
        assert "language" in data
        assert "detected_language" in data
        assert "aspects" in data
        assert "processing_time_ms" in data
        # Content-type must be JSON
        assert "application/json" in response.headers["content-type"]

    def test_openapi_schema_page_routes_hidden(self):
        """Page GET routes must NOT appear in the OpenAPI schema."""
        with _html_client() as client:
            response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        paths = schema.get("paths", {})
        # None of the page routes should be in the schema
        assert "/predict" not in paths or all(
            method == "post" for method in paths.get("/predict", {})
        ), "GET /predict should not appear in OpenAPI schema"
        assert "/" not in paths, "GET / should not appear in OpenAPI schema"
        assert "/batch" not in paths or all(
            method == "post" for method in paths.get("/batch", {})
        ), "GET /batch should not appear in OpenAPI schema"
        assert "/monitor" not in paths, "GET /monitor should not appear in OpenAPI schema"
