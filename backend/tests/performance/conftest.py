"""Performance test fixtures.

Ensures service dependencies (NIM provider, Piston) can be constructed so
performance tests exercise real request paths rather than failing during
dependency setup. The external NIM provider is mocked: perf tests measure
request-handling latency, not third-party API latency.
"""

import os
import pytest

from app.main import app


@pytest.fixture(autouse=True)
def _perf_env():
    """Set env vars needed for NIM provider / Piston construction."""
    os.environ["NVIDIA_API_KEY"] = "test_nvidia_key_for_perf_tests"
    os.environ["PISTON_API_URL"] = "http://127.0.0.1:2000/api/v2"

    from app.api.coach import get_coaching_provider as get_provider

    class MockNIMProvider:
        async def get_structured(self, **kwargs):
            return {
                "summary": "mock",
                "hints": [],
                "code_review": None,
                "complexity_analysis": None,
                "suggestions": [],
                "edge_cases": [],
                "explanation": None,
                "debug_help": None,
            }

        async def stream(self, **kwargs):
            yield "mock"
            return

    async def override_provider():
        return MockNIMProvider()

    app.dependency_overrides[get_provider] = override_provider
    yield
    app.dependency_overrides.pop(get_provider, None)
