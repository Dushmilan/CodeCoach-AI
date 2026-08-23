"""SEC-3 behavior-parity tests: the slowapi replacement must behave identically.

Pins the observable contract of the in-process rate limiter:
- `@limiter.limit(...)` decorator with lazy env-driven limit strings
- 429 on the Nth+1 request with a descriptive error body
- `app.state.limiter.reset()` clears counters between tests
- no X-RateLimit-* headers on the plain IP limiter (those belong to the
  separate per-plan daily caps limiter)
"""

from fastapi.testclient import TestClient

from app.main import app


class TestRateLimitBehaviorParity:
    def test_third_request_429_after_reset(self, test_client: TestClient, monkeypatch):
        monkeypatch.setenv("QUESTIONS_RATE_LIMIT", "2/minute")
        app.state.limiter.reset()

        first = test_client.get("/api/questions/")
        second = test_client.get("/api/questions/")
        third = test_client.get("/api/questions/")

        assert first.status_code == 200
        assert second.status_code == 200
        assert third.status_code == 429

    def test_429_error_body_describes_limit(self, test_client: TestClient, monkeypatch):
        monkeypatch.setenv("QUESTIONS_RATE_LIMIT", "1/minute")
        app.state.limiter.reset()

        test_client.get("/api/questions/")
        blocked = test_client.get("/api/questions/")

        assert blocked.status_code == 429
        body = blocked.json()
        assert "error" in body
        assert "1 per 1 minute" in body["error"]

    def test_429_has_no_x_ratelimit_headers(self, test_client: TestClient, monkeypatch):
        """The IP limiter does NOT emit X-RateLimit-* headers; the separate
        per-plan daily caps limiter owns that contract."""
        monkeypatch.setenv("QUESTIONS_RATE_LIMIT", "1/minute")
        app.state.limiter.reset()

        test_client.get("/api/questions/")
        blocked = test_client.get("/api/questions/")

        assert blocked.status_code == 429
        assert "x-ratelimit-limit" not in blocked.headers
        assert "x-ratelimit-remaining" not in blocked.headers

    def test_reset_clears_counters(self, test_client: TestClient, monkeypatch):
        monkeypatch.setenv("QUESTIONS_RATE_LIMIT", "1/minute")
        app.state.limiter.reset()

        test_client.get("/api/questions/")
        blocked = test_client.get("/api/questions/")
        assert blocked.status_code == 429

        # After reset the window is fresh again.
        app.state.limiter.reset()
        again = test_client.get("/api/questions/")
        assert again.status_code == 200

    def test_store_is_bounded_under_key_flood(self):
        """A flood of unique keys must not grow memory without bound (the
        store clears past the cap rather than leaking)."""
        from unittest.mock import MagicMock

        from app.middleware.rate_limit import Limiter

        lim = Limiter()
        lim._MAX_KEYS = 100  # shrink cap for the test

        fake = MagicMock()
        fake.client.host = "10.0.0.1"
        for i in range(250):
            fake.client.host = f"10.0.0.{i % 250}"
            try:
                lim.check(fake, "5/minute")
            except Exception:
                pass  # individual limits may trip; the bound is what we assert

        assert len(lim._windows) <= 100
