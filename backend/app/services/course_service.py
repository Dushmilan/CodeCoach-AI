from datetime import datetime, timezone
from typing import List, Optional

from app.models.course_schemas import Course, CourseProgress, CourseSummary, Lesson
from app.ports.course_repository import CourseRepository
from app.ports.progress_repository import ProgressRepository
from app.services.redis_service import RedisCache


class CourseService:
    def __init__(
        self,
        course_repo: CourseRepository,
        progress_repo: ProgressRepository,
        cache: Optional[RedisCache] = None,
    ):
        self.course_repo = course_repo
        self.progress_repo = progress_repo
        self.cache = cache

    async def list_courses(self, user_id: Optional[str] = None) -> List[CourseSummary]:
        courses = await self.course_repo.get_all_courses()
        courses.sort(key=lambda c: c.order)

        all_modules_by_id = {}
        if user_id and courses:
            all_modules = await self.course_repo.get_modules_by_course_batch(
                [c.id for c in courses]
            )
            all_modules_by_id = {m.id: m for m in all_modules}

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
                        module = all_modules_by_id.get(module_id)
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

    async def get_course_with_modules(self, course_id: str) -> Optional[dict]:
        if self.cache:
            cache_key = RedisCache.key("courses", "detail", course_id)
            cached = await self.cache.get(cache_key)
            if cached is not None:
                return cached

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
            lessons.sort(key=lambda le: le.order)
            mod_dict["lessons"] = [le.model_dump() for le in lessons]
            result["modules"].append(mod_dict)

        if self.cache:
            await self.cache.set(
                RedisCache.key("courses", "detail", course_id),
                result,
                ttl=3600,
            )

        return result

    async def get_lesson(self, lesson_id: str) -> Optional[Lesson]:
        if self.cache:
            cache_key = RedisCache.key("courses", "lesson", lesson_id)
            cached = await self.cache.get(cache_key)
            if cached is not None:
                return Lesson(**cached)

        lesson = await self.course_repo.get_lesson_by_id(lesson_id)

        if self.cache and lesson is not None:
            await self.cache.set(
                RedisCache.key("courses", "lesson", lesson_id),
                lesson.model_dump(),
                ttl=3600,
            )

        return lesson

    async def mark_lesson_complete(self, user_id: str, course_id: str, lesson_id: str):
        return await self.progress_repo.mark_lesson_complete(
            user_id, course_id, lesson_id
        )

    async def get_progress(self, user_id: str, course_id: str):
        return await self.progress_repo.get_progress(user_id, course_id)

    async def get_all_progress(self, user_id: str):
        return await self.progress_repo.get_all_progress(user_id)

    async def track_lesson_access(self, user_id: str, course_id: str, lesson_id: str):
        progress = await self.progress_repo.get_progress(user_id, course_id)
        if progress is None:
            progress = CourseProgress(
                user_id=user_id,
                course_id=course_id,
                completed_lessons=[],
                last_accessed_lesson_id=lesson_id,
            )
        else:
            progress.last_accessed_lesson_id = lesson_id
            progress.last_accessed_at = datetime.now(timezone.utc)
        await self.progress_repo.save(progress)
