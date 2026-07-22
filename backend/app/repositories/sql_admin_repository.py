from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.models.orm import UserORM, QuestionORM, CourseORM, LessonORM
from app.models.admin_models import (
    StatsResponse,
    QuestionFilter,
    QuestionImportResult,
    CourseProgressDetail,
)
from app.ports.admin_repository import AdminRepository
from app.models.auth_schemas import UserInDB
from app.repositories.sql_user_admin_repository import SqlUserAdminRepository
from app.repositories.sql_question_admin_repository import SqlQuestionAdminRepository
from app.repositories.sql_course_admin_repository import SqlCourseAdminRepository


class SqlAdminRepository(AdminRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        self._users = SqlUserAdminRepository(session)
        self._questions = SqlQuestionAdminRepository(session)
        self._courses = SqlCourseAdminRepository(session)

    # ── User delegation ──
    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        return await self._users.get_user_by_id(user_id)

    async def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        return await self._users.get_user_by_username(username)

    async def update_user_role(
        self, user_id: str, role: str, current_user_id: str
    ) -> bool:
        return await self._users.update_user_role(user_id, role, current_user_id)

    async def update_user_status(
        self, user_id: str, is_active: bool, current_user_id: str
    ) -> bool:
        return await self._users.update_user_status(user_id, is_active, current_user_id)

    async def list_users(
        self, skip: int = 0, limit: int = 20
    ) -> Tuple[List[UserInDB], int]:
        return await self._users.list_users(skip, limit)

    # ── Question delegation ──
    async def get_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        return await self._questions.get_question_by_id(question_id)

    async def update_question(
        self, question_id: str, update_data: Dict[str, Any]
    ) -> bool:
        return await self._questions.update_question(question_id, update_data)

    async def delete_question(self, question_id: str) -> bool:
        return await self._questions.delete_question(question_id)

    async def list_questions(
        self, filter: QuestionFilter
    ) -> Tuple[List[Dict[str, Any]], int]:
        return await self._questions.list_questions(filter)

    async def import_questions(
        self, questions: List[Dict[str, Any]], dry_run: bool = False
    ) -> QuestionImportResult:
        return await self._questions.import_questions(questions, dry_run)

    async def create_question(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._questions.create_question(data)

    # ── Course delegation ──
    async def get_course_tree(self) -> Dict[str, Any]:
        return await self._courses.get_course_tree()

    async def delete_course(self, course_id: str) -> bool:
        return await self._courses.delete_course(course_id)

    async def delete_module(self, module_id: str) -> bool:
        return await self._courses.delete_module(module_id)

    async def delete_lesson(self, lesson_id: str) -> bool:
        return await self._courses.delete_lesson(lesson_id)

    async def create_course(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._courses.create_course(data)

    async def update_course(self, course_id: str, data: Dict[str, Any]) -> bool:
        return await self._courses.update_course(course_id, data)

    async def create_module(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._courses.create_module(data)

    async def update_module(self, module_id: str, data: Dict[str, Any]) -> bool:
        return await self._courses.update_module(module_id, data)

    async def create_lesson(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._courses.create_lesson(data)

    async def update_lesson(self, lesson_id: str, data: Dict[str, Any]) -> bool:
        return await self._courses.update_lesson(lesson_id, data)

    async def exists(self, entity_type: str, entity_id: str) -> bool:
        return await self._courses.exists(entity_type, entity_id)

    # ── Stats ──
    async def get_system_stats(self) -> StatsResponse:
        users_count = await self.session.execute(
            select(func.count()).select_from(UserORM)
        )
        total_users = users_count.scalar_one()

        questions_count = await self.session.execute(
            select(func.count()).select_from(QuestionORM)
        )
        total_questions = questions_count.scalar_one()

        courses_count = await self.session.execute(
            select(func.count()).select_from(CourseORM)
        )
        total_courses = courses_count.scalar_one()

        lessons_count = await self.session.execute(
            select(func.count()).select_from(LessonORM)
        )
        total_lessons = lessons_count.scalar_one()

        return StatsResponse(
            users={"total": total_users, "active": 0, "admin": 0, "inactive": 0},
            questions={"total": total_questions, "by_difficulty": {}},
            courses={"total": total_courses, "modules": 0, "lessons": total_lessons},
            system={"storage": "sql", "version": "1.0.0"},
            generation={"total_jobs": 0, "pending": 0, "completed": 0},
        )

    async def get_course_progress_by_user(
        self, user_id: str
    ) -> List[CourseProgressDetail]:
        return []
