"""Unit tests for MemoryGraphService — forgetting-curve aggregation (Idea #3).

Contracts:
  * Topics are derived from ``questions.category``; only topics where the
    learner has at least one review card are surfaced.
  * ``totalDue`` / ``totalCards`` are global counts.
  * Per-topic ``dueCount`` counts scheduled cards with due_at <= now.
  * ``energyCostMinutes`` grows with interval + lapses so the most-urgent
    topic sorts first.
  * ``daysSinceLastTouch`` prefers the freshest submission or card review
    for that topic.
"""

from datetime import datetime, timedelta, timezone

from app.models.mistake_schemas import ReviewCard
from app.models.schemas import Question, Difficulty

NOW = datetime(2026, 8, 24, 12, 0, 0, tzinfo=timezone.utc)
USER = "user-1"


def _q(qid: str, category: str) -> Question:
    return Question(
        id=qid,
        title=f"Q {qid}",
        difficulty=Difficulty.EASY,
        category=category,
        company_tags=[],
        description="desc",
        starter={"python": ""},
        examples=[],
        test_cases=[],
        hints=[],
        solution=None,
        time_complexity=None,
        space_complexity=None,
        constraints=[],
        is_interactive=0,
        validation_status=None,
    )


def _card(
    *,
    card_id: str,
    question_id: str,
    state: str = "scheduled",
    interval_days: int = 1,
    lapses: int = 0,
    due_at: datetime | None = None,
    last_reviewed_at: datetime | None = None,
    created_at: datetime | None = None,
) -> ReviewCard:
    return ReviewCard(
        id=card_id,
        user_id=USER,
        question_id=question_id,
        error_signature=f"sig-{card_id}",
        state=state,
        ease=2.5,
        interval_days=interval_days,
        repetitions=1,
        lapses=lapses,
        due_at=due_at or NOW,
        last_reviewed_at=last_reviewed_at,
        created_at=created_at or (NOW - timedelta(days=2)),
        updated_at=NOW,
    )


class FakeReviewRepo:
    def __init__(self, rows=None):
        self.rows: list[ReviewCard] = rows or []

    async def get(self, user_id, card_id):
        for r in self.rows:
            if r.user_id == user_id and r.id == card_id:
                return r
        return None

    async def list_for_question(self, user_id, question_id):
        return [r for r in self.rows if r.user_id == user_id and r.question_id == question_id]

    async def list_due(self, *, user_id, now, limit=20):
        due = [r for r in self.rows if r.user_id == user_id and r.state == "scheduled" and r.due_at <= now]
        due.sort(key=lambda r: r.due_at)
        return due[:limit]

    async def list_for_user(self, user_id):
        return [r for r in self.rows if r.user_id == user_id]

    async def save(self, card):
        self.rows.append(card)
        return card


class FakeQuestionRepo:
    def __init__(self, questions):
        self._qs = questions

    async def get_all(self, difficulty=None, category=None):
        return [q for q in self._qs if (not category or q.category == category)]

    async def get_by_id(self, question_id):
        for q in self._qs:
            if q.id == question_id:
                return q
        return None

    async def search(self, query, difficulty=None, category=None):
        return []

    async def get_categories(self):
        return list({q.category for q in self._qs})

    async def get_company_tags(self):
        return []

    async def add(self, question):
        self._qs.append(question)


class FakeSubmissionRepo:
    def __init__(self, subs=None):
        self.subs = subs or []

    async def add(self, *, user_id, submission):
        self.subs.append(submission)
        return submission

    async def list_by_user(self, user_id, *, limit=50):
        return [s for s in self.subs if s.user_id == user_id][:limit]

    async def count_attempts(self, user_id, question_id):
        return len([s for s in self.subs if s.user_id == user_id and s.question_id == question_id])


def _sub(qid, created_at):
    from app.models.submission_schemas import Submission

    # Minimal submission shape for daysSinceLastTouch derivation
    return Submission(
        id=f"sub-{qid}-{created_at.isoformat()}",
        user_id=USER,
        question_id=qid,
        language="python",
        code="print(1)",
        passed=True,
        error_signature=None,
        attempt_index=1,
        created_at=created_at,
    )


class TestMemoryGraph:
    async def test_empty_user_returns_no_topics(self):
        from app.services.memory_graph_service import MemoryGraphService

        svc = MemoryGraphService(
            review_repo=FakeReviewRepo([]),
            question_repo=FakeQuestionRepo([_q("q1", "Arrays"), _q("q2", "Strings")]),
            submission_repo=FakeSubmissionRepo([]),
        )
        res = await svc.graph(user_id=USER, now=NOW)
        assert res.totalCards == 0
        assert res.totalDue == 0
        assert res.topics == []

    async def test_single_topic_counts_and_due(self):
        from app.services.memory_graph_service import MemoryGraphService

        cards = [
            _card(card_id="c1", question_id="q1", state="scheduled", due_at=NOW - timedelta(hours=1), interval_days=6, lapses=0),
            _card(card_id="c2", question_id="q1", state="scheduled", due_at=NOW + timedelta(days=5), interval_days=6, lapses=0),
        ]
        svc = MemoryGraphService(
            review_repo=FakeReviewRepo(cards),
            question_repo=FakeQuestionRepo([_q("q1", "Arrays")]),
            submission_repo=FakeSubmissionRepo([]),
        )
        res = await svc.graph(user_id=USER, now=NOW)
        assert res.totalCards == 2
        assert res.totalDue == 1
        assert len(res.topics) == 1
        t = res.topics[0]
        assert t.topic == "Arrays"
        assert t.totalCards == 2
        assert t.dueCount == 1

    async def test_energy_cost_sorts_most_urgent_first(self):
        from app.services.memory_graph_service import MemoryGraphService

        cards = [
            _card(card_id="c-arrays", question_id="q1", interval_days=1, lapses=0, due_at=NOW - timedelta(days=1)),
            _card(card_id="c-dp", question_id="q2", interval_days=6, lapses=2, due_at=NOW - timedelta(days=1)),
        ]
        svc = MemoryGraphService(
            review_repo=FakeReviewRepo(cards),
            question_repo=FakeQuestionRepo([_q("q1", "Arrays"), _q("q2", "DP")]),
            submission_repo=FakeSubmissionRepo([]),
        )
        res = await svc.graph(user_id=USER, now=NOW)
        assert [t.topic for t in res.topics] == ["DP", "Arrays"]

    async def test_days_since_last_touch_from_submission(self):
        from app.services.memory_graph_service import MemoryGraphService

        cards = [_card(card_id="c1", question_id="q1", due_at=NOW - timedelta(days=1))]
        subs = [_sub("q1", NOW - timedelta(days=6))]
        svc = MemoryGraphService(
            review_repo=FakeReviewRepo(cards),
            question_repo=FakeQuestionRepo([_q("q1", "Recursion")]),
            submission_repo=FakeSubmissionRepo(subs),
        )
        res = await svc.graph(user_id=USER, now=NOW)
        assert res.topics[0].daysSinceLastTouch == 6
