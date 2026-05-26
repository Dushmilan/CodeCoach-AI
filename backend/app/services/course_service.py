from typing import List, Optional

from app.models.course_schemas import Course, CourseSummary, Module, Lesson
from app.ports.course_repository import CourseRepository
from app.ports.progress_repository import ProgressRepository
from app.repositories.file_course_repository import FileCourseRepository
from app.repositories.file_progress_repository import FileProgressRepository

DATA_DIR = "data"


class CourseService:
    def __init__(
        self,
        course_repo: Optional[CourseRepository] = None,
        progress_repo: Optional[ProgressRepository] = None,
    ):
        self.course_repo = course_repo or FileCourseRepository(
            courses_path=f"{DATA_DIR}/courses.json",
            modules_path=f"{DATA_DIR}/modules.json",
            lessons_path=f"{DATA_DIR}/lessons.json",
        )
        self.progress_repo = progress_repo or FileProgressRepository(
            file_path=f"{DATA_DIR}/user_progress.json",
        )

    async def list_courses(self, user_id: Optional[str] = None) -> List[CourseSummary]:
        courses = await self.course_repo.get_all_courses()
        courses.sort(key=lambda c: c.order)
        summaries = []
        for course in courses:
            progress = 0.0
            if user_id:
                user_progress = await self.progress_repo.get_progress(
                    user_id, course.id
                )
                if user_progress:
                    module_lesson_count = 0
                    for module_id in course.modules:
                        module = await self.course_repo.get_module_by_id(module_id)
                        if module:
                            module_lesson_count += len(module.lessons)
                    if module_lesson_count > 0:
                        progress = round(
                            len(user_progress.completed_lessons)
                            / module_lesson_count
                            * 100,
                            1,
                        )
            summaries.append(
                CourseSummary(
                    id=course.id,
                    title=course.title,
                    description=course.description,
                    language=course.language,
                    icon=course.icon,
                    order=course.order,
                    progress=progress,
                )
            )
        return summaries

    async def get_course(self, course_id: str) -> Optional[Course]:
        return await self.course_repo.get_course_by_id(course_id)

    async def get_course_with_modules(
        self, course_id: str
    ) -> Optional[dict]:
        course = await self.course_repo.get_course_by_id(course_id)
        if not course:
            return None
        modules = await self.course_repo.get_modules_by_course(course_id)
        modules.sort(key=lambda m: m.order)
        result = course.model_dump()
        result["modules"] = []
        for mod in modules:
            mod_dict = mod.model_dump()
            lessons = await self.course_repo.get_lessons_by_module(mod.id)
            lessons.sort(key=lambda l: l.order)
            mod_dict["lessons"] = [l.model_dump() for l in lessons]
            result["modules"].append(mod_dict)
        return result

    async def get_lesson(self, lesson_id: str) -> Optional[Lesson]:
        return await self.course_repo.get_lesson_by_id(lesson_id)

    async def mark_lesson_complete(
        self, user_id: str, course_id: str, lesson_id: str
    ):
        return await self.progress_repo.mark_lesson_complete(
            user_id, course_id, lesson_id
        )

    async def get_progress(self, user_id: str, course_id: str):
        return await self.progress_repo.get_progress(user_id, course_id)

    async def get_all_progress(self, user_id: str):
        return await self.progress_repo.get_all_progress(user_id)
