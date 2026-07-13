# Security Analysis — Multilingual ABSA

## Current State

| Area | Status | Notes |
|------|--------|-------|
| JWT Authentication | ❌ Not implemented | No auth layer |
| OAuth | ❌ Not implemented | No SSO |
| HTTPS | ❌ Not enforced | Expects reverse proxy to terminate TLS |
| Input Validation | ✅ Partial | Pydantic validation present; no server-side max_length |
| SQL Injection | ✅ Protected | SQLAlchemy ORM parameterized queries |
| XSS | ✅ Protected | Jinja2 auto-escaping |
| CSRF | ❌ Not implemented | No CSRF middleware; CORS `"*"` mitigates partially |
| Secrets Management | ⚠️ Manual | `.env` gitignored; Docker Compose has hardcoded dev creds |
| Rate Limiting | ❌ Not implemented | No throttling on any endpoint |
| File Upload Security | ⚠️ Partial | Extension validation; no size limit; temp files not cleaned on success |
| Authorization | ❌ None | No role-based or API-key access control |
| CORS | ⚠️ Permissive | `allow_origins=["*"]` |

## Risks & Recommendations

### Critical

1. **Missing authentication** — All endpoints are publicly accessible
   - **Fix**: Add FastAPI middleware for API key validation
   - **Fix**: Integrate OAuth2/OIDC for multi-user scenarios

2. **No rate limiting** — `/batch` endpoint can be abused (10K rows per request)
   - **Fix**: Add `slowapi` or custom rate-limiting middleware
   - **Fix**: Implement per-IP request quotas

### High

3. **Temp file leak** — Batch CSV saved via `NamedTemporaryFile(delete=False)` but `os.unlink()` only called on validation error, not on success
   - **Fix**: Add `try/finally` block to ensure cleanup

4. **CORS all origins** — `"*"` allows any website to call the API
   - **Fix**: Restrict to known dashboard domains

5. **No server-side text length limit** — `ReviewInput.text` accepts arbitrary length
   - **Fix**: Add `StringConstraints(max_length=512)` to Pydantic model

### Medium

6. **No file size limit on batch uploads** — Only row count limit (10K)
   - **Fix**: Add file-size check (e.g., 50MB max)

7. **Hardcoded credentials** in `docker-compose.yml` — `absa_user/absa_pass`
   - **Fix**: Use environment variables or Docker secrets

8. **CSRF** — No protection; token-based auth (when implemented) would mitigate

### Low

9. **Weak health check** — Returns `"db": "connected"` without actually pinging DB
   - **Fix**: Add actual DB ping to `/health` endpoint

10. **No request logging** — No structured logging or audit trail

## Configuration Checklist

- [ ] Set `ENABLE_METRICS` to `false` if Prometheus not needed
- [ ] Set `LOG_LEVEL` to `WARNING` in production
- [ ] Use strong, random passwords for PostgreSQL
- [ ] Run API behind TLS-terminating reverse proxy (Railway does this automatically)
- [ ] Keep `.env` out of version control (already in `.gitignore`)
- [ ] Rotate secrets regularly
