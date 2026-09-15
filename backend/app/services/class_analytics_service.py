"""ClassAnalyticsService — read-only class aggregates over existing data.

Issue #159, phase 2 (professor dashboard). MVP uses only data that already
exists per student: ``course_progress`` (via ``ProgressRepository``) and
``submissions`` (via ``SubmissionRepository``). No new tracking tables, no
writes — pure aggregation for class-level views.
"""

from typing import List, Optional, Sequence

from app.models.analytics_schemas import (
    ClassAnalyticsResponse,
    ClassStudentSummary,
)
from app.ports.progress_repository import ProgressRepository
from app.ports.submission_repository import SubmissionRepository


class ClassAnalyticsService:
    def __init__(
        self,
        submissions: SubmissionRepository,
        progress: Optional[ProgressRepository] = None,
    ):
        self._submissions = submissions
        self._progress = progress

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

    async def _completed_lessons(self, user_id: str) -> int:
        if self._progress is None:
            return 0
        rows = await self._progress.get_all_progress(user_id)
        seen = set()
        for row in rows or []:
            for lesson_id in getattr(row, "completed_lessons", []) or []:
                seen.add(lesson_id)
        return len(seen)
