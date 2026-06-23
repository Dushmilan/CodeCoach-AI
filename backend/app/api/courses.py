from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from app.models.course_schemas import Lesson
from app.ports.course_repository import CourseRepository
from app.ports.progress_repository import ProgressRepository
from app.services.course_service import CourseService
from app.services.redis_service import RedisCache
from app.api.auth import get_optional_current_user
from app.api.dependencies import get_course_repo, get_progress_repo, get_redis_cache
from app.models.auth_schemas import UserResponse

router = APIRouter()


def get_course_service(
    course_repo: CourseRepository = Depends(get_course_repo),
    progress_repo: ProgressRepository = Depends(get_progress_repo),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
) -> CourseService:
    return CourseService(
        course_repo=course_repo, progress_repo=progress_repo, cache=cache
    )


@router.get("/")
async def list_courses(
    current_user: Optional[UserResponse] = Depends(get_optional_current_user),
    course_service: CourseService = Depends(get_course_service),
):
    try:
        courses = await course_service.list_courses(
            user_id=current_user.id if current_user else None
        )
        return {"courses": courses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching courses: {str(e)}")


@router.get("/{course_id}")
async def get_course(
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching course: {str(e)}")


@router.get("/lessons/{lesson_id}", response_model=Lesson)
async def get_lesson(
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching lesson: {str(e)}")


@router.get("/lessons/{lesson_id}/adjacent")
async def get_adjacent_lessons(
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
