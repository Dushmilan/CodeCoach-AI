from abc import ABC, abstractmethod
from typing import List, Optional

from app.models.course_schemas import CourseProgress


class ProgressRepository(ABC):
    @abstractmethod
    async def get_progress(
        self, user_id: str, course_id: str
    ) -> Optional[CourseProgress]: ...

    @abstractmethod
    async def get_all_progress(self, user_id: str) -> List[CourseProgress]: ...

    @abstractmethod
    async def mark_lesson_complete(
        self, user_id: str, course_id: str, lesson_id: str
    ) -> CourseProgress: ...

    @abstractmethod
    async def save(self, progress: CourseProgress) -> None: ...
