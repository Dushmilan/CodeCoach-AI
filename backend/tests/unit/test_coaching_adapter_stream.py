"""Issue #273: adapter stream must keep learner/submission personalization."""

import pytest

from app.services.coaching_adapter import CoachingAdapter


class _FakeInner:
    def __init__(self):
        self.seen = {}

    async def stream(self, **kwargs):
        self.seen.update(kwargs)
        yield "hi"


@pytest.mark.asyncio
async def test_adapter_stream_forwards_personalization():
    """learner_context/submission_context must reach inner.stream, not drop."""
    inner = _FakeInner()
    adapter = CoachingAdapter(inner=inner)
    chunks = [
        chunk
        async for chunk in adapter.stream(
            problem="Two Sum",
            code="x",
            language="python",
            message="hint?",
            learner_context="## Learner Skill Context\n- arrays",
            submission_context="## Recent Attempts\n- q1 failed",
        )
    ]
    assert chunks == ["hi"]
    assert "arrays" in (inner.seen.get("learner_context") or "")
    assert "q1 failed" in (inner.seen.get("submission_context") or "")
