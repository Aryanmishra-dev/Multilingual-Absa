import os
import re
from typing import Optional
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_CSRF_SECRET = os.getenv("CSRF_SECRET", "unsafe-default-change-in-production")
_CSRF_SALT = "csrf-token"
_SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
_EXEMPT_PATHS = {"/metrics", "/health", "/info", "/docs", "/openapi.json"}

_serializer = URLSafeTimedSerializer(_CSRF_SECRET, salt=_CSRF_SALT)


def generate_csrf_token() -> str:
    return _serializer.dumps("csrf")


def validate_csrf_token(token: str, max_age: int = 3600) -> bool:
    try:
        _serializer.loads(token, max_age=max_age)
        return True
    except (BadSignature, SignatureExpired):
        return False


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        needs_csrf = request.method in {"POST"} and path.endswith("/fragment")
        is_html_page = request.method in _SAFE_METHODS and not path.startswith("/api/") and not path.startswith("/static/") and path not in _EXEMPT_PATHS

        if needs_csrf:
            csrf_cookie = request.cookies.get("csrf_token", "")
            csrf_header = request.headers.get("X-CSRF-Token", "")
            token = csrf_header or csrf_cookie

            if token and not validate_csrf_token(str(token)):
                from fastapi.responses import HTMLResponse
                return HTMLResponse(
                    content="<h1>403: CSRF validation failed</h1><p>Invalid or expired token. Please refresh the page.</p>",
                    status_code=403,
                )

        response: Response = await call_next(request)

        if is_html_page:
            response.set_cookie(
                key="csrf_token",
                value=generate_csrf_token(),
                max_age=3600,
                secure=False,
                httponly=True,
                samesite="lax",
            )

        return response
