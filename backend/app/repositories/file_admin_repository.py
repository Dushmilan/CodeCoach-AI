"""File-based admin repository for non-DB mode."""

import json
import logging
import uuid
import shutil
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

    # ── Internal helpers ─────────────────────────────────

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
                    data = json.load(f)
                if path.name == "course.json":
                    tree["courses"].append(data)
                elif path.name == "modules.json":
                    tree["modules"].extend(data.get("items", []))
                elif path.name == "lessons.json":
                    tree["lessons"].extend(data.get("items", []))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Skipping %s: %s", path, e)
        return tree

    def _load_progress(self) -> List[Dict[str, Any]]:
        if not self._progress_file.exists():
            return []
        with open(self._progress_file) as f:
            return json.load(f)

    def _course_dir(self, course_id: str) -> Path:
        return self._courses_dir / course_id

    def _read_json(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        with open(path) as f:
            return json.load(f)

    def _write_json(self, path: Path, data: Any):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    # ── User operations ──────────────────────────────────

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

    # ── Question operations ──────────────────────────────

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

    # ── Course tree ──────────────────────────────────────

    async def get_course_tree(self) -> Dict[str, Any]:
        return self._load_courses()

    async def delete_course(self, course_id: str) -> bool:
        course_dir = self._course_dir(course_id)
        if not course_dir.exists():
            return False
        shutil.rmtree(course_dir)
        return True

    async def delete_module(self, module_id: str) -> bool:
        tree = self._load_courses()
        module_to_del = None
        for m in tree.get("modules", []):
            if m.get("id") == module_id:
                module_to_del = m
                break
        if not module_to_del:
            return False

        course_id = module_to_del.get("course_id")
        course_dir = self._course_dir(course_id)
        if not course_dir.exists():
            return False

        # Remove from modules.json
        modules_path = course_dir / "modules.json"
        modules_data = self._read_json(modules_path)
        modules_data["items"] = [
            m for m in modules_data.get("items", []) if m.get("id") != module_id
        ]
        self._write_json(modules_path, modules_data)

        # Remove module ID from parent course's modules list
        course_path = course_dir / "course.json"
        course_data = self._read_json(course_path)
        course_data["modules"] = [
            mid for mid in course_data.get("modules", []) if mid != module_id
        ]
        self._write_json(course_path, course_data)

        # Remove associated lessons
        lessons_path = course_dir / "lessons.json"
        if lessons_path.exists():
            lessons_data = self._read_json(lessons_path)
            lessons_data["items"] = [
                les
                for les in lessons_data.get("items", [])
                if les.get("module_id") != module_id
            ]
            self._write_json(lessons_path, lessons_data)

        return True

    async def delete_lesson(self, lesson_id: str) -> bool:
        tree = self._load_courses()
        lesson_to_del = None
        for les in tree.get("lessons", []):
            if les.get("id") == lesson_id:
                lesson_to_del = les
                break
        if not lesson_to_del:
            return False

        course_id = lesson_to_del.get("course_id")
        module_id = lesson_to_del.get("module_id")
        course_dir = self._course_dir(course_id)
        if not course_dir.exists():
            return False

        lessons_path = course_dir / "lessons.json"
        lessons_data = self._read_json(lessons_path)
        lessons_data["items"] = [
            les for les in lessons_data.get("items", []) if les.get("id") != lesson_id
        ]
        self._write_json(lessons_path, lessons_data)

        # Remove lesson ID from parent module's lessons list
        if module_id:
            modules_path = course_dir / "modules.json"
            modules_data = self._read_json(modules_path)
            for mod in modules_data.get("items", []):
                if mod.get("id") == module_id:
                    mod["lessons"] = [
                        lid for lid in mod.get("lessons", []) if lid != lesson_id
                    ]
                    break
            self._write_json(modules_path, modules_data)

        return True

    # ── Curriculum CRUD ──────────────────────────────────

    async def create_course(self, data: Dict[str, Any]) -> Dict[str, Any]:
        course_id = data["id"]
        course_dir = self._course_dir(course_id)
        if course_dir.exists():
            raise FileExistsError(f"Course '{course_id}' already exists")

        course_dir.mkdir(parents=True, exist_ok=True)

        course = {
            "id": course_id,
            "title": data["title"],
            "description": data.get("description", ""),
            "language": data.get("language", ""),
            "icon": data.get("icon", "code"),
            "order": data.get("order", 1),
        }
        self._write_json(course_dir / "course.json", course)
        self._write_json(course_dir / "modules.json", {"items": []})
        self._write_json(course_dir / "lessons.json", {"items": []})
        return course

    async def update_course(self, course_id: str, data: Dict[str, Any]) -> bool:
        course_dir = self._course_dir(course_id)
        course_path = course_dir / "course.json"
        if not course_path.exists():
            return False

        course = self._read_json(course_path)
        for key in ("title", "description", "language", "icon", "order"):
            if key in data:
                course[key] = data[key]
        self._write_json(course_path, course)
        return True

    async def create_module(self, data: Dict[str, Any]) -> Dict[str, Any]:
        course_id = data["course_id"]
        course_dir = self._course_dir(course_id)
        if not course_dir.exists():
            raise FileNotFoundError(f"Course '{course_id}' not found")

        module = {
            "id": data["id"],
            "course_id": course_id,
            "title": data["title"],
            "description": data.get("description", ""),
            "order": data.get("order", 1),
            "lessons": [],
        }

        modules_path = course_dir / "modules.json"
        modules_data = self._read_json(modules_path)
        modules_data.setdefault("items", []).append(module)
        self._write_json(modules_path, modules_data)

        # Add module ID to parent course's modules list
        course_path = course_dir / "course.json"
        course_data = self._read_json(course_path)
        course_data.setdefault("modules", []).append(data["id"])
        self._write_json(course_path, course_data)

        return module

    async def update_module(self, module_id: str, data: Dict[str, Any]) -> bool:
        tree = self._load_courses()
        module = None
        for m in tree.get("modules", []):
            if m.get("id") == module_id:
                module = m
                break
        if not module:
            return False

        course_dir = self._course_dir(module["course_id"])
        modules_path = course_dir / "modules.json"
        if not modules_path.exists():
            return False

        modules_data = self._read_json(modules_path)
        for m in modules_data.get("items", []):
            if m["id"] == module_id:
                for key in ("title", "description", "order"):
                    if key in data:
                        m[key] = data[key]
                self._write_json(modules_path, modules_data)
                return True
        return False

    async def create_lesson(self, data: Dict[str, Any]) -> Dict[str, Any]:
        course_id = data["course_id"]
        course_dir = self._course_dir(course_id)
        if not course_dir.exists():
            raise FileNotFoundError(f"Course '{course_id}' not found")

        lesson = {
            "id": data["id"],
            "course_id": course_id,
            "module_id": data["module_id"],
            "title": data["title"],
            "type": data.get("type", "theory"),
            "content": data.get("content", ""),
            "order": data.get("order", 1),
            "language": data.get("language", ""),
        }
        if "starter_code" in data and data["starter_code"]:
            lesson["starter_code"] = data["starter_code"]
        if "test_cases" in data and data["test_cases"]:
            lesson["test_cases"] = data["test_cases"]
        if "question_id" in data and data["question_id"]:
            lesson["question_id"] = data["question_id"]

        lessons_path = course_dir / "lessons.json"
        lessons_data = self._read_json(lessons_path)
        lessons_data.setdefault("items", []).append(lesson)
        self._write_json(lessons_path, lessons_data)

        # Add lesson ID to parent module's lessons list in modules.json
        module_id = data["module_id"]
        modules_path = course_dir / "modules.json"
        modules_data = self._read_json(modules_path)
        for mod in modules_data.get("items", []):
            if mod.get("id") == module_id:
                mod.setdefault("lessons", []).append(data["id"])
                break
        self._write_json(modules_path, modules_data)

        return lesson

    async def update_lesson(self, lesson_id: str, data: Dict[str, Any]) -> bool:
        tree = self._load_courses()
        lesson = None
        for les in tree.get("lessons", []):
            if les.get("id") == lesson_id:
                lesson = les
                break
        if not lesson:
            return False

        course_dir = self._course_dir(lesson["course_id"])
        lessons_path = course_dir / "lessons.json"
        if not lessons_path.exists():
            return False

        lessons_data = self._read_json(lessons_path)
        for les in lessons_data.get("items", []):
            if les["id"] == lesson_id:
                for key in (
                    "title",
                    "type",
                    "content",
                    "order",
                    "starter_code",
                    "test_cases",
                    "question_id",
                    "language",
                ):
                    if key in data:
                        les[key] = data[key]
                self._write_json(lessons_path, lessons_data)
                return True
        return False

    async def create_question(self, data: Dict[str, Any]) -> Dict[str, Any]:
        questions = self._load_questions()

        question = {
            "id": data["id"],
            "title": data["title"],
            "difficulty": data.get("difficulty", "medium"),
            "category": data.get("category", ""),
            "company_tags": data.get("company_tags", []),
            "description": data.get("description", ""),
            "starter_code": data.get(
                "starter_code", {"python": "", "javascript": "", "java": ""}
            ),
            "examples": data.get("examples", []),
            "test_cases": data.get("test_cases", []),
            "hints": data.get("hints", []),
            "solution": data.get("solution", None),
            "time_complexity": data.get("time_complexity", ""),
            "space_complexity": data.get("space_complexity", ""),
            "constraints": data.get("constraints", []),
            "is_interactive": data.get("is_interactive", False),
        }
        questions.append(question)
        self._save_questions(questions)
        return question

    # ── Stats ────────────────────────────────────────────

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
