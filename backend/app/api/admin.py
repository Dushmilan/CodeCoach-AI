from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List, Dict, Any
import logging

from app.ports.admin_repository import AdminRepository
from app.ports.user_admin_repository import UserAdminRepository
from app.ports.question_admin_repository import QuestionAdminRepository
from app.ports.course_admin_repository import CourseAdminRepository
from app.ports.usage_repository import UsageRepository
from app.ports.code_executor import CodeExecutor
from app.api.auth_deps import require_admin, require_super_admin
from app.api.dependencies import (
    get_admin_repo,
    get_user_admin_repo,
    get_question_admin_repo,
    get_course_admin_repo,
    get_executor,
    get_redis_cache,
    get_usage_repo,
)
from app.services.course_service import invalidate_anonymous_course_list_cache
from app.services.redis_service import RedisCache
from app.services.question_validator import QuestionValidatorService
from app.models.schemas import Question
from app.models.auth_schemas import UserResponse
from app.models.usage_schemas import (
    AbuseFlagOut,
    AbuseReportOut,
    RateLimitAnalytics,
    UsageSummary,
    UserUsageDetail,
)
from app.models.admin_models import (
    UserAdminUpdate,
    UserDetailResponse,
    StatsResponse,
    QuestionFilter,
    QuestionImportResult,
    CourseCreate,
    CourseUpdate,
    ModuleCreate,
    ModuleUpdate,
    LessonCreate,
    LessonUpdate,
    QuestionCreate,
    QuestionUpdate,
)

router = APIRouter()
logger = logging.getLogger(__name__)


async def _invalidate_course_caches(cache: Optional[RedisCache]) -> None:
    """Drop course catalog caches after admin curriculum mutations.

    Learners must see published/edited content immediately instead of
    waiting out the anonymous-list (30s) and detail (1h) TTLs.
    """
    await invalidate_anonymous_course_list_cache(cache)
    if cache is not None:
        try:
            await cache.delete(RedisCache.key("courses", "detail", "*"))
        except Exception as exc:  # noqa: BLE001 - invalidation is best-effort
            logger.debug("Course detail cache invalidation failed: %s", exc)


async def _invalidate_question_caches(cache: Optional[RedisCache]) -> None:
    """Drop question caches after admin question mutations (detail/stats TTL 5m)."""
    if cache is not None:
        await cache.delete("codecoach:questions:*")


