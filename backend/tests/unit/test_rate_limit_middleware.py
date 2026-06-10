import os
import pytest
from importlib import reload


class TestRateLimitConfig:
    def test_limiter_exists(self):
        from app.middleware.rate_limit import limiter
        assert limiter is not None

    def test_coach_rate_limit_default(self):
        os.environ.pop("COACH_RATE_LIMIT", None)
        import app.middleware.rate_limit as rl
        reload(rl)
        assert rl.COACH_RATE_LIMIT == "10/minute"

    def test_run_rate_limit_default(self):
        os.environ.pop("RUN_RATE_LIMIT", None)
        import app.middleware.rate_limit as rl
        reload(rl)
        assert rl.RUN_RATE_LIMIT == "30/minute"

    def test_questions_rate_limit_default(self):
        os.environ.pop("QUESTIONS_RATE_LIMIT", None)
        import app.middleware.rate_limit as rl
        reload(rl)
        assert rl.QUESTIONS_RATE_LIMIT == "100/minute"

    def test_coach_rate_limit_from_env(self):
        os.environ["COACH_RATE_LIMIT"] = "50/minute"
        import app.middleware.rate_limit as rl
        reload(rl)
        assert rl.COACH_RATE_LIMIT == "50/minute"
        os.environ.pop("COACH_RATE_LIMIT", None)

    def test_limiter_registered_on_app(self):
        from app.main import app
        assert hasattr(app.state, "limiter")
