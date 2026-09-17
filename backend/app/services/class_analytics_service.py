"""ClassAnalyticsService — read-only class aggregates over existing data.

Issue #159, phase 2 (professor dashboard). MVP uses only data that already
exists per student: ``course_progress`` (via ``ProgressRepository``) and
``submissions`` (via ``SubmissionRepository``). No new tracking tables, no
writes — pure aggregation for class-level views.
"""

import logging
from typing import List, Optional, Sequence

from app.models.analytics_schemas import (
    ClassAnalyticsResponse,
    ClassStudentSummary,
)
from app.models.orm import ClassroomORM
from app.ports.classroom_repository import ClassroomRepository
from app.ports.progress_repository import ProgressRepository
from app.ports.submission_repository import SubmissionRepository
from app.ports.user_repository import UserRepository

logger = logging.getLogger(__name__)

# Shared fallback denominator when a room's course has no lessons yet.
# Matches the legacy instructor default so every completion view agrees.
DEFAULT_TOTAL_LESSONS = 10


def resolve_total_lessons(explicit: Optional[int], course_lesson_count: int) -> int:
    """One denominator rule for every completion view.

    An explicit caller value always wins (API contract); otherwise the
    room's real course lesson count; a course with no lessons yet falls
    back to the shared default instead of a zero denominator (which
    would force every student to 0%).
    """
    if explicit is not None:
        return explicit
    if course_lesson_count > 0:
        return course_lesson_count
    return DEFAULT_TOTAL_LESSONS


class ClassroomNotFoundError(LookupError):
    """Unknown classroom id — routes map this to 404 (never 400)."""


