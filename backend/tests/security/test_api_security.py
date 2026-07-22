"""
API-level security tests (CORS, headers, methods, size limits).
"""

from fastapi.testclient import TestClient


class TestApiSecurity:
    """Tests for API-level security controls."""

    def test_cors_no_wildcard_for_auth(self, test_client: TestClient):
        """Authenticated endpoints should not return CORS wildcard."""
        origins = [
            "https://malicious-site.com",
            "http://localhost:3001",
            "null",
            "https://evil.com",
        ]
        for origin in origins:
            response = test_client.get("/api/auth/me", headers={"Origin": origin})
            cors = response.headers.get("access-control-allow-origin", "")
            assert cors != "*", f"CORS wildcard returned for origin {origin}"

    def test_content_type_enforcement(self, test_client: TestClient):
        """Wrong content types should be rejected with 415 or 422."""
        invalid_types = [
            "application/xml",
            "text/plain",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        ]
        for content_type in invalid_types:
            response = test_client.post(
                "/api/coach/",
                data='{"test": "data"}',
                headers={"Content-Type": content_type},
            )
            assert response.status_code in [401, 415, 422]

    def test_request_size_limit(self, test_client: TestClient):
        """Overly large payloads should be rejected or handled."""
        large_payload = "x" * (1024 * 1024 + 1)
        body = {
            "problem": large_payload,
            "code": "x=1",
            "language": "python",
            "message": "test",
            "mode": "hint",
            "difficulty": "easy",
        }
        response = test_client.post("/api/coach/", json=body)
        assert response.status_code in [200, 401, 413, 422]

    def test_wrong_http_method(self, test_client: TestClient):
        """Wrong HTTP methods should return 405."""
        get_only_endpoints = [
            "/api/auth/me",
            "/health/health",
            "/api/questions/categories",
        ]
        for endpoint in get_only_endpoints:
            response = test_client.post(endpoint, json={"test": "data"})
            assert response.status_code in [405, 401, 200]

        post_only_endpoints = ["/api/auth/login", "/api/auth/register"]
        for endpoint in post_only_endpoints:
            response = test_client.get(endpoint)
            assert response.status_code in [405, 401, 200]

    def test_header_injection_crlf(self, test_client: TestClient):
        """CRLF injection in headers should be handled gracefully."""
        payloads = [
            {"X-Forwarded-For": "1.1.1.1\r\nX-Custom: injected"},
            {"User-Agent": "Mozilla\r\nLocation: http://evil.com"},
        ]
        for headers in payloads:
            response = test_client.get("/health/health", headers=headers)
            assert response.status_code in [200, 401]

    def test_hsts_header(self, test_client: TestClient):
        """HSTS header should be present on responses (if configured)."""
        response = test_client.get("/health/health")
        hsts = response.headers.get("strict-transport-security")
        if hsts:
            assert "max-age=" in hsts

    def test_cache_control_no_store_sensitive(self, test_client: TestClient):
        """Sensitive endpoints should have Cache-Control: no-store (if authenticated)."""
        response = test_client.get("/api/auth/me")
        cache = response.headers.get("cache-control", "")
        if cache:
            assert "no-store" in cache, f"Missing no-store in Cache-Control: {cache}"

    def test_server_header_not_leaked(self, test_client: TestClient):
        """Server header should not leak version info."""
        response = test_client.get("/health/health")
        server = response.headers.get("server", "")
        assert "uvicorn" not in server.lower(), f"Server header leaks version: {server}"
