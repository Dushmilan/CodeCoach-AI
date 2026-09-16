"""Issue #179: classroom-analytics batch path (RED first).

Covers: ports expose batch methods, service _summarize figures identical to
legacy loop, class_overviews grouping, and O(1) repo calls (2 total for any
roster size).
"""

import asyncio
from datetime import datetime, timezone

from app.models.course_schemas import CourseProgress
from app.services.class_analytics_service import ClassAnalyticsService


def _sub(passed, uid="u", idx=0):
    from app.models.submission_schemas import Submission

    return Submission(
        id=f"s-{uid}-{idx}-{passed}",
        user_id=uid,
        question_id="two-sum",
        code="c",
        language="python",
        passed=passed,
        attempt_index=idx,
        created_at=datetime.now(timezone.utc),
    )


class CountingSubmissions:
    """Batch-capable fake: records call counts for O(1) assertions."""

    def __init__(self, by_user):
        self._by_user = by_user
        self.list_by_user_calls = 0
        self.list_by_users_calls = 0

    async def list_by_user(self, user_id, limit=1000):
        self.list_by_user_calls += 1
        return list(self._by_user.get(user_id, [])[:limit])

    async def list_by_users(self, user_ids, limit=1000):
        self.list_by_users_calls += 1
        return {u: list(self._by_user.get(u, [])[:limit]) for u in user_ids}


class CountingProgress:
    def __init__(self, by_user):
        self._by_user = by_user
        self.get_all_calls = 0
        self.get_all_for_users_calls = 0

    async def get_all_progress(self, user_id):
        self.get_all_calls += 1
        completed = self._by_user.get(user_id, [])
        if not completed:
            return []
        return [
            CourseProgress(
                user_id=user_id, course_id="course-1", completed_lessons=completed
            )
        ]

    async def get_all_progress_for_users(self, user_ids):
        self.get_all_for_users_calls += 1
        out = {}
        for u in user_ids:
            completed = self._by_user.get(u, [])
            out[u] = (
                []
                if not completed
                else [
                    CourseProgress(
                        user_id=u,
                        course_id="course-1",
                        completed_lessons=completed,
                    )
                ]
            )
        return out


def _svc():
    subs = CountingSubmissions(
        {
            "s1": [_sub(True, "s1", 0), _sub(False, "s1", 1)],
            "s2": [_sub(False, "s2", 0)],
            "s3": [_sub(True, "s3", 0), _sub(True, "s3", 1)],
        }
    )
    progress = CountingProgress(
        {
            "s1": ["l1", "l2", "l3", "l4", "l5", "l6"],
            "s2": ["l1", "l2"],
            "s3": ["l1"],
        }
    )
    svc = ClassAnalyticsService(submissions=subs, progress=progress)
    return svc, subs, progress


def test_ports_expose_batch_methods():
    from app.ports.classroom_repository import ClassroomRepository
    from app.ports.progress_repository import ProgressRepository
    from app.ports.submission_repository import SubmissionRepository

    assert hasattr(SubmissionRepository, "list_by_users")
    assert hasattr(ProgressRepository, "get_all_progress_for_users")
    assert hasattr(ClassroomRepository, "list_classroom_student_ids_by_room")


def test_summarize_matches_legacy_figures():
    svc, _, _ = _svc()
    assert hasattr(svc, "_summarize")
    rows = [
        CourseProgress(
            user_id="s1",
            course_id="course-1",
            completed_lessons=["l1", "l2", "l3", "l4", "l5", "l6"],
        )
    ]
    summary = svc._summarize(
        "s1", [_sub(True, "s1", 0), _sub(False, "s1", 1)], rows, total_lessons=10
    )
    assert summary.user_id == "s1"
    assert summary.attempted == 2
    assert summary.solved == 1
    assert summary.completed_lessons == 6
    assert summary.completion_pct == 60.0


def test_class_overview_uses_batch_o1_and_figures_identical():
    svc, subs, progress = _svc()
    resp = asyncio.run(svc.class_overview(["s1", "s2", "s3"], total_lessons=10))
    assert resp.total_students == 3
    by_id = {s.user_id: s for s in resp.students}
    assert by_id["s1"].completion_pct == 60.0
    assert by_id["s1"].solved == 1
    assert by_id["s2"].completion_pct == 20.0
    assert by_id["s3"].completion_pct == 10.0
    assert resp.avg_completion == round((60.0 + 20.0 + 10.0) / 3, 1)
    # O(1): exactly one batch call per repo, zero per-user calls.
    assert subs.list_by_users_calls == 1
    assert progress.get_all_for_users_calls == 1
    assert subs.list_by_user_calls == 0
    assert progress.get_all_calls == 0


def test_class_overviews_groups_per_room_with_identical_figures():
    svc, subs, progress = _svc()
    assert hasattr(svc, "class_overviews")
    rosters = {"room-a": ["s1", "s2"], "room-b": ["s3"]}
    out = asyncio.run(svc.class_overviews(rosters, total_lessons=10))
    assert set(out) == {"room-a", "room-b"}
    assert out["room-a"].total_students == 2
    assert out["room-b"].total_students == 1
    # Figures identical to single-room path.
    svc2, _, _ = _svc()
    single = asyncio.run(svc2.class_overview(["s1", "s2"], total_lessons=10))
    assert [s.model_dump() for s in out["room-a"].students] == [
        s.model_dump() for s in single.students
    ]
    # O(1) across rooms: still one batch call per repo.
    assert subs.list_by_users_calls == 1
    assert progress.get_all_for_users_calls == 1


def test_classroom_overview_accepts_prefetched_room_and_ids():
    import inspect

    sig = inspect.signature(ClassAnalyticsService.classroom_overview)
    assert "room" in sig.parameters
    assert "student_ids" in sig.parameters
