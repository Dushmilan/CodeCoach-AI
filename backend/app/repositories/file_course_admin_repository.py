import json
import logging
import shutil
import threading
from pathlib import Path
from typing import Dict, Any

from app.ports.course_admin_repository import CourseAdminRepository

logger = logging.getLogger(__name__)


class FileCourseAdminRepository(CourseAdminRepository):
    def __init__(self, courses_dir: str = ""):
        self._courses_dir = Path(
            courses_dir
            or str(Path(__file__).resolve().parent.parent.parent / "data" / "courses")
        )
        self._lock = threading.Lock()

    def _course_dir(self, course_id: str) -> Path:
        return self._courses_dir / course_id

    def _read_json(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _write_json(self, path: Path, data: Any):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _load_courses(self) -> Dict[str, Any]:
        tree = {"courses": [], "modules": [], "lessons": []}
        if not self._courses_dir.exists():
            return tree
        for path in self._courses_dir.rglob("*.json"):
            try:
                with open(path, encoding="utf-8") as f:
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

    async def exists(self, entity_type: str, entity_id: str) -> bool:
        tree = self._load_courses()
        if entity_type == "course":
            return any(c.get("id") == entity_id for c in tree.get("courses", []))
        if entity_type == "module":
            return any(m.get("id") == entity_id for m in tree.get("modules", []))
        if entity_type == "lesson":
            return any(les.get("id") == entity_id for les in tree.get("lessons", []))
        return False

    async def get_course_tree(self) -> Dict[str, Any]:
        return self._load_courses()

    async def delete_course(self, course_id: str) -> bool:
        with self._lock:
            course_dir = self._course_dir(course_id)
            if not course_dir.exists():
                return False
            shutil.rmtree(course_dir)
            return True

    async def delete_module(self, module_id: str) -> bool:
        with self._lock:
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
            modules_path = course_dir / "modules.json"
            modules_data = self._read_json(modules_path)
            modules_data["items"] = [
                m for m in modules_data.get("items", []) if m.get("id") != module_id
            ]
            self._write_json(modules_path, modules_data)
            course_path = course_dir / "course.json"
            course_data = self._read_json(course_path)
            course_data["modules"] = [
                mid for mid in course_data.get("modules", []) if mid != module_id
            ]
            self._write_json(course_path, course_data)
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
        with self._lock:
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
                les
                for les in lessons_data.get("items", [])
                if les.get("id") != lesson_id
            ]
            self._write_json(lessons_path, lessons_data)
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

    async def create_course(self, data: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
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
        with self._lock:
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
        with self._lock:
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
            course_path = course_dir / "course.json"
            course_data = self._read_json(course_path)
            course_data.setdefault("modules", []).append(data["id"])
            self._write_json(course_path, course_data)
            return module

    async def update_module(self, module_id: str, data: Dict[str, Any]) -> bool:
        with self._lock:
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
        with self._lock:
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
        with self._lock:
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
