from abc import ABC, abstractmethod
from typing import List, Optional

from app.models.course_schemas import Course, Module, Lesson


class CourseRepository(ABC):
    @abstractmethod
    async def get_all_courses(self) -> List[Course]: ...

    @abstractmethod
    async def get_course_by_id(self, course_id: str) -> Optional[Course]: ...

    @abstractmethod
    async def get_module_by_id(self, module_id: str) -> Optional[Module]: ...

    @abstractmethod
    async def get_lesson_by_id(self, lesson_id: str) -> Optional[Lesson]: ...

    @abstractmethod
    async def get_lessons_by_module(self, module_id: str) -> List[Lesson]: ...

    @abstractmethod
    async def get_modules_by_course(self, course_id: str) -> List[Module]: ...

    async def get_modules_by_course_batch(self, course_ids: List[str]) -> List[Module]:
        result = []
        for cid in course_ids:
            result.extend(await self.get_modules_by_course(cid))
        return result
