"""Professor curriculum API (Issue #185) — owned-course scoped CRUD.

Professors manage only their own courses via ``/api/professor/*``:

- tree lists owned courses only (cross-owner rows invisible)
- create stamps ``owner_id`` with the caller
- update of a foreign course/module/lesson -> 403 (404 when unknown)
- deletes are admin-only -> 403 for professors
- guarded by ``require_professor`` (professor + admin + super_admin);
  students and TAs get 403

Deletes stay on ``/api/admin/*``; the DELETE stubs below exist so a
professor hitting the parallel professor path gets an explicit 403
instead of a misleading 404.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.admin import _invalidate_course_caches
from app.api.auth_deps import require_professor
from app.api.dependencies import get_course_admin_repo, get_redis_cache
from app.models.admin_models import (
    CourseCreate,
    CourseUpdate,
    LessonCreate,
    LessonUpdate,
    ModuleCreate,
    ModuleUpdate,
)
from app.models.auth_schemas import UserResponse
from app.ports.course_admin_repository import CourseAdminRepository
from app.services.redis_service import RedisCache

logger = logging.getLogger(__name__)

router = APIRouter()

_DELETE_FORBIDDEN = "Deletes are admin-only"


async def _owned_course_id_for_module(
    repo: CourseAdminRepository,
    module_id: str,
) -> Optional[str]:
    return await repo.get_module_course(module_id)


async def _owned_course_id_for_lesson(
    repo: CourseAdminRepository,
    lesson_id: str,
) -> Optional[str]:
    return await repo.get_lesson_course(lesson_id)


async def _require_course_owner(
    repo: CourseAdminRepository,
    course_id: str,
    user_id: str,
) -> None:
    """404 when the course is unknown, 403 when owned by someone else."""
    owner = await repo.get_course_owner(course_id)
    if owner is None and not await repo.exists("course", course_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )
    if owner != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not the owning professor of this course",
        )


async def _require_module_owner(
    repo: CourseAdminRepository,
    module_id: str,
    user_id: str,
) -> None:
    course_id = await _owned_course_id_for_module(repo, module_id)
    if course_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Module not found"
        )
    await _require_course_owner(repo, course_id, user_id)


async def _require_lesson_owner(
    repo: CourseAdminRepository,
    lesson_id: str,
    user_id: str,
) -> None:
    course_id = await _owned_course_id_for_lesson(repo, lesson_id)
    if course_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found"
        )
    await _require_course_owner(repo, course_id, user_id)


@router.get("/courses/tree", response_model=dict)
async def get_owned_tree(
    repo: CourseAdminRepository = Depends(get_course_admin_repo),
    current_user: UserResponse = Depends(require_professor),
):
    """Tree scoped to courses owned by the caller."""
    try:
        return await repo.get_course_tree(owner_id=current_user.id)
    except Exception as e:
        logger.error(f"Error fetching professor course tree: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching course tree: {str(e)}",
        )


@router.post("/courses", response_model=dict)
async def create_owned_course(
    data: CourseCreate,
    repo: CourseAdminRepository = Depends(get_course_admin_repo),
    current_user: UserResponse = Depends(require_professor),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
):
    """Create a course stamped with the caller as owner."""
    try:
        payload = data.model_dump()
        payload["owner_id"] = current_user.id
        result = await repo.create_course(payload)
        logger.info(f"Course '{data.id}' created by professor {current_user.id}")
        await _invalidate_course_caches(cache)
        return result
    except FileExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating professor course: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating course: {str(e)}",
        )


@router.put("/courses/{course_id}", response_model=dict)
async def update_owned_course(
    course_id: str,
    data: CourseUpdate,
    repo: CourseAdminRepository = Depends(get_course_admin_repo),
    current_user: UserResponse = Depends(require_professor),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
):
    """Update an owned course; 404 when unknown, 403 when foreign."""
    await _require_course_owner(repo, course_id, current_user.id)
    try:
        success = await repo.update_course(
            course_id, data.model_dump(exclude_none=True)
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
            )
        logger.info(f"Course '{course_id}' updated by professor {current_user.id}")
        await _invalidate_course_caches(cache)
        return {"message": "Course updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating professor course {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating course: {str(e)}",
        )


@router.post("/modules", response_model=dict)
async def create_owned_module(
    data: ModuleCreate,
    repo: CourseAdminRepository = Depends(get_course_admin_repo),
    current_user: UserResponse = Depends(require_professor),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
):
    """Create a module under an owned course; 404/403 via the parent course."""
    await _require_course_owner(repo, data.course_id, current_user.id)
    try:
        result = await repo.create_module(data.model_dump())
        logger.info(f"Module '{data.id}' created by professor {current_user.id}")
        await _invalidate_course_caches(cache)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating professor module: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating module: {str(e)}",
        )


@router.put("/modules/{module_id}", response_model=dict)
async def update_owned_module(
    module_id: str,
    data: ModuleUpdate,
    repo: CourseAdminRepository = Depends(get_course_admin_repo),
    current_user: UserResponse = Depends(require_professor),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
):
    """Update a module in an owned course; 404 when unknown, 403 when foreign."""
    await _require_module_owner(repo, module_id, current_user.id)
    try:
        success = await repo.update_module(
            module_id, data.model_dump(exclude_none=True)
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Module not found"
            )
        logger.info(f"Module '{module_id}' updated by professor {current_user.id}")
        await _invalidate_course_caches(cache)
        return {"message": "Module updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating professor module {module_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating module: {str(e)}",
        )


@router.post("/lessons", response_model=dict)
async def create_owned_lesson(
    data: LessonCreate,
    repo: CourseAdminRepository = Depends(get_course_admin_repo),
    current_user: UserResponse = Depends(require_professor),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
):
    """Create a lesson in an owned course; module must belong to the course."""
    await _require_course_owner(repo, data.course_id, current_user.id)
    module_course = await repo.get_module_course(data.module_id)
    if module_course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Module not found"
        )
    if module_course != data.course_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Module does not belong to the given course",
        )
    try:
        result = await repo.create_lesson(data.model_dump())
        logger.info(f"Lesson '{data.id}' created by professor {current_user.id}")
        await _invalidate_course_caches(cache)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating professor lesson: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating lesson: {str(e)}",
        )


@router.put("/lessons/{lesson_id}", response_model=dict)
async def update_owned_lesson(
    lesson_id: str,
    data: LessonUpdate,
    repo: CourseAdminRepository = Depends(get_course_admin_repo),
    current_user: UserResponse = Depends(require_professor),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
):
    """Update a lesson in an owned course; 404 when unknown, 403 when foreign."""
    await _require_lesson_owner(repo, lesson_id, current_user.id)
    try:
        success = await repo.update_lesson(
            lesson_id, data.model_dump(exclude_none=True)
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found"
            )
        logger.info(f"Lesson '{lesson_id}' updated by professor {current_user.id}")
        await _invalidate_course_caches(cache)
        return {"message": "Lesson updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating professor lesson {lesson_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating lesson: {str(e)}",
        )


@router.delete("/courses/{course_id}", response_model=dict)
async def delete_course_forbidden(
    course_id: str,
    current_user: UserResponse = Depends(require_professor),
):
    """Deletes stay admin-only; professors get an explicit 403."""
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_DELETE_FORBIDDEN)


@router.delete("/modules/{module_id}", response_model=dict)
async def delete_module_forbidden(
    module_id: str,
    current_user: UserResponse = Depends(require_professor),
):
    """Deletes stay admin-only; professors get an explicit 403."""
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_DELETE_FORBIDDEN)


@router.delete("/lessons/{lesson_id}", response_model=dict)
async def delete_lesson_forbidden(
    lesson_id: str,
    current_user: UserResponse = Depends(require_professor),
):
    """Deletes stay admin-only; professors get an explicit 403."""
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_DELETE_FORBIDDEN)
