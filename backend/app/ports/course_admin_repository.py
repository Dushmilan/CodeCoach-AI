from abc import ABC, abstractmethod
from typing import Dict, Any


class CourseAdminRepository(ABC):
    @abstractmethod
    async def get_course_tree(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def delete_course(self, course_id: str) -> bool: ...

    @abstractmethod
    async def delete_module(self, module_id: str) -> bool: ...

    @abstractmethod
    async def delete_lesson(self, lesson_id: str) -> bool: ...

    @abstractmethod
    async def create_course(self, data: Dict[str, Any]) -> Dict[str, Any]: ...

    @abstractmethod
    async def update_course(self, course_id: str, data: Dict[str, Any]) -> bool: ...

    @abstractmethod
    async def create_module(self, data: Dict[str, Any]) -> Dict[str, Any]: ...

    @abstractmethod
    async def update_module(self, module_id: str, data: Dict[str, Any]) -> bool: ...

    @abstractmethod
    async def create_lesson(self, data: Dict[str, Any]) -> Dict[str, Any]: ...

    @abstractmethod
    async def update_lesson(self, lesson_id: str, data: Dict[str, Any]) -> bool: ...
