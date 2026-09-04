import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional

from app.models.course_schemas import Course, CourseProgress, CourseSummary, Lesson
from app.ports.course_repository import CourseRepository
from app.ports.progress_repository import ProgressRepository
from app.services.redis_service import RedisCache

logger = logging.getLogger(__name__)

# Anonymous course list is identical for every visitor — cache it in Redis so
# every backend replica shares one entry (avoids repeated Supabase roundtrips
# and intermittent 408s on a cold pool).
_ANON_LIST_KEY = RedisCache.key("courses", "list", "anonymous")
_ANON_LIST_LOCK_KEY = RedisCache.key("courses", "list", "anonymous", "lock")
# Stampede protection: SET NX lock so only one worker rebuilds on a miss.
# Losers poll briefly, then build directly (fail-safe — never block the hot path).
_ANON_LIST_LOCK_TTL = 10
_ANON_LIST_LOCK_POLLS = 20
_ANON_LIST_LOCK_POLL_INTERVAL = 0.05


async def invalidate_anonymous_course_list_cache(
    cache: Optional[RedisCache],
) -> None:
    """Drop the cached anonymous course list after a catalog write.

    Best-effort: cache failures must never break admin mutations.
    """
    if cache is None:
        return
    try:
        await cache.delete(_ANON_LIST_KEY)
    except Exception as exc:  # noqa: BLE001 - invalidation is best-effort
        logger.debug("Course-list cache invalidation failed: %s", exc)


class CourseService:
    def __init__(
        self,
        course_repo: CourseRepository,
        progress_repo: ProgressRepository,
        cache: Optional[RedisCache] = None,
        list_ttl: int = 30,
    ):
        self.course_repo = course_repo
        self.progress_repo = progress_repo
        self.cache = cache
        self.list_ttl = list_ttl

    async def list_courses(self, user_id: Optional[str] = None) -> List[CourseSummary]:
        # Anonymous list is the same for everyone — serve from the shared
        # Redis entry. Authenticated lists embed per-user progress and bypass
        # the cache.
        if user_id is None and self.cache is not None:
            return await self._list_courses_anonymous_cached()
        return await self._build_summaries(user_id)

    async def _list_courses_anonymous_cached(self) -> List[CourseSummary]:
        try:
            cached = await self.cache.get(_ANON_LIST_KEY)  # type: ignore[union-attr]
            if cached is not None:
                return [CourseSummary(**s) for s in cached]
        except Exception as exc:  # noqa: BLE001 - cache must never break listing
            logger.debug("Course-list Redis read failed: %s", exc)
            return await self._build_summaries(None)

        try:
            acquired = await self.cache.set_if_absent(  # type: ignore[union-attr]
                _ANON_LIST_LOCK_KEY, "1", ttl=_ANON_LIST_LOCK_TTL
            )
        except Exception as exc:  # noqa: BLE001 - cache must never break listing
            logger.debug("Course-list Redis lock failed: %s", exc)
            return await self._build_summaries(None)

        if acquired:
            # Winner rebuilds. DB errors propagate (route maps them to 500);
            # only the cache write itself is best-effort.
            summaries = await self._build_summaries(None)
            try:
                await self.cache.set(  # type: ignore[union-attr]
                    _ANON_LIST_KEY,
                    [s.model_dump() for s in summaries],
                    ttl=self.list_ttl,
                )
            except Exception as exc:  # noqa: BLE001 - cache must never break listing
                logger.debug("Course-list Redis write failed: %s", exc)
            finally:
                try:
                    await self.cache.delete(_ANON_LIST_LOCK_KEY)  # type: ignore[union-attr]
                except Exception:  # noqa: BLE001 - lock auto-expires via TTL
                    pass
            return summaries
        else:
            # Another worker is rebuilding — wait briefly for its value,
            # then fall back to a direct build (fail-safe under lock stalls).
            for _ in range(_ANON_LIST_LOCK_POLLS):
                await asyncio.sleep(_ANON_LIST_LOCK_POLL_INTERVAL)
                try:
                    cached = await self.cache.get(_ANON_LIST_KEY)  # type: ignore[union-attr]
                except Exception:  # noqa: BLE001 - fall through to direct build
                    break
                if cached is not None:
                    return [CourseSummary(**s) for s in cached]
            return await self._build_summaries(None)

    async def _build_summaries(self, user_id: Optional[str]) -> List[CourseSummary]:
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
