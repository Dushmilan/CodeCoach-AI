import json
import os
from typing import Dict, List, Optional

from app.models.course_schemas import Course, Module, Lesson
from app.ports.course_repository import CourseRepository


class FileCourseRepository(CourseRepository):
    def __init__(
        self,
        courses_path: str,
        modules_path: str,
        lessons_path: str,
    ):
        self.courses_path = courses_path
        self.modules_path = modules_path
        self.lessons_path = lessons_path
        self._courses: Dict[str, Course] = {}
        self._modules: Dict[str, Module] = {}
        self._lessons: Dict[str, Lesson] = {}
        self._load()

    def _load(self):
        self._load_file(self.courses_path, self._courses, Course)
        self._load_file(self.modules_path, self._modules, Module)
        self._load_file(self.lessons_path, self._lessons, Lesson)

    def _load_file(self, path: str, target: Dict, model):
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = data.get("items", [])
        for item in data:
            obj = model(**item)
            target[obj.id] = obj

    async def get_all_courses(self) -> List[Course]:
        return list(self._courses.values())

    async def get_course_by_id(self, course_id: str) -> Optional[Course]:
        return self._courses.get(course_id)

    async def get_module_by_id(self, module_id: str) -> Optional[Module]:
        return self._modules.get(module_id)

    async def get_lesson_by_id(self, lesson_id: str) -> Optional[Lesson]:
        return self._lessons.get(lesson_id)

    async def get_lessons_by_module(self, module_id: str) -> List[Lesson]:
        module = self._modules.get(module_id)
        if not module:
            return []
        return [
            self._lessons[lesson_id]
            for lesson_id in module.lessons
            if lesson_id in self._lessons
        ]

    async def get_modules_by_course(self, course_id: str) -> List[Module]:
        course = self._courses.get(course_id)
        if not course:
            return []
        return [
            self._modules[module_id]
            for module_id in course.modules
            if module_id in self._modules
        ]
