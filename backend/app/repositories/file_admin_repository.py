"""File-based admin repository for non-DB mode."""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from app.models.auth_schemas import UserInDB
from app.models.admin_models import (
    StatsResponse,
    QuestionFilter,
    QuestionImportResult,
    FeatureFlagUpdate,
    CourseProgressDetail,
    AuditLogFilter,
)
from app.ports.admin_repository import AdminRepository

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class FileAdminRepository(AdminRepository):
    """File-based admin repository. Delegates to existing file repos."""

    def __init__(
        self,
        users_file: str = "",
        questions_file: str = "",
        courses_dir: str = "",
        progress_file: str = "",
    ):
        self._users_file = Path(users_file or BASE_DIR / "data" / "users.json")
        self._questions_file = Path(
            questions_file or BASE_DIR / "questions" / "sample_questions.json"
        )
        self._courses_dir = Path(courses_dir or BASE_DIR / "data" / "courses")
        self._progress_file = Path(
            progress_file or BASE_DIR / "data" / "user_progress.json"
        )

    def _load_users(self) -> List[Dict[str, Any]]:
        if not self._users_file.exists():
            return []
        with open(self._users_file) as f:
            return json.load(f)

    def _save_users(self, users: List[Dict[str, Any]]):
        self._users_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._users_file, "w") as f:
            json.dump(users, f, indent=2)

    def _load_questions(self) -> List[Dict[str, Any]]:
        if not self._questions_file.exists():
            return []
        with open(self._questions_file) as f:
            return json.load(f)

    def _save_questions(self, questions: List[Dict[str, Any]]):
        self._questions_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._questions_file, "w") as f:
            json.dump(questions, f, indent=2)

    def _load_courses(self) -> Dict[str, Any]:
        tree = {"courses": [], "modules": [], "lessons": []}
        if not self._courses_dir.exists():
            return tree
        for path in self._courses_dir.rglob("*.json"):
            try:
                with open(path) as f:
                    tree["courses"].append(json.load(f))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Skipping %s: %s", path, e)
        return tree

    def _load_progress(self) -> List[Dict[str, Any]]:
        if not self._progress_file.exists():
            return []
        with open(self._progress_file) as f:
            return json.load(f)

    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        for u in self._load_users():
            if u.get("id") == user_id:
                return UserInDB(**u)
        return None

    async def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        for u in self._load_users():
            if u.get("username") == username:
                return UserInDB(**u)
        return None

    async def update_user_role(
        self, user_id: str, role: str, current_user_id: str
    ) -> bool:
        users = self._load_users()
        for u in users:
            if u["id"] == user_id:
                if u["id"] == current_user_id:
                    return False
                u["role"] = role
                self._save_users(users)
                return True
        return False

    async def update_user_status(
        self, user_id: str, is_active: bool, current_user_id: str
    ) -> bool:
        users = self._load_users()
        for u in users:
            if u["id"] == user_id:
                if u["id"] == current_user_id:
                    return False
                u["is_active"] = is_active
                self._save_users(users)
                return True
        return False

    async def list_users(
        self, skip: int = 0, limit: int = 20
    ) -> Tuple[List[UserInDB], int]:
        users = self._load_users()
        parsed = [UserInDB(**u) for u in users]
        return parsed[skip : skip + limit], len(parsed)

    async def get_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        for q in self._load_questions():
            if q.get("id") == question_id:
                return q
        return None

    async def update_question(
        self, question_id: str, update_data: Dict[str, Any]
    ) -> bool:
        questions = self._load_questions()
        for q in questions:
            if q["id"] == question_id:
                q.update(update_data)
                self._save_questions(questions)
                return True
        return False

    async def delete_question(self, question_id: str) -> bool:
        questions = self._load_questions()
        for i, q in enumerate(questions):
            if q["id"] == question_id:
                questions.pop(i)
                self._save_questions(questions)
                return True
        return False

    async def list_questions(
        self, filter: QuestionFilter
    ) -> Tuple[List[Dict[str, Any]], int]:
        all_q = self._load_questions()
        filtered = all_q
        if filter.difficulty:
            filtered = [q for q in filtered if q.get("difficulty") == filter.difficulty]
        if filter.category:
            filtered = [q for q in filtered if q.get("category") == filter.category]
        total = len(filtered)
        start = (filter.page - 1) * filter.per_page
        return filtered[start : start + filter.per_page], total

    async def import_questions(
        self, questions: List[Dict[str, Any]], dry_run: bool = False
    ) -> QuestionImportResult:
        result = QuestionImportResult(
            total=len(questions), successful=0, failed=0, errors=[]
        )
        if dry_run:
            result.successful = len(questions)
            return result
        existing = self._load_questions()
        for q in questions:
            if "id" not in q:
                q["id"] = str(uuid.uuid4())
            existing.append(q)
            result.successful += 1
        self._save_questions(existing)
        return result

    async def get_course_tree(self) -> Dict[str, Any]:
        return self._load_courses()

    async def delete_course(self, course_id: str) -> bool:
        tree = self._load_courses()
        for i, c in enumerate(tree["courses"]):
            if c.get("id") == course_id:
                tree["courses"].pop(i)
                return True
        return False

    async def delete_module(self, module_id: str) -> bool:
        tree = self._load_courses()
        for i, m in enumerate(tree.get("modules", [])):
            if m.get("id") == module_id:
                tree["modules"].pop(i)
                return True
        return False

    async def delete_lesson(self, lesson_id: str) -> bool:
        tree = self._load_courses()
        for i, lesson in enumerate(tree.get("lessons", [])):
            if lesson.get("id") == lesson_id:
                tree["lessons"].pop(i)
                return True
        return False

    async def get_generation_jobs(
        self, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        return []

    async def get_generation_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        return None

    async def update_generation_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        return True

    async def get_feature_flags(self) -> Dict[str, Any]:
        return {
            "question_generation": {
                "enabled": True,
                "rollout_pct": 100,
                "target_roles": ["admin", "super_admin"],
            },
            "audit_logging": {
                "enabled": True,
                "rollout_pct": 100,
                "target_roles": ["super_admin"],
            },
            "experimental_languages": {
                "enabled": False,
                "rollout_pct": 0,
                "target_roles": ["admin", "super_admin"],
            },
        }

    async def update_feature_flag(self, key: str, updates: FeatureFlagUpdate) -> bool:
        return True

    async def get_audit_logs(
        self, filter: AuditLogFilter, skip: int = 0, limit: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        return [], 0

    async def get_system_stats(self) -> StatsResponse:
        users = self._load_users()
        questions = self._load_questions()
        tree = self._load_courses()

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

    async def generate_user_role_grant_report(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        return []
