from app.middleware.rate_limit import (
    COACH_RATE_LIMIT,
    RUN_RATE_LIMIT,
    QUESTIONS_RATE_LIMIT,
    limiter,
)


class TestRateLimitConfig:
    def test_limiter_exists(self):
        assert limiter is not None

    def test_coach_rate_limit_default(self, monkeypatch):
        monkeypatch.delenv("COACH_RATE_LIMIT", raising=False)
        assert COACH_RATE_LIMIT() == "10/minute"

    def test_run_rate_limit_default(self, monkeypatch):
        monkeypatch.delenv("RUN_RATE_LIMIT", raising=False)
        assert RUN_RATE_LIMIT() == "30/minute"

    def test_questions_rate_limit_default(self, monkeypatch):
        monkeypatch.delenv("QUESTIONS_RATE_LIMIT", raising=False)
        assert QUESTIONS_RATE_LIMIT() == "100/minute"

    def test_coach_rate_limit_from_env(self, monkeypatch):
        monkeypatch.setenv("COACH_RATE_LIMIT", "50/minute")
        assert COACH_RATE_LIMIT() == "50/minute"

    def test_limiter_registered_on_app(self):
        from app.main import app

        assert hasattr(app.state, "limiter")
