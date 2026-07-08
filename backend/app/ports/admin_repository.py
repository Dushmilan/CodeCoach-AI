from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Tuple

from app.models.auth_schemas import UserInDB
from app.models.admin_models import (
    StatsResponse,
    QuestionFilter,
    QuestionImportResult,
    CourseProgressDetail,
)


class AdminRepository(ABC):
    """Abstract interface for admin repository operations."""

    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]: ...

    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[UserInDB]: ...

    @abstractmethod
    async def update_user_role(
        self, user_id: str, role: str, current_user_id: str
    ) -> bool: ...

    @abstractmethod
    async def update_user_status(
        self, user_id: str, is_active: bool, current_user_id: str
    ) -> bool: ...

    @abstractmethod
    async def list_users(
        self, skip: int = 0, limit: int = 20
    ) -> Tuple[List[UserInDB], int]: ...

    @abstractmethod
    async def get_question_by_id(
        self, question_id: str
    ) -> Optional[Dict[str, Any]]: ...

    @abstractmethod
    async def update_question(
        self, question_id: str, update_data: Dict[str, Any]
    ) -> bool: ...

    @abstractmethod
    async def delete_question(self, question_id: str) -> bool: ...

    @abstractmethod
    async def list_questions(
        self, filter: QuestionFilter
    ) -> Tuple[List[Dict[str, Any]], int]: ...

    @abstractmethod
    async def import_questions(
        self, questions: List[Dict[str, Any]], dry_run: bool = False
    ) -> QuestionImportResult: ...

    @abstractmethod
    async def get_course_tree(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def delete_course(self, course_id: str) -> bool: ...

    @abstractmethod
    async def delete_module(self, module_id: str) -> bool: ...

    @abstractmethod
    async def delete_lesson(self, lesson_id: str) -> bool: ...

    @abstractmethod
    async def get_system_stats(self) -> StatsResponse: ...

    @abstractmethod
    async def get_course_progress_by_user(
        self, user_id: str
    ) -> List[CourseProgressDetail]: ...

    # ── Curriculum CRUD ─────────────────────────────────

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

    @abstractmethod
    async def create_question(self, data: Dict[str, Any]) -> Dict[str, Any]: ...
