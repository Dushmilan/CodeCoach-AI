from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from app.models.auth_schemas import UserInDB
from app.models.admin_models import (
    StatsResponse,
    QuestionFilter,
    QuestionImportResult,
    FeatureFlagUpdate,
    CourseProgressDetail,
    AuditLogFilter,
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
    async def get_generation_jobs(
        self, status: Optional[str] = None
    ) -> List[Dict[str, Any]]: ...

    @abstractmethod
    async def get_generation_job_by_id(
        self, job_id: str
    ) -> Optional[Dict[str, Any]]: ...

    @abstractmethod
    async def update_generation_job(
        self, job_id: str, updates: Dict[str, Any]
    ) -> bool: ...

    @abstractmethod
    async def get_feature_flags(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def update_feature_flag(
        self, key: str, updates: FeatureFlagUpdate
    ) -> bool: ...

    @abstractmethod
    async def get_audit_logs(
        self, filter: AuditLogFilter, skip: int = 0, limit: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]: ...

    @abstractmethod
    async def get_system_stats(self) -> StatsResponse: ...

    @abstractmethod
    async def get_course_progress_by_user(
        self, user_id: str
    ) -> List[CourseProgressDetail]: ...

    @abstractmethod
    async def generate_user_role_grant_report(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]: ...
