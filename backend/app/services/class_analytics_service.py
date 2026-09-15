"""ClassAnalyticsService — read-only class aggregates over existing data.

Issue #159, phase 2 (professor dashboard). MVP uses only data that already
exists per student: ``course_progress`` (via ``ProgressRepository``) and
``submissions`` (via ``SubmissionRepository``). No new tracking tables, no
writes — pure aggregation for class-level views.
"""

from typing import List, Optional, Sequence

from sqlalchemy import select

from app.models.analytics_schemas import (
    ClassAnalyticsResponse,
    ClassStudentSummary,
)
from app.models.orm import ClassroomEnrollmentORM, ClassroomORM
from app.ports.classroom_repository import ClassroomRepository
from app.ports.progress_repository import ProgressRepository
from app.ports.submission_repository import SubmissionRepository


class ClassroomNotFoundError(LookupError):
    """Unknown classroom id — routes map this to 404 (never 400)."""


class ClassAnalyticsService:
    def __init__(
        self,
        submissions: SubmissionRepository,
        progress: Optional[ProgressRepository] = None,
        classrooms: Optional[ClassroomRepository] = None,
    ):
        self._submissions = submissions
        self._progress = progress
        self._classrooms = classrooms

    async def class_overview(
        self,
        user_ids: Sequence[str],
        *,
        total_lessons: int = 10,
    ) -> ClassAnalyticsResponse:
        students: List[ClassStudentSummary] = []
        for user_id in user_ids:
            subs = await self._submissions.list_by_user(user_id, limit=1000)
            attempted = len(subs)
            solved = sum(1 for s in subs if getattr(s, "passed", False))
            completed = await self._completed_lessons(user_id)
            pct = (completed / total_lessons * 100.0) if total_lessons else 0.0
            students.append(
                ClassStudentSummary(
                    user_id=user_id,
                    completed_lessons=completed,
                    completion_pct=round(pct, 1),
                    attempted=attempted,
                    solved=solved,
                )
            )
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

    def _classroom_session(self, classrooms: Optional[ClassroomRepository] = None):
        """Session behind the SQL classroom repo (port has no read methods)."""
        repo = classrooms if classrooms is not None else self._classrooms
        if repo is None:
            raise ValueError("classroom read requires a ClassroomRepository")
        session = getattr(repo, "session", None)
        if session is None:
            raise ValueError("ClassroomRepository does not expose a session")
        return session

    async def get_classroom(
        self,
        classroom_id: str,
        *,
        classrooms: Optional[ClassroomRepository] = None,
    ) -> Optional[ClassroomORM]:
        """One room by id, or None (route maps None to 404)."""
        session = self._classroom_session(classrooms)
        return (
            await session.execute(
                select(ClassroomORM).where(ClassroomORM.id == classroom_id)
            )
        ).scalar_one_or_none()

    async def classroom_overview(
        self,
        classroom_id: str,
        *,
        total_lessons: int = 10,
        classrooms: Optional[ClassroomRepository] = None,
    ) -> tuple[ClassroomORM, ClassAnalyticsResponse]:
        """Room + aggregates with the roster resolved from enrollments.

        Only ``student`` enrollments count toward totals (TAs are staff, not
        students). Raises ClassroomNotFoundError for unknown ids. The
        aggregation itself delegates to class_overview, so the
        ClassAnalyticsResponse contract is unchanged.
        """
        session = self._classroom_session(classrooms)
        room = await self.get_classroom(classroom_id, classrooms=classrooms)
        if room is None:
            raise ClassroomNotFoundError(f"unknown classroom {classroom_id!r}")
        student_ids = list(
            (
                await session.execute(
                    select(ClassroomEnrollmentORM.user_id)
                    .where(
                        ClassroomEnrollmentORM.classroom_id == classroom_id,
                        ClassroomEnrollmentORM.role == "student",
                    )
                    .order_by(ClassroomEnrollmentORM.user_id)
                )
            )
            .scalars()
            .all()
        )
        overview = await self.class_overview(student_ids, total_lessons=total_lessons)
        return room, overview

    async def _completed_lessons(self, user_id: str) -> int:
        if self._progress is None:
            return 0
        rows = await self._progress.get_all_progress(user_id)
        seen = set()
        for row in rows or []:
            for lesson_id in getattr(row, "completed_lessons", []) or []:
                seen.add(lesson_id)
        return len(seen)
