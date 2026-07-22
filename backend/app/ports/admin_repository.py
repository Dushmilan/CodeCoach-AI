from abc import abstractmethod
from typing import List

from app.models.admin_models import StatsResponse, CourseProgressDetail
from app.ports.user_admin_repository import UserAdminRepository
from app.ports.question_admin_repository import QuestionAdminRepository
from app.ports.course_admin_repository import CourseAdminRepository


class AdminRepository(
    UserAdminRepository, QuestionAdminRepository, CourseAdminRepository
):
    @abstractmethod
    async def get_system_stats(self) -> StatsResponse: ...

    @abstractmethod
    async def get_course_progress_by_user(
        self, user_id: str
    ) -> List[CourseProgressDetail]: ...