class ClassAnalyticsService:
    def __init__(
        self,
        submissions: SubmissionRepository,
        progress: Optional[ProgressRepository] = None,
        classrooms: Optional[ClassroomRepository] = None,
        users: Optional[UserRepository] = None,
    ):
        self._submissions = submissions
        self._progress = progress
        self._classrooms = classrooms
        self._users = users

    def _summarize(
        self,
        user_id: str,
        subs: list,
        progress_rows: list,
        username: str = "",
        *,
        total_lessons: int = 10,
    ) -> ClassStudentSummary:
        """Per-student figures — the exact legacy math in one place."""
        attempted = len(subs)
        solved = sum(1 for s in subs if getattr(s, "passed", False))
        seen = set()
        for row in progress_rows or []:
            for lesson_id in getattr(row, "completed_lessons", []) or []:
                seen.add(lesson_id)
        completed = len(seen)
        raw_pct = (completed / total_lessons * 100.0) if total_lessons else 0.0
        # Belt-and-braces: completed lessons can exceed the denominator
        # (stale progress rows, cross-course ids), so clamp at 100%.
        pct = min(raw_pct, 100.0)
        return ClassStudentSummary(
            user_id=user_id,
            username=username or user_id,
            completed_lessons=completed,
            completion_pct=round(pct, 1),
            attempted=attempted,
            solved=solved,
        )

    def _aggregate(self, students: List[ClassStudentSummary]) -> ClassAnalyticsResponse:
        total = len(students)
        avg_completion = (
            round(sum(s.completion_pct for s in students) / total, 1) if total else 0.0
        )
        avg_solved = round(sum(s.solved for s in students) / total, 2) if total else 0.0
        return ClassAnalyticsResponse(
            total_students=total,
            avg_completion=avg_completion,
            avg_solved=avg_solved,
            students=students,
        )

    async def class_overview(
        self,
        user_ids: Sequence[str],
        *,
        total_lessons: int = 10,
    ) -> ClassAnalyticsResponse:
        ids = list(user_ids)
        if hasattr(self._submissions, "list_by_users"):
            subs_by_user = await self._submissions.list_by_users(ids, limit=1000)
        else:
            subs_by_user = {}
            for user_id in ids:
                subs_by_user[user_id] = await self._submissions.list_by_user(
                    user_id, limit=1000
                )
        if self._progress is not None and hasattr(
            self._progress, "get_all_progress_for_users"
        ):
            progress_by_user = await self._progress.get_all_progress_for_users(ids)
        else:
            progress_by_user = {}
            for user_id in ids:
                progress_by_user[user_id] = await self._completed_rows(user_id)
        usernames = await self._usernames_by_id(ids)
        students = [
            self._summarize(
                user_id,
                subs_by_user.get(user_id, []),
                progress_by_user.get(user_id, []),
                usernames.get(user_id, user_id),
                total_lessons=total_lessons,
            )
            for user_id in ids
        ]
        return self._aggregate(students)

    async def course_lesson_counts(
        self, course_ids: Sequence[str], courses
    ) -> dict[str, int]:
        """Real lesson count per course (batch reads, no per-course roundtrip).

        ``courses`` is a CourseRepository; missing courses count as 0 lessons
        (callers fall back via resolve_total_lessons).
        """
        ids = list(dict.fromkeys(course_ids))
        if not ids:
            return {}
        modules = await courses.get_modules_by_course_batch(ids)
        summaries = await courses.get_lesson_summaries_by_module_ids(
            [m.id for m in modules or []]
        )
        counts: dict[str, int] = {cid: 0 for cid in ids}
        for lesson in summaries or []:
            cid = getattr(lesson, "course_id", None)
            if cid in counts:
                counts[cid] += 1
        return counts

    async def class_overviews(
        self,
        room_students: dict[str, List[str]],
        *,
        total_lessons: int | dict[str, int] = 10,
    ) -> dict[str, ClassAnalyticsResponse]:
        """Batch overviews for many rooms with O(1) repo calls.

        ``total_lessons`` is one denominator for all rooms or a per-room
        map (room id -> denominator); a per-room map keeps batching while
        letting each room use its own course lesson count.
        """
        all_ids = list(
            dict.fromkeys(uid for ids in room_students.values() for uid in ids)
        )
        if hasattr(self._submissions, "list_by_users"):
            subs_by_user = await self._submissions.list_by_users(all_ids, limit=1000)
        else:
            subs_by_user = {}
            for user_id in all_ids:
                subs_by_user[user_id] = await self._submissions.list_by_user(
                    user_id, limit=1000
                )
        if self._progress is not None and hasattr(
            self._progress, "get_all_progress_for_users"
        ):
            progress_by_user = await self._progress.get_all_progress_for_users(all_ids)
        else:
            progress_by_user = {}
            for user_id in all_ids:
                progress_by_user[user_id] = await self._completed_rows(user_id)
        usernames = await self._usernames_by_id(all_ids)
        out: dict[str, ClassAnalyticsResponse] = {}
        for room_id, ids in room_students.items():
            per_room = (
                total_lessons.get(room_id, DEFAULT_TOTAL_LESSONS)
                if isinstance(total_lessons, dict)
                else total_lessons
            )
            students = [
                self._summarize(
                    user_id,
                    subs_by_user.get(user_id, []),
                    progress_by_user.get(user_id, []),
                    usernames.get(user_id, user_id),
                    total_lessons=per_room,
                )
                for user_id in ids
            ]
            out[room_id] = self._aggregate(students)
        return out

    def _classroom_repo(
        self, classrooms: Optional[ClassroomRepository] = None
    ) -> ClassroomRepository:
        """Resolve the port — the service never touches the SQL session."""
        repo = classrooms if classrooms is not None else self._classrooms
        if repo is None:
            raise ValueError("classroom read requires a ClassroomRepository")
        return repo

    async def get_classroom(
        self,
        classroom_id: str,
        *,
        classrooms: Optional[ClassroomRepository] = None,
    ) -> Optional[ClassroomORM]:
        """One room by id, or None (route maps None to 404)."""
        return await self._classroom_repo(classrooms).get_classroom_by_id(classroom_id)

    async def classroom_overview(
        self,
        classroom_id: str,
        *,
        total_lessons: int = 10,
        classrooms: Optional[ClassroomRepository] = None,
        room: Optional[ClassroomORM] = None,
        student_ids: Optional[Sequence[str]] = None,
    ) -> tuple[ClassroomORM, ClassAnalyticsResponse]:
        """Room + aggregates with the roster resolved from enrollments.

        Only ``student`` enrollments count toward totals (TAs are staff, not
        students). Raises ClassroomNotFoundError for unknown ids. The
        aggregation itself delegates to class_overview, so the
        ClassAnalyticsResponse contract is unchanged.
        """
        repo = self._classroom_repo(classrooms)
        if room is None:
            room = await repo.get_classroom_by_id(classroom_id)
        if room is None:
            raise ClassroomNotFoundError(f"unknown classroom {classroom_id!r}")
        if student_ids is None:
            student_ids = await repo.list_classroom_student_ids(classroom_id)
        overview = await self.class_overview(student_ids, total_lessons=total_lessons)
        return room, overview

    async def _usernames_by_id(self, user_ids: List[str]) -> dict:
        """One batch user lookup; unknown ids fall back to the raw user id.

        User resolution is display-only — a users-port failure must never
        take down the analytics payload, so resolve failures degrade to
        user-id fallbacks.
        """
        if not user_ids or self._users is None:
            return {}
        try:
            users = await self._users.list_by_ids(user_ids)
        except Exception:
            logger.warning(
                "Class analytics user lookup failed; falling back to user ids",
                exc_info=True,
            )
            return {}
        names = {}
        for user in users or []:
            uid = getattr(user, "id", None)
            uname = getattr(user, "username", None)
            if uid and uname:
                names[uid] = uname
        return names

    async def _completed_rows(self, user_id: str) -> list:
        if self._progress is None:
            return []
        return await self._progress.get_all_progress(user_id)

    async def _completed_lessons(self, user_id: str) -> int:
        rows = await self._completed_rows(user_id)
        seen = set()
        for row in rows or []:
            for lesson_id in getattr(row, "completed_lessons", []) or []:
                seen.add(lesson_id)
        return len(seen)
