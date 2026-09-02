import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from app.models.course_schemas import Course, CourseProgress, CourseSummary, Lesson
from app.ports.course_repository import CourseRepository
from app.ports.progress_repository import ProgressRepository
from app.services.redis_service import RedisCache

# In-memory TTL cache for anonymous course list (Supabase pooler ~1.5s per query; intermittent timeout on cold pool)
# Keyed by None (anonymous) — user-specific progress bypasses cache
_course_list_cache: Dict[str, Tuple[float, List[CourseSummary]]] = {}
_COURSE_LIST_TTL = 30.0


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
        # Anonymous list is same for everyone — cache to avoid repeated Supabase roundtrips and intermittent 408 on cold pool
        if not user_id:
            cached = _course_list_cache.get("anonymous")
            if cached and (time.time() - cached[0] < _COURSE_LIST_TTL):
                return cached[1]

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
        if not user_id:
            _course_list_cache["anonymous"] = (time.time(), summaries)
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
        # Batch fetch lesson outlines (titles only) in single query — avoids N+1 roundtrips to Supabase pooler (~1-2s each)
        module_ids = [m.id for m in modules]
        all_lessons = []
        if hasattr(self.course_repo, "get_lesson_summaries_by_module_ids"):
            all_lessons = await self.course_repo.get_lesson_summaries_by_module_ids(
                module_ids
            )  # type: ignore
        else:
            # Fallback for in-memory test repos
            for mid in module_ids:
                all_lessons.extend(await self.course_repo.get_lessons_by_module(mid))
        # Group by module_id preserving order
        lessons_by_module: dict[str, list] = {mid: [] for mid in module_ids}
        for le in all_lessons:
            lessons_by_module.setdefault(le.module_id, []).append(le)
        for mod in modules:
            mod_dict = mod.model_dump()
            lessons = lessons_by_module.get(mod.id, [])
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