# Dashboard and Analytics Endpoints
@router.get("/stats", response_model=StatsResponse)
async def get_admin_stats(
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Get system statistics and dashboard metrics."""
    try:
        stats = await admin_repo.get_system_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching admin stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching admin stats: {str(e)}",
        )


@router.get("/stats/users", response_model=dict)
async def get_user_stats(
    admin_repo: UserAdminRepository = Depends(get_user_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Get user statistics (admins only)."""
    try:
        # Load the full user list so active/admin counts are not truncated
        users, total = await admin_repo.list_users(skip=0, limit=1_000_000)

        # Calculate stats
        active_users = sum(1 for u in users if u.is_active)
        admin_users = sum(1 for u in users if u.role in ["admin", "super_admin"])

        return {
            "total": total,
            "active": active_users,
            "admin": admin_users,
            "inactive": total - active_users,
        }
    except Exception as e:
        logger.error(f"Error fetching user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user stats: {str(e)}",
        )


# User Management Endpoints
@router.get("/users", response_model=dict)
async def list_users(
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    admin_repo: UserAdminRepository = Depends(get_user_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """List all users with pagination and filtering (admins only)."""
    try:
        skip = (page - 1) * per_page
        if search:
            q = search.lower()
            all_users, _ = await admin_repo.list_users(skip=0, limit=1_000_000)
            all_users = [
                u for u in all_users if q in u.username.lower() or q in u.email.lower()
            ]
            total = len(all_users)
            page_users = all_users[skip : skip + per_page]
        else:
            page_users, total = await admin_repo.list_users(skip=skip, limit=per_page)

        user_list = []
        for user in page_users:
            user_list.append(
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_active": bool(user.is_active),
                    "role": user.role,
                    "created_at": user.created_at,
                }
            )

        return {
            "users": user_list,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page if per_page else 1,
        }
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing users: {str(e)}",
        )


@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: str,
    admin_repo: UserAdminRepository = Depends(get_user_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Get detailed user information (admins only)."""
    try:
        user = await admin_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return UserDetailResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=bool(user.is_active),
            role=user.role,
            oauth_provider=user.oauth_provider,
            oauth_id=user.oauth_id,
            created_at=user.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user: {str(e)}",
        )


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    user_data: UserAdminUpdate,
    admin_repo: UserAdminRepository = Depends(get_user_admin_repo),
    current_user: UserResponse = Depends(require_super_admin),
):
    """Update user role or status (super-admins only)."""
    try:
        if user_data.role and user_data.role not in ["user", "admin", "super_admin"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be 'user', 'admin', or 'super_admin'",
            )

        if user_data.role:
            success = await admin_repo.update_user_role(
                user_id, user_data.role, current_user.id
            )
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )
            logger.info(
                f"User {user_id} role updated by {current_user.id}: {user_data.role}"
            )

        if user_data.is_active is not None:
            success = await admin_repo.update_user_status(
                user_id, user_data.is_active, current_user.id
            )
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )
            logger.info(
                f"User {user_id} status updated by {current_user.id}: active={user_data.is_active}"
            )

        return {"message": "User updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}",
        )


# Question Management Endpoints
@router.get("/questions", response_model=dict)
async def list_questions(
    difficulty: Optional[str] = None,
    category: Optional[str] = None,
    has_solution: Optional[bool] = None,
    page: int = 1,
    per_page: int = 20,
    admin_repo: QuestionAdminRepository = Depends(get_question_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """List questions with filtering and pagination (admins only)."""
    try:
        filter = QuestionFilter(
            difficulty=difficulty,
            category=category,
            has_solution=has_solution,
            page=page,
            per_page=per_page,
        )

        questions, total = await admin_repo.list_questions(filter)

        return {
            "questions": questions,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        }
    except Exception as e:
        logger.error(f"Error listing questions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing questions: {str(e)}",
        )


@router.get("/questions/{question_id}", response_model=dict)
async def get_question(
    question_id: str,
    admin_repo: QuestionAdminRepository = Depends(get_question_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Get question details (admins only)."""
    try:
        question = await admin_repo.get_question_by_id(question_id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found",
            )

        return question
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching question {question_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching question: {str(e)}",
        )


@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: str,
    admin_repo: QuestionAdminRepository = Depends(get_question_admin_repo),
    current_user: UserResponse = Depends(require_admin),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
):
    """Delete a question (admins only)."""
    try:
        success = await admin_repo.delete_question(question_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found",
            )

        logger.info(f"Question {question_id} deleted by {current_user.id}")
        await _invalidate_question_caches(cache)
        return {"message": "Question deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting question {question_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting question: {str(e)}",
        )


@router.post("/questions/import", response_model=QuestionImportResult)
async def import_questions(
    questions: List[Dict[str, Any]],
    dry_run: bool = False,
    admin_repo: QuestionAdminRepository = Depends(get_question_admin_repo),
    current_user: UserResponse = Depends(require_admin),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
):
    """Import questions from JSON (admins only)."""
    try:
        if not questions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No questions provided",
            )

        result = await admin_repo.import_questions(questions, dry_run)

        if not dry_run:
            await _invalidate_question_caches(cache)
            logger.info(
                f"Questions imported by {current_user.id}: {result['successful']} successful, {result['failed']} failed"
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing questions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing questions: {str(e)}",
        )


