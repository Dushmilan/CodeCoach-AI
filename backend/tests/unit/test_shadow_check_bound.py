"""Issue #264: animate shadow-check is bounded and degrades open."""

import asyncio
import time

import pytest

from app.services.groq_service import GroqService

QUESTION = {
    "title": "Add",
    "description": "Add",
    "examples": [{"input": "a = 1, b = 2", "output": "3"}],
}

ANIMATION = {
    "animated_code": "def add(a, b):\n    return a + b",
}


def _service(executor):
    svc = GroqService.__new__(GroqService)
    svc.executor = executor
    return svc


@pytest.mark.asyncio
async def test_shadow_check_hanging_executor_degrades_open():
    """A 10s-hanging Piston must not stall coaching — bound ~5s, trust model."""

    class _HangingExecutor:
        async def execute(self, **kwargs):
            await asyncio.sleep(10)
            raise AssertionError("should have been cancelled")

    svc = _service(_HangingExecutor())
    start = time.monotonic()
    ok, reason = await svc._shadow_check_animation(ANIMATION, QUESTION, None)
    elapsed = time.monotonic() - start
    assert ok is True
    assert reason is None
    assert elapsed < 8, f"shadow-check took {elapsed:.2f}s"
