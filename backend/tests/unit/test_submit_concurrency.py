"""Issue #264: submit post-grading side effects run concurrently."""

import asyncio
import time
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.api.submit import _record_post_grading


class _Slow:
    def __init__(self, delay=0.2):
        self.delay = delay
        self.calls = []

    async def observe_submission(self, **kwargs):
        await asyncio.sleep(self.delay)
        self.calls.append("observe")

    async def ingest_events(self, events, user_id=None):
        await asyncio.sleep(self.delay)
        self.calls.append("ingest")

    async def invalidate(self, user_id):
        await asyncio.sleep(self.delay)
        self.calls.append("invalidate")


class _SkillService:
    def __init__(self, slow):
        self.slow = slow

    async def ingest_events(self, events, user_id=None):
        await self.slow.ingest_events(events, user_id=user_id)


class _Cache:
    def __init__(self, slow):
        self.slow = slow

    async def invalidate(self, user_id):
        await self.slow.invalidate(user_id)

    async def delete(self, key):
        # Real Redis deletes are ms; no sleep — the SUT's concurrency is
        # across branches, not within the pre-existing sequential deletes.
        self.slow.calls.append("invalidate")


@pytest.mark.asyncio
async def test_post_grading_side_effects_are_concurrent():
    """Three 0.2s side effects must overlap — well under the 0.6s sequential sum."""
    slow = _Slow()
    persisted = SimpleNamespace(id="sub-1", created_at=datetime.now(timezone.utc))
    start = time.monotonic()
    await _record_post_grading(
        reviews=slow,
        skill_service=_SkillService(slow),
        cache=_Cache(slow),
        user_id="user-1",
        question_id="q-1",
        passed=False,
        error_signature="sig",
        persisted=persisted,
        now=datetime.now(timezone.utc),
    )
    elapsed = time.monotonic() - start
    assert set(slow.calls) == {"ingest", "invalidate", "observe"}
    assert slow.calls.count("ingest") == 1
    assert slow.calls.count("observe") == 1
    assert elapsed < 0.5, f"sequential side effects took {elapsed:.2f}s"


@pytest.mark.asyncio
async def test_post_grading_degrades_open():
    """Failing side effects must never raise."""

    class _Fail:
        async def observe_submission(self, **kwargs):
            raise RuntimeError("db down")

        async def ingest_events(self, events, user_id=None):
            raise RuntimeError("db down")

        async def invalidate(self, user_id):
            raise RuntimeError("redis down")

    await _record_post_grading(
        reviews=_Fail(),
        skill_service=_Fail(),
        cache=_Fail(),
        user_id="user-1",
        question_id="q-1",
        passed=True,
        error_signature=None,
        persisted=None,
        now=datetime.now(timezone.utc),
    )
