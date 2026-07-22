"""File-based admin repository — delegates to focused sub-repositories."""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from app.models.auth_schemas import UserInDB
from app.models.admin_models import (
    StatsResponse,
    QuestionFilter,
    QuestionImportResult,
    CourseProgressDetail,
)
from app.ports.admin_repository import AdminRepository
from app.repositories.file_user_admin_repository import FileUserAdminRepository
from app.repositories.file_question_admin_repository import FileQuestionAdminRepository
from app.repositories.file_course_admin_repository import FileCourseAdminRepository

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class FileAdminRepository(AdminRepository):
    def __init__(
        self,
        users_file: str = "",
        questions_file: str = "",
        courses_dir: str = "",
        progress_file: str = "",
    ):
        self._users = FileUserAdminRepository(
            users_file or str(BASE_DIR / "data" / "users.json")
        )
        self._questions = FileQuestionAdminRepository(
            questions_file or str(BASE_DIR / "questions" / "sample_questions.json")
        )
        self._courses = FileCourseAdminRepository(
            courses_dir or str(BASE_DIR / "data" / "courses")
        )
        self._progress_file = Path(
            progress_file or BASE_DIR / "data" / "user_progress.json"
        )

    def _load_progress(self) -> List[Dict[str, Any]]:
        if not self._progress_file.exists():
            return []
        with open(self._progress_file, encoding="utf-8") as f:
            return json.load(f)

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
    async def exists(self, entity_type: str, entity_id: str) -> bool:
        return await self._courses.exists(entity_type, entity_id)

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

    # ── Stats ──
    async def get_system_stats(self) -> StatsResponse:
        users = self._users._load_users()
        questions = self._questions._load_questions()
        tree = self._courses._load_courses()

        active = sum(1 for u in users if u.get("is_active", False))
        admins = sum(1 for u in users if u.get("role") in ("admin", "super_admin"))

        diff_dist = {}
        for q in questions:
            d = q.get("difficulty", "unknown")
            diff_dist[d] = diff_dist.get(d, 0) + 1

        return StatsResponse(
            users={
                "total": len(users),
                "active": active,
                "admin": admins,
                "inactive": len(users) - active,
            },
            questions={
                "total": len(questions),
                "by_difficulty": diff_dist,
            },
            courses={
                "total": len(tree.get("courses", [])),
                "modules": len(tree.get("modules", [])),
                "lessons": len(tree.get("lessons", [])),
            },
            system={
                "storage": "file",
                "version": "1.0.0",
            },
            generation={
                "total_jobs": 0,
                "pending": 0,
                "completed": 0,
            },
        )

    async def get_course_progress_by_user(
        self, user_id: str
    ) -> List[CourseProgressDetail]:
        progress = self._load_progress()
        results = []
        for p in progress:
            if p.get("user_id") == user_id:
                results.append(CourseProgressDetail(**p))
        return results
