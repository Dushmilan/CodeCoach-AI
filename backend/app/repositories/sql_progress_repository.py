from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from app.models.course_schemas import CourseProgress
from app.models.orm import CourseProgressORM
from app.ports.progress_repository import ProgressRepository


class SqlProgressRepository(ProgressRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _orm_to_model(self, orm: CourseProgressORM) -> CourseProgress:
        return CourseProgress(
            user_id=orm.user_id,
            course_id=orm.course_id,
            completed_lessons=orm.completed_lessons or [],
            last_accessed_lesson_id=orm.last_accessed_lesson_id,
            started_at=orm.started_at,
            last_accessed_at=orm.last_accessed_at,
        )

    async def get_progress(
        self, user_id: str, course_id: str
    ) -> Optional[CourseProgress]:
        result = await self.session.execute(
            select(CourseProgressORM).where(
                CourseProgressORM.user_id == user_id,
                CourseProgressORM.course_id == course_id,
            )
        )
        orm = result.scalar_one_or_none()
        return self._orm_to_model(orm) if orm else None

    async def get_all_progress(self, user_id: str) -> List[CourseProgress]:
        result = await self.session.execute(
            select(CourseProgressORM).where(CourseProgressORM.user_id == user_id)
        )
        return [self._orm_to_model(p) for p in result.scalars().all()]

    async def mark_lesson_complete(
        self, user_id: str, course_id: str, lesson_id: str
    ) -> CourseProgress:
        progress = await self.get_progress(user_id, course_id)
        if progress is None:
            progress = CourseProgress(
                user_id=user_id,
                course_id=course_id,
                completed_lessons=[],
                started_at=datetime.now(timezone.utc),
            )

        if lesson_id not in progress.completed_lessons:
            progress.completed_lessons.append(lesson_id)
        progress.last_accessed_lesson_id = lesson_id
        progress.last_accessed_at = datetime.now(timezone.utc)

        await self.save(progress)
        return progress

    async def save(self, progress: CourseProgress) -> None:
        result = await self.session.execute(
            select(CourseProgressORM).where(
                CourseProgressORM.user_id == progress.user_id,
                CourseProgressORM.course_id == progress.course_id,
            )
        )
        orm = result.scalar_one_or_none()

        if orm:
            orm.completed_lessons = progress.completed_lessons
            orm.last_accessed_lesson_id = progress.last_accessed_lesson_id
            orm.last_accessed_at = progress.last_accessed_at
        else:
            orm = CourseProgressORM(
                id=f"{progress.user_id}:{progress.course_id}",
                user_id=progress.user_id,
                course_id=progress.course_id,
                completed_lessons=progress.completed_lessons or [],
                last_accessed_lesson_id=progress.last_accessed_lesson_id,
                started_at=progress.started_at or datetime.now(timezone.utc),
                last_accessed_at=progress.last_accessed_at or datetime.now(timezone.utc),
            )
            self.session.add(orm)
        await self.session.flush()
