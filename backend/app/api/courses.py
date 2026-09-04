from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional
import logging

from app.models.course_schemas import Lesson
from app.ports.course_repository import CourseRepository
from app.ports.progress_repository import ProgressRepository
from app.services.course_service import CourseService
from app.services.redis_service import RedisCache
from app.api.auth_deps import get_optional_current_user
from app.api.dependencies import get_course_repo, get_progress_repo, get_redis_cache
from app.core.config import Settings, get_settings
from app.models.auth_schemas import UserResponse
from app.middleware.rate_limit import limiter, QUESTIONS_RATE_LIMIT

logger = logging.getLogger(__name__)

router = APIRouter()


def get_course_service(
    course_repo: CourseRepository = Depends(get_course_repo),
    progress_repo: ProgressRepository = Depends(get_progress_repo),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
    settings: Settings = Depends(get_settings),
) -> CourseService:
    return CourseService(
        course_repo=course_repo,
        progress_repo=progress_repo,
        cache=cache,
        list_ttl=settings.COURSE_LIST_TTL_SECONDS,
    )


@router.get("")
@router.get("/")
@limiter.limit(QUESTIONS_RATE_LIMIT)
async def list_courses(
    request: Request,
    current_user: Optional[UserResponse] = Depends(get_optional_current_user),
    course_service: CourseService = Depends(get_course_service),
):
    try:
        courses = await course_service.list_courses(
            user_id=current_user.id if current_user else None
        )
        return {"courses": courses}
    except Exception:
        logger.exception("Failed to fetch courses")
        raise HTTPException(status_code=500, detail="Failed to fetch courses")


@router.get("/{course_id}")
@limiter.limit(QUESTIONS_RATE_LIMIT)
async def get_course(
    request: Request,
    course_id: str,
    course_service: CourseService = Depends(get_course_service),
):
    try:
        course = await course_service.get_course_with_modules(course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return course
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to fetch course %s", course_id)
        raise HTTPException(status_code=500, detail="Failed to fetch course")


@router.get("/lessons/{lesson_id}", response_model=Lesson)
@limiter.limit(QUESTIONS_RATE_LIMIT)
async def get_lesson(
    request: Request,
    lesson_id: str,
    course_service: CourseService = Depends(get_course_service),
):
    try:
        lesson = await course_service.get_lesson(lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        return lesson
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to fetch lesson %s", lesson_id)
        raise HTTPException(status_code=500, detail="Failed to fetch lesson")


@router.get("/lessons/{lesson_id}/adjacent")
@limiter.limit(QUESTIONS_RATE_LIMIT)
async def get_adjacent_lessons(
    request: Request,
    lesson_id: str,
    course_service: CourseService = Depends(get_course_service),
):
    try:
        lesson = await course_service.get_lesson(lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        course = await course_service.get_course_with_modules(lesson.course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        all_lessons = [
            (m["order"], lesson["order"], lesson["id"])
            for m in course["modules"]
            for lesson in m["lessons"]
        ]
        all_lessons.sort()
        flat_ids = [lid for _, _, lid in all_lessons]

        try:
            current_idx = flat_ids.index(lesson_id)
        except ValueError:
            return {"prev_id": None, "next_id": None}

        return {
            "prev_id": flat_ids[current_idx - 1] if current_idx > 0 else None,
            "next_id": flat_ids[current_idx + 1]
            if current_idx < len(flat_ids) - 1
            else None,
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to resolve adjacent lessons for %s", lesson_id)
        raise HTTPException(
            status_code=500, detail="Failed to resolve adjacent lessons"
        )
