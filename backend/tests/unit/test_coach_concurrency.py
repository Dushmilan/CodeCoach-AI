"""Issue #264: /coach builds context + sent-row concurrently; shadow-check bounded."""

import asyncio
import time
from types import SimpleNamespace

import pytest

from app.api.coach import _fetch_context_and_begin_interaction


class _SlowContext:
    async def get_context(self, user_id):
        await asyncio.sleep(0.2)
        return {"skill_block": "s", "submission_block": "a"}


class _SlowInteractions:
    async def create_sent(self, **kwargs):
        await asyncio.sleep(0.2)
        return SimpleNamespace(id="interaction-1")


def _request():
    return SimpleNamespace(
        mode=SimpleNamespace(value="hint"),
        language=SimpleNamespace(value="python"),
        difficulty=SimpleNamespace(value="easy"),
        problem="p",
        code="c",
    )


@pytest.mark.asyncio
async def test_context_and_sent_row_are_concurrent():
    """Two 0.2s awaits must overlap — total well under the 0.4s sequential sum."""
    start = time.monotonic()
    learner_ctx, interaction = await _fetch_context_and_begin_interaction(
        _SlowContext(), _SlowInteractions(), "user-1", _request(), "questions"
    )
    elapsed = time.monotonic() - start
    assert learner_ctx == {"skill_block": "s", "submission_block": "a"}
    assert interaction.id == "interaction-1"
    assert elapsed < 0.35, f"sequential awaits took {elapsed:.2f}s"


@pytest.mark.asyncio
async def test_context_and_sent_degrade_open():
    """A failing context fetch or sent persist must not break the request."""

    class _FailContext:
        async def get_context(self, user_id):
            raise RuntimeError("redis down")

    class _FailInteractions:
        async def create_sent(self, **kwargs):
            raise RuntimeError("db down")

    learner_ctx, interaction = await _fetch_context_and_begin_interaction(
        _FailContext(), _FailInteractions(), "user-1", _request(), "questions"
    )
    assert learner_ctx == {"skill_block": "", "submission_block": ""}
    assert interaction is None
