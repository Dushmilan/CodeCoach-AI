from abc import ABC, abstractmethod
from typing import List, Optional, Sequence

from app.models.course_schemas import CourseProgress


class ProgressRepository(ABC):
    @abstractmethod
    async def get_progress(
        self, user_id: str, course_id: str
    ) -> Optional[CourseProgress]: ...

    @abstractmethod
    async def get_all_progress(self, user_id: str) -> List[CourseProgress]: ...

    async def get_all_progress_for_users(
        self, user_ids: Sequence[str]
    ) -> dict[str, List[CourseProgress]]:
        """Return progress rows per user in ONE round trip.

        Keys cover every requested id (unknown users map to ``[]``). The
        default loops for fakes; the SQL implementation uses one IN query.
        """
        out: dict[str, List[CourseProgress]] = {}
        for user_id in user_ids:
            out[user_id] = await self.get_all_progress(user_id)
        return out

    @abstractmethod
    async def mark_lesson_complete(
        self, user_id: str, course_id: str, lesson_id: str
    ) -> CourseProgress: ...

    @abstractmethod
    async def save(self, progress: CourseProgress) -> None: ...
