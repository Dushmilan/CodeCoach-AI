"""Unit tests for RescueService - the rules engine over the rescue queue.

All clock input is explicit (`now=`), so the rules are deterministic.
The fake repository mirrors the SQL storage invariants (single open row,
dismiss wins forever) without touching PostgreSQL.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.models.rescue_schemas import RescueItem
from app.services.rescue_service import RescueService, next_nine_am_utc

NOW = datetime(2026, 8, 23, 12, 0, 0, tzinfo=timezone.utc)
USER = "user-1"
QUESTION = "q-1"


class InMemoryRescueRepo:
    """Fake mirroring SqlRescueRepository semantics."""

    def __init__(self):
        self.rows: dict[str, RescueItem] = {}  # key: (user, question)

    @staticmethod
    def _key(user_id: str, question_id: str) -> str:
        return f"{user_id}:{question_id}"

    async def create_abandoned(self, *, user_id, question_id, due_at, now):
        key = self._key(user_id, question_id)
        if key in self.rows and self.rows[key].status == "abandoned":
            raise ValueError("unique open row violated")
        item = RescueItem(
            id=f"id-{len(self.rows)}",
            user_id=user_id,
            question_id=question_id,
            status="abandoned",
            first_abandoned_at=now,
            due_at=due_at,
            resurface_count=0,
            created_at=now,
            updated_at=now,
        )
        self.rows[key] = item
        return item

    async def get(self, user_id, question_id):
        row = self.rows.get(self._key(user_id, question_id))
        return row if row and row.status == "abandoned" else None

    async def latest(self, user_id, question_id):
        return self.rows.get(self._key(user_id, question_id))

    async def reschedule(self, *, user_id, question_id, due_at, now):
        row = await self.get(user_id, question_id)
        if row is None:
            return None
        row.due_at = due_at
        row.resurface_count += 1
        row.updated_at = now
        return row

    async def close(self, *, user_id, question_id, status, now):
        row = await self.get(user_id, question_id)
        if row is None:
            return None
        row.status = status
        row.updated_at = now
        return row

    async def list_due(self, *, user_id, now, limit=50):
        rows = [
            r
            for r in self.rows.values()
            if r.user_id == user_id and r.status == "abandoned" and r.due_at <= now
        ]
        return sorted(rows, key=lambda r: r.due_at)[:limit]


@pytest.fixture
def svc():
    return RescueService(repo=InMemoryRescueRepo())


class TestNextNineAmUtc:
    def test_after_nine_am_returns_tomorrow_nine_am(self):
        due = next_nine_am_utc(NOW)
        assert due == datetime(2026, 8, 24, 9, 0, 0, tzinfo=timezone.utc)

    def test_before_nine_am_still_returns_next_day(self):
        early = datetime(2026, 8, 23, 3, 0, 0, tzinfo=timezone.utc)
        assert next_nine_am_utc(early).day == 24

    def test_client_timezone_offset_is_honored(self):
        # Client at UTC+8: their local time is Aug 23 20:00; tomorrow 09:00
        # local is Aug 24 09:00+08:00 == Aug 24 01:00 UTC.
        due = next_nine_am_utc(NOW, tz_offset_minutes=480)
        assert due == datetime(2026, 8, 24, 1, 0, 0, tzinfo=timezone.utc)


class TestAbandon:
    async def test_first_abandon_creates_row_due_tomorrow(self, svc):
        item = await svc.abandon(user_id=USER, question_id=QUESTION, now=NOW)

        assert item is not None
        assert item.status == "abandoned"
        assert item.due_at == datetime(2026, 8, 24, 9, 0, 0, tzinfo=timezone.utc)
        assert item.resurface_count == 0

    async def test_re_abandon_pushes_due_date_out_and_counts(self, svc):
        await svc.abandon(user_id=USER, question_id=QUESTION, now=NOW)
        later = NOW + timedelta(days=2)

        pushed = await svc.abandon(user_id=USER, question_id=QUESTION, now=later)

        assert pushed is not None
        # Re-abandoned Aug 25 12:00 UTC: old due + 1 day (Aug 25 09:00) is
        # already past, so the next-9am floor wins -> Aug 26 09:00.
        assert pushed.due_at == datetime(2026, 8, 26, 9, 0, 0, tzinfo=timezone.utc)
        assert pushed.resurface_count == 1

    async def test_re_abandon_before_due_keeps_original_date_floor(self, svc):
        await svc.abandon(user_id=USER, question_id=QUESTION, now=NOW)
        soon = NOW + timedelta(hours=1)

        pushed = await svc.abandon(user_id=USER, question_id=QUESTION, now=soon)

        # max(old_due + 1 day, next 9am from now): old due + 1 day = Aug 25.
        assert pushed.due_at == datetime(2026, 8, 25, 9, 0, 0, tzinfo=timezone.utc)

    async def test_dismissed_question_never_resurfaces(self, svc):
        await svc.abandon(user_id=USER, question_id=QUESTION, now=NOW)
        await svc.dismiss(user_id=USER, question_id=QUESTION, now=NOW)

        result = await svc.abandon(
            user_id=USER, question_id=QUESTION, now=NOW + timedelta(days=30)
        )

        assert result is None
        assert await svc.due(user_id=USER, now=NOW + timedelta(days=31)) == []

    async def test_completed_question_can_be_re_abandoned(self, svc):
        await svc.abandon(user_id=USER, question_id=QUESTION, now=NOW)
        await svc.complete(user_id=USER, question_id=QUESTION, now=NOW)

        again = await svc.abandon(
            user_id=USER, question_id=QUESTION, now=NOW + timedelta(days=1)
        )

        assert again is not None
        assert again.status == "abandoned"


class TestTransitions:
    async def test_complete_closes_open_row(self, svc):
        await svc.abandon(user_id=USER, question_id=QUESTION, now=NOW)

        closed = await svc.complete(user_id=USER, question_id=QUESTION, now=NOW)

        assert closed is not None and closed.status == "completed"
        assert await svc.due(user_id=USER, now=NOW + timedelta(days=2)) == []

    async def test_dismiss_closes_open_row_permanently(self, svc):
        await svc.abandon(user_id=USER, question_id=QUESTION, now=NOW)

        closed = await svc.dismiss(user_id=USER, question_id=QUESTION, now=NOW)

        assert closed is not None and closed.status == "dismissed"

    async def test_close_without_open_row_returns_none(self, svc):
        assert await svc.complete(user_id=USER, question_id="q-x", now=NOW) is None
        assert await svc.dismiss(user_id=USER, question_id="q-x", now=NOW) is None


class TestDue:
    async def test_only_matured_rows_surface(self, svc):
        await svc.abandon(user_id=USER, question_id="q-a", now=NOW)
        await svc.abandon(user_id=USER, question_id="q-b", now=NOW)
        # Abandoned later -> due tomorrow 9am from THAT moment: still future.
        late = datetime(2026, 8, 25, 9, 30, 0, tzinfo=timezone.utc)
        await svc.abandon(user_id=USER, question_id="q-c", now=late)

        # Clock advanced past q-a/q-b's due dates but before q-c's.
        future = datetime(2026, 8, 25, 10, 0, 0, tzinfo=timezone.utc)

        due = await svc.due(user_id=USER, now=future)

        assert {i.question_id for i in due} == {"q-a", "q-b"}


class TestOpenItem:
    async def test_open_item_returns_open_row_or_none(self, svc):
        assert await svc.open_item(user_id=USER, question_id=QUESTION) is None

        await svc.abandon(user_id=USER, question_id=QUESTION, now=NOW)

        found = await svc.open_item(user_id=USER, question_id=QUESTION)
        assert found is not None and found.status == "abandoned"
