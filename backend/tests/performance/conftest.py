"""Performance-tier fixtures.

Load tests intentionally fire hundreds of requests per test at the public
read endpoints, which are rate-limited by default. This tier measures raw
throughput, so the per-client cap is raised here (the security tier is where
the limit itself is validated). The slowapi limiter state is global, so it is
also reset around every test to keep load measurements isolated.

The app's async engine is disposed after every async test too: asyncpg
connections are bound to the event loop they were created on, and mixing
sync TestClient sessions (session-scoped, own loop) with per-test async loops
leaks cross-loop connections otherwise.
"""

import pytest
import pytest_asyncio
from app.main import app

_HIGH_QUESTIONS_LIMIT = "100000/minute"


@pytest.fixture(autouse=True)
def _load_test_rate_limit_env(monkeypatch):
    monkeypatch.setenv("QUESTIONS_RATE_LIMIT", _HIGH_QUESTIONS_LIMIT)
    yield
    app.state.limiter.reset()


@pytest_asyncio.fixture(autouse=True)
async def _dispose_app_engine_between_tests():
    """Close any connections bound to the just-finished test's event loop."""
    from app.core.database import engine

    yield
    await engine.dispose()
