import httpx
import streamlit as st
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

class APIClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.client = httpx.Client(base_url=self.base_url, timeout=30.0)
        
    def get_health(self):
        try:
            response = self.client.get("/health")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            st.error(f"API Health Check Failed: {e}")
            return None

    def get_info(self):
        try:
            response = self.client.get("/info")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return None

    def predict(self, text: str, language: str = "auto"):
        try:
            payload = {"text": text, "language": language}
            response = self.client.post("/predict", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            st.error(f"Prediction API Error: {e}")
            return None

    def batch_predict(self, file):
        try:
            files = {"file": (file.name, file, "text/csv")}
            response = self.client.post("/batch", files=files)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            st.error(f"Batch API Error: {e}")
            return None

    def get_batch_status(self, job_id: str):
        try:
            response = self.client.get(f"/status/{job_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return None
