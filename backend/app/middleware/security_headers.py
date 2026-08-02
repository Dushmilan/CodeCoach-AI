"""Security headers middleware — sets baseline hardening headers on every response.

CSP is configurable via the SECURITY_HEADERS_CSP env var; a Swagger-friendly
default is used so /docs keeps working out of the box.
"""

import os
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_DEFAULT_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com https://cdnjs.cloudflare.com; "
    "style-src 'self' 'unsafe-inline' https://unpkg.com https://cdnjs.cloudflare.com; "
    "img-src 'self' data:; "
    "font-src 'self' data:; "
    "connect-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "frame-ancestors 'none'"
)

_HSTS_MAX_AGE = 31536000


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds X-Content-Type-Options, X-Frame-Options, Referrer-Policy,
    Permissions-Policy, CSP, and (over HTTPS only) HSTS headers."""

    def __init__(
        self,
        app,
        csp: Optional[str] = None,
        hsts_max_age: int = _HSTS_MAX_AGE,
    ):
        super().__init__(app)
        self.csp = csp or os.getenv("SECURITY_HEADERS_CSP") or _DEFAULT_CSP
        self.hsts_max_age = hsts_max_age

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )
        response.headers["Content-Security-Policy"] = self.csp

        if (
            request.url.scheme == "https"
            or request.headers.get("x-forwarded-proto") == "https"
        ):
            response.headers["Strict-Transport-Security"] = (
                f"max-age={self.hsts_max_age}; includeSubDomains"
            )

        return response