@router.post("/questions/validate/{question_id}")
async def validate_question(
    question_id: str,
    admin_repo: QuestionAdminRepository = Depends(get_question_admin_repo),
    executor: CodeExecutor = Depends(get_executor),
    current_user: UserResponse = Depends(require_admin),
):
    """Run the full validation pipeline on a question (admins only)."""
    try:
        question = await admin_repo.get_question_by_id(question_id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found",
            )

        question_data = dict(question)
        if "starter_code" in question_data and "starter" not in question_data:
            question_data["starter"] = question_data.pop("starter_code")

        validator = QuestionValidatorService(executor=executor)
        result = await validator.validate_question(Question(**question_data))

        logger.info(
            f"Question {question_id} validated by {current_user.id}: "
            f"valid={result.valid}, issues={result.total_issues}"
        )
        return {
            "question_id": question_id,
            "valid": result.valid,
            "total_issues": result.total_issues,
            "error_count": result.error_count,
            "warning_count": result.warning_count,
            "results": {
                uc.value: {
                    "passed": r.passed,
                    "issues": [i.message for i in r.issues],
                }
                for uc, r in result.results.items()
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating question {question_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating question: {str(e)}",
        )


# Course Management Endpoints
@router.get("/courses/tree", response_model=dict)
async def get_course_tree(
    admin_repo: CourseAdminRepository = Depends(get_course_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Get courses tree structure (admins only)."""
    try:
        tree = await admin_repo.get_course_tree()
        return tree
    except Exception as e:
        logger.error(f"Error fetching course tree: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching course tree: {str(e)}",
        )


@router.delete("/courses/{course_id}")
async def delete_course(
    course_id: str,
    admin_repo: CourseAdminRepository = Depends(get_course_admin_repo),
    current_user: UserResponse = Depends(require_admin),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
):
    """Delete a course (admins only)."""
    try:
        success = await admin_repo.delete_course(course_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found",
            )
        logger.info(f"Course {course_id} deleted by {current_user.id}")
        await _invalidate_course_caches(cache)
        return {"message": "Course deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting course {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting course: {str(e)}",
        )


@router.delete("/modules/{module_id}")
async def delete_module(
    module_id: str,
    admin_repo: CourseAdminRepository = Depends(get_course_admin_repo),
    current_user: UserResponse = Depends(require_admin),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
):
    """Delete a module (admins only)."""
    try:
        success = await admin_repo.delete_module(module_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module not found",
            )
        logger.info(f"Module {module_id} deleted by {current_user.id}")
        await _invalidate_course_caches(cache)
        return {"message": "Module deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting module {module_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting module: {str(e)}",
        )


@router.delete("/lessons/{lesson_id}")
async def delete_lesson(
    lesson_id: str,
    admin_repo: CourseAdminRepository = Depends(get_course_admin_repo),
    current_user: UserResponse = Depends(require_admin),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
):
    """Delete a lesson (admins only)."""
    try:
        success = await admin_repo.delete_lesson(lesson_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found",
            )
        logger.info(f"Lesson {lesson_id} deleted by {current_user.id}")
        await _invalidate_course_caches(cache)
        return {"message": "Lesson deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting lesson {lesson_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting lesson: {str(e)}",
        )


# ── Curriculum CRUD Endpoints ───────────────────────────


@router.get("/check-id")
async def check_id_exists(
    entity_type: str,
    entity_id: str,
    admin_repo: CourseAdminRepository = Depends(get_course_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Check if an entity ID already exists."""
    exists = await admin_repo.exists(entity_type, entity_id)
    return {"exists": exists}


@router.post("/courses", response_model=dict)
async def create_course(
    data: CourseCreate,
    admin_repo: CourseAdminRepository = Depends(get_course_admin_repo),
    current_user: UserResponse = Depends(require_admin),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
):
    """Create a new course (admins only)."""
    try:
        result = await admin_repo.create_course(data.model_dump())
        logger.info(f"Course '{data.id}' created by {current_user.id}")
        await _invalidate_course_caches(cache)
        return result
    except FileExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating course: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating course: {str(e)}",
        )


@router.put("/courses/{course_id}", response_model=dict)
async def update_course(
    course_id: str,
    data: CourseUpdate,
    admin_repo: CourseAdminRepository = Depends(get_course_admin_repo),
    current_user: UserResponse = Depends(require_admin),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
):
    """Update a course (admins only)."""
    try:
        success = await admin_repo.update_course(
            course_id, data.model_dump(exclude_none=True)
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
            )
        logger.info(f"Course '{course_id}' updated by {current_user.id}")
        await _invalidate_course_caches(cache)
        return {"message": "Course updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating course {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating course: {str(e)}",
        )


@router.post("/modules", response_model=dict)
async def create_module(
    data: ModuleCreate,
    admin_repo: CourseAdminRepository = Depends(get_course_admin_repo),
    current_user: UserResponse = Depends(require_admin),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
):
    """Create a new module (admins only)."""
    try:
        result = await admin_repo.create_module(data.model_dump())
        logger.info(f"Module '{data.id}' created by {current_user.id}")
        await _invalidate_course_caches(cache)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating module: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating module: {str(e)}",
        )


@router.put("/modules/{module_id}", response_model=dict)
async def update_module(
    module_id: str,
    data: ModuleUpdate,
    admin_repo: CourseAdminRepository = Depends(get_course_admin_repo),
    current_user: UserResponse = Depends(require_admin),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
):
    """Update a module (admins only)."""
    try:
        success = await admin_repo.update_module(
            module_id, data.model_dump(exclude_none=True)
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Module not found"
            )
        logger.info(f"Module '{module_id}' updated by {current_user.id}")
        await _invalidate_course_caches(cache)
        return {"message": "Module updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating module {module_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating module: {str(e)}",
        )


@router.post("/lessons", response_model=dict)
async def create_lesson(
    data: LessonCreate,
    admin_repo: CourseAdminRepository = Depends(get_course_admin_repo),
    current_user: UserResponse = Depends(require_admin),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
):
    """Create a new lesson (admins only)."""
    try:
        result = await admin_repo.create_lesson(data.model_dump())
        logger.info(f"Lesson '{data.id}' created by {current_user.id}")
        await _invalidate_course_caches(cache)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating lesson: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating lesson: {str(e)}",
        )


@router.put("/lessons/{lesson_id}", response_model=dict)
async def update_lesson(
    lesson_id: str,
    data: LessonUpdate,
    admin_repo: CourseAdminRepository = Depends(get_course_admin_repo),
    current_user: UserResponse = Depends(require_admin),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
):
    """Update a lesson (admins only)."""
    try:
        success = await admin_repo.update_lesson(
            lesson_id, data.model_dump(exclude_none=True)
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found"
            )
        logger.info(f"Lesson '{lesson_id}' updated by {current_user.id}")
        await _invalidate_course_caches(cache)
        return {"message": "Lesson updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating lesson {lesson_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating lesson: {str(e)}",
        )


@router.post("/questions", response_model=dict)
async def create_question(
    data: QuestionCreate,
    admin_repo: QuestionAdminRepository = Depends(get_question_admin_repo),
    current_user: UserResponse = Depends(require_admin),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
):
    """Create a new question (admins only)."""
    try:
        result = await admin_repo.create_question(data.model_dump())
        logger.info(f"Question '{data.id}' created by {current_user.id}")
        await _invalidate_question_caches(cache)
        return result
    except Exception as e:
        logger.error(f"Error creating question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating question: {str(e)}",
        )


@router.put("/questions/{question_id}", response_model=dict)
async def update_question(
    question_id: str,
    data: QuestionUpdate,
    admin_repo: QuestionAdminRepository = Depends(get_question_admin_repo),
    current_user: UserResponse = Depends(require_admin),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
):
    """Update a question (admins only)."""
    try:
        success = await admin_repo.update_question(
            question_id, data.model_dump(exclude_none=True)
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Question not found"
            )
        logger.info(f"Question '{question_id}' updated by {current_user.id}")
        await _invalidate_question_caches(cache)
        return {"message": "Question updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating question {question_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating question: {str(e)}",
        )


# Usage Analytics Endpoints
@router.get("/usage", response_model=UsageSummary)
async def get_usage_summary(
    since_days: int = 30,
    usage_repo: UsageRepository = Depends(get_usage_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Aggregate LLM token usage per user over the last N days (admins only)."""
    from datetime import datetime, timedelta, timezone

    try:
        since = datetime.now(timezone.utc) - timedelta(days=since_days)
        rows = await usage_repo.all_user_totals(since=since, limit=1000)
        total_input = sum(r.input_tokens for r in rows)
        total_output = sum(r.output_tokens for r in rows)
        total_calls = sum(r.call_count for r in rows)
        return UsageSummary(
            users=list(rows),
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_calls=total_calls,
        )
    except Exception as e:
        logger.error(f"Error fetching usage summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching usage summary: {str(e)}",
        )


@router.get("/usage/{user_id}", response_model=UserUsageDetail)
async def get_user_usage_detail(
    user_id: str,
    days: int = 30,
    usage_repo: UsageRepository = Depends(get_usage_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Detailed per-user usage: daily counters + recent events (admins only)."""
    from datetime import datetime, timedelta, timezone

    try:
        since_dt = datetime.now(timezone.utc) - timedelta(days=days)
        since_date = since_dt.date()
        daily = await usage_repo.all_daily(user_id, since=since_date, limit=60)
        events = await usage_repo.recent_events(user_id, limit=50)
        totals = await usage_repo.user_totals(user_id, since=since_dt)
        return UserUsageDetail(
            user_id=user_id,
            daily=list(daily),
            events=list(events),
            total_input_tokens=totals.input_tokens,
            total_output_tokens=totals.output_tokens,
        )
    except Exception as e:
        logger.error(f"Error fetching usage detail for {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching usage detail: {str(e)}",
        )


@router.get("/rate-limits", response_model=RateLimitAnalytics)
async def get_rate_limit_analytics(
    since_hours: int = 24,
    usage_repo: UsageRepository = Depends(get_usage_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Admin analytics for rate-limit / abuse events over the last N hours."""
    from datetime import datetime, timedelta, timezone

    try:
        since = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        total = await usage_repo.count_rate_limit_events(since)
        recent = await usage_repo.recent_rate_limit_events(limit=50)
        by_reason = await usage_repo.rate_limit_event_breakdown(since, "reason")
        by_ip = await usage_repo.rate_limit_event_breakdown(since, "ip")
        by_endpoint = await usage_repo.rate_limit_event_breakdown(since, "endpoint")
        return RateLimitAnalytics(
            since_hours=since_hours,
            total_events=total,
            recent_events=list(recent),
            by_reason=list(by_reason),
            by_ip=list(by_ip),
            by_endpoint=list(by_endpoint),
        )
    except Exception as e:
        logger.error(f"Error fetching rate-limit analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching rate-limit analytics: {str(e)}",
        )


@router.get("/abuse", response_model=AbuseReportOut)
async def get_abuse_report(
    since_hours: int = 24,
    usage_repo: UsageRepository = Depends(get_usage_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Admin report of suspicious / abusive rate-limit patterns."""
    from datetime import datetime, timedelta, timezone

    from app.services.abuse_detection import AbuseDetectionService

    try:
        since = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        service = AbuseDetectionService(
            total_events_getter=usage_repo.count_rate_limit_events,
            breakdown_by_ip=lambda s: usage_repo.rate_limit_event_breakdown(s, "ip"),
            breakdown_by_user=lambda s: usage_repo.rate_limit_event_breakdown(
                s, "user_id"
            ),
            recent_events=usage_repo.recent_rate_limit_events,
        )
        report = await service.analyze(since)
        return AbuseReportOut(
            since_hours=since_hours,
            total_events=report.total_events,
            flags=[
                AbuseFlagOut(
                    rule=f.rule,
                    key=f.key,
                    count=f.count,
                    severity=f.severity,
                    detail=f.detail,
                )
                for f in report.flags
            ],
        )
    except Exception as e:
        logger.error(f"Error running abuse detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running abuse detection: {str(e)}",
        )


@router.get("/groq/status")
async def get_groq_status(
    current_user: UserResponse = Depends(require_admin),
):
    """Verify the configured Groq API key and list available models."""
    from app.services.groq_verification import check_groq_status

    try:
        return await check_groq_status()
    except Exception as e:
        logger.error(f"Error checking Groq status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking Groq status: {str(e)}",
        )
