# API Documentation — Multilingual ABSA

## Base URL

- Local development: `http://localhost:8000`
- Production: `https://your-railway-app.up.railway.app`

## Authentication

Currently **none**. All endpoints are publicly accessible.

## Endpoints

### POST /predict

Analyze a single review for aspect-based sentiment.

**Request Body:**
```json
{
  "text": "The food was great but the service was terrible.",
  "language": "en"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Review text to analyze |
| `language` | string | No | Force language (`"en"`, `"hi"`, `"hinglish"`). Auto-detected if omitted |

**Response `200`:**

```json
{
  "text": "The food was great but the service was terrible.",
  "language": "en",
  "detected_language": "en",
  "aspects": [
    {
      "aspect": "Food",
      "sentiment": "positive",
      "confidence": 0.85,
      "start": 4,
      "end": 8
    },
    {
      "aspect": "Service",
      "sentiment": "negative",
      "confidence": 0.82,
      "start": 27,
      "end": 34
    }
  ],
  "processing_time_ms": 185.3
}
```

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Original input text |
| `language` | string | Language used (detected or forced) |
| `detected_language` | string | Auto-detected language code |
| `aspects` | array | List of extracted aspect-sentiment pairs |
| `processing_time_ms` | float | Total inference time in milliseconds |

**Aspect Object:**

| Field | Type | Description |
|-------|------|-------------|
| `aspect` | string | Extracted aspect term (title-cased) |
| `sentiment` | string | `"positive"`, `"negative"`, `"neutral"`, or `"conflict"` |
| `confidence` | float | Confidence score (0.0–1.0) |
| `start` | int | Character offset start in original text |
| `end` | int | Character offset end in original text |

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 422 | Empty text, missing `text` field |
| 500 | Model inference failure |

---

### POST /batch

Upload a CSV file for batch analysis. Processed asynchronously via Celery.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | CSV file with a `text` column (max 10,000 rows) |

**Response `200`:**

```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "queued",
  "total_reviews": 4250,
  "processed": 0,
  "result_url": null
}
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 422 | Non-CSV file, missing `text` column, >10K rows |
| 500 | Batch processing failed |

---

### GET /status/{job_id}

Poll batch job progress.

**Response `200` (processing):**

```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "processing",
  "total_reviews": 4250,
  "processed": 1200,
  "result_url": null
}
```

**Response `200` (completed):**

```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "completed",
  "total_reviews": 4250,
  "processed": 4250,
  "result_url": "/results/download/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 404 | Job ID not found |

---

### GET /health

System health check.

**Response `200`:**

```json
{
  "status": "ok",
  "model": "loaded",
  "db": "connected"
}
```

---

### GET /info

Get model metadata.

**Response `200`:**

```json
{
  "model_name": "xlm-roberta-base-absa",
  "version": "1.0",
  "supported_languages": "en, hi",
  "max_batch_size": "10000"
}
```

---

### GET /metrics

Prometheus metrics endpoint (auto-instrumented).

**Response `200`:** Prometheus text format metrics.

Available metrics:
- `fastapi_requests_total` (counter by method, path, status)
- `fastapi_requests_duration_seconds` (histogram)
- `fastapi_requests_inprogress` (gauge)
- Custom ABSA metrics (if implemented)

---

## Example Usage

### cURL

```bash
# Single prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This phone has amazing battery life but the camera is disappointing", "language": "en"}'

# Health check
curl http://localhost:8000/health

# Model info
curl http://localhost:8000/info
```

### Python

```python
import httpx

response = httpx.post(
    "http://localhost:8000/predict",
    json={"text": "This phone has amazing battery life but the camera is disappointing"}
)
print(response.json())
```

### JavaScript

```javascript
const response = await fetch('http://localhost:8000/predict', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: 'This phone has amazing battery life but the camera is disappointing'
  })
});
const data = await response.json();
console.log(data);
```
