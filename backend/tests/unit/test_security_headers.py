"""Unit tests for the security headers middleware."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.security_headers import SecurityHeadersMiddleware


def _make_app(csp=None):
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware, csp=csp)

    @app.get("/")
    async def root():
        return {"ok": True}

    return app


class TestSecurityHeaders:
    def test_core_headers_present(self):
        client = TestClient(_make_app())
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.headers["X-Content-Type-Options"] == "nosniff"
        assert resp.headers["X-Frame-Options"] == "DENY"
        assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "Permissions-Policy" in resp.headers
        assert "Content-Security-Policy" in resp.headers

    def test_csp_default_is_swagger_friendly(self):
        client = TestClient(_make_app())
        resp = client.get("/")
        csp = resp.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp

    def test_csp_from_constructor_override(self):
        client = TestClient(_make_app(csp="default-src 'none'"))
        resp = client.get("/")
        assert resp.headers["Content-Security-Policy"] == "default-src 'none'"

    def test_no_hsts_over_plain_http(self):
        client = TestClient(_make_app())
        resp = client.get("/")
        assert "Strict-Transport-Security" not in resp.headers

    def test_hsts_when_forwarded_https(self):
        client = TestClient(_make_app())
        resp = client.get("/", headers={"X-Forwarded-Proto": "https"})
        assert (
            resp.headers["Strict-Transport-Security"]
            == "max-age=31536000; includeSubDomains"
        )

    def test_applied_on_main_app(self):
        from app.main import app

        client = TestClient(app)
        resp = client.get("/")
        assert resp.headers["X-Content-Type-Options"] == "nosniff"
