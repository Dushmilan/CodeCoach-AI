import json
import os
from typing import Dict, List, Optional

from app.models.course_schemas import Course, Module, Lesson
from app.ports.course_repository import CourseRepository


class FileCourseRepository(CourseRepository):
    def __init__(self, courses_dir: str):
        self.courses_dir = courses_dir
        self._courses: Dict[str, Course] = {}
        self._modules: Dict[str, Module] = {}
        self._lessons: Dict[str, Lesson] = {}
        self._load()

    def _load(self):
        for root, _, files in os.walk(self.courses_dir):
            if "course.json" in files:
                self._load_file(os.path.join(root, "course.json"), self._courses, Course)
            if "modules.json" in files:
                self._load_file(os.path.join(root, "modules.json"), self._modules, Module)
            if "lessons.json" in files:
                self._load_file(os.path.join(root, "lessons.json"), self._lessons, Lesson)

    def _load_file(self, path: str, target: Dict, model):
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if "items" in data:
            items = data["items"]
        else:
            items = [data]
            
        for item in items:
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
