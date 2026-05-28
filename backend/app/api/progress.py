from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

from app.services.course_service import CourseService
from app.api.auth import get_current_user
from app.models.auth_schemas import UserResponse
from app.models.course_schemas import CourseProgress

router = APIRouter()


def get_course_service() -> CourseService:
    return CourseService()


@router.get("/")
async def get_all_progress(
    current_user: UserResponse = Depends(get_current_user),
    course_service: CourseService = Depends(get_course_service),
):
    try:
        progress = await course_service.get_all_progress(current_user.id)
        return {"progress": [p.model_dump() for p in progress]}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching progress: {str(e)}"
        )


@router.get("/{course_id}")
async def get_course_progress(
    course_id: str,
    current_user: UserResponse = Depends(get_current_user),
    course_service: CourseService = Depends(get_course_service),
):
    try:
        progress = await course_service.get_progress(current_user.id, course_id)
        if not progress:
            return {"completed_lessons": [], "progress": 0.0}
        return progress
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching progress: {str(e)}"
        )


@router.post("/{lesson_id}/complete")
async def mark_lesson_complete(
    lesson_id: str,
    course_id: str,
    current_user: UserResponse = Depends(get_current_user),
    course_service: CourseService = Depends(get_course_service),
):
    try:
        lesson = await course_service.get_lesson(lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        if lesson.course_id != course_id:
            raise HTTPException(
                status_code=400,
                detail="Lesson does not belong to the specified course",
            )
        progress = await course_service.mark_lesson_complete(
            current_user.id, course_id, lesson_id
        )
        return progress
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error marking lesson complete: {str(e)}"
        )


@router.post("/{lesson_id}/access")
async def track_lesson_access(
    lesson_id: str,
    course_id: str,
    current_user: UserResponse = Depends(get_current_user),
    course_service: CourseService = Depends(get_course_service),
):
    """Track that a user accessed a lesson (for 'Continue where you left off')."""
    try:
        lesson = await course_service.get_lesson(lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        if lesson.course_id != course_id:
            raise HTTPException(
                status_code=400,
                detail="Lesson does not belong to the specified course",
            )

        progress = await course_service.get_progress(current_user.id, course_id)
        if progress is None:
            progress = CourseProgress(
                user_id=current_user.id,
                course_id=course_id,
                completed_lessons=[],
                last_accessed_lesson_id=lesson_id,
            )
            await course_service.progress_repo.save(progress)
        else:
            progress.last_accessed_lesson_id = lesson_id
            progress.last_accessed_at = datetime.utcnow()
            await course_service.progress_repo.save(progress)

        return {"status": "ok", "last_accessed_lesson_id": lesson_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error tracking lesson access: {str(e)}"
        )
