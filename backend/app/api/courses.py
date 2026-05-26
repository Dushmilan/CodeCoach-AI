from fastapi import APIRouter, Depends, HTTPException
from functools import lru_cache

from app.models.course_schemas import Course, Lesson
from app.services.course_service import CourseService
from app.api.auth import get_current_user
from app.models.auth_schemas import UserResponse

router = APIRouter()


@lru_cache()
def get_course_service() -> CourseService:
    return CourseService()


@router.get("/")
async def list_courses(
    current_user: UserResponse = Depends(get_current_user),
    course_service: CourseService = Depends(get_course_service),
):
    try:
        courses = await course_service.list_courses(user_id=current_user.id)
        return {"courses": courses}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching courses: {str(e)}"
        )


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
        raise HTTPException(
            status_code=500, detail=f"Error fetching course: {str(e)}"
        )


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
        raise HTTPException(
            status_code=500, detail=f"Error fetching lesson: {str(e)}"
        )
