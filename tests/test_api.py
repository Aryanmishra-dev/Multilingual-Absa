import pytest
from fastapi.testclient import TestClient
import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
import unittest.mock as mock

from api.main import app
import json
import io

client = TestClient(app)

def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

def test_predict_english():
    with TestClient(app) as client:
        payload = {"text": "The food was great but service was slow.", "language": "en"}
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "en"
        assert "aspects" in data

def test_predict_hindi():
    with TestClient(app) as client:
        payload = {"text": "खाना बहुत अच्छा था", "language": "hi"}
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "hi"
        assert "aspects" in data

def test_predict_empty():
    with TestClient(app) as client:
        payload = {"text": ""}
        response = client.post("/predict", json=payload)
        assert response.status_code == 200

def test_batch_upload():
    with TestClient(app) as client:
        csv_content = "text\nThe food was great\nTerrible service"
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        with mock.patch("api.routers.predict.process_batch.delay") as mock_delay:
            response = client.post("/batch", files=files)
            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data
            assert data["status"] == "queued"
            assert data["total_reviews"] == 2
            mock_delay.assert_called_once()
