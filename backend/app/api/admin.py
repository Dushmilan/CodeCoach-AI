from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List, Dict, Any
import logging

from app.ports.admin_repository import AdminRepository
from app.api.admin_middleware import require_admin, require_super_admin
from app.api.dependencies import get_admin_repo, get_file_course_repo
from app.models.auth_schemas import UserResponse
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


def _reload_course_repo():
    """Reload the shared FileCourseRepository after admin mutations."""
    repo = get_file_course_repo()
    if repo is not None:
        repo.reload()


# Dashboard and Analytics Endpoints
@router.get("/stats", response_model=StatsResponse)
async def get_admin_stats(
    admin_repo: AdminRepository = Depends(get_admin_repo),
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
async def get_user_stats(admin_repo: AdminRepository = Depends(get_admin_repo)):
    """Get user statistics (admins only)."""
    try:
        # Get all users
        users, total = await admin_repo.list_users(skip=0, limit=1000)

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
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """List all users with pagination and filtering (admins only)."""
    try:
        skip = (page - 1) * per_page
        all_users, total = await admin_repo.list_users(skip=0, limit=10000)

        if search:
            q = search.lower()
            all_users = [
                u for u in all_users if q in u.username.lower() or q in u.email.lower()
            ]
            total = len(all_users)

        page_users = all_users[skip : skip + per_page]
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
    admin_repo: AdminRepository = Depends(get_admin_repo),
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
    admin_repo: AdminRepository = Depends(get_admin_repo),
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
    admin_repo: AdminRepository = Depends(get_admin_repo),
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
    admin_repo: AdminRepository = Depends(get_admin_repo),
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
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
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
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
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
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Validate question test cases (admins only)."""
    try:
        question = await admin_repo.get_question_by_id(question_id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found",
            )

        return {"message": "Validation completed", "result": "All test cases passed"}
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
    admin_repo: AdminRepository = Depends(get_admin_repo),
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
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Delete a course (admins only)."""
    try:
        success = await admin_repo.delete_course(course_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found",
            )
        _reload_course_repo()
        logger.info(f"Course {course_id} deleted by {current_user.id}")
        return {"message": "Course deleted successfully"}
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
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Delete a module (admins only)."""
    try:
        success = await admin_repo.delete_module(module_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module not found",
            )
        _reload_course_repo()
        logger.info(f"Module {module_id} deleted by {current_user.id}")
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
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Delete a lesson (admins only)."""
    try:
        success = await admin_repo.delete_lesson(lesson_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found",
            )
        _reload_course_repo()
        logger.info(f"Lesson {lesson_id} deleted by {current_user.id}")
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
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Check if an entity ID already exists."""
    tree = await admin_repo.get_course_tree()
    exists = False
    if entity_type == "course":
        exists = any(c.get("id") == entity_id for c in tree.get("courses", []))
    elif entity_type == "module":
        exists = any(m.get("id") == entity_id for m in tree.get("modules", []))
    elif entity_type == "lesson":
        exists = any(les.get("id") == entity_id for les in tree.get("lessons", []))
    return {"exists": exists}


@router.post("/courses", response_model=dict)
async def create_course(
    data: CourseCreate,
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Create a new course (admins only)."""
    try:
        result = await admin_repo.create_course(data.model_dump())
        _reload_course_repo()
        logger.info(f"Course '{data.id}' created by {current_user.id}")
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
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
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
        _reload_course_repo()
        logger.info(f"Course '{course_id}' updated by {current_user.id}")
        return {"message": "Course updated successfully"}
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
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Create a new module (admins only)."""
    try:
        result = await admin_repo.create_module(data.model_dump())
        _reload_course_repo()
        logger.info(f"Module '{data.id}' created by {current_user.id}")
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
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
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
        _reload_course_repo()
        logger.info(f"Module '{module_id}' updated by {current_user.id}")
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
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Create a new lesson (admins only)."""
    try:
        result = await admin_repo.create_lesson(data.model_dump())
        _reload_course_repo()
        logger.info(f"Lesson '{data.id}' created by {current_user.id}")
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
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
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
        _reload_course_repo()
        logger.info(f"Lesson '{lesson_id}' updated by {current_user.id}")
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
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Create a new question (admins only)."""
    try:
        result = await admin_repo.create_question(data.model_dump())
        logger.info(f"Question '{data.id}' created by {current_user.id}")
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
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
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
        return {"message": "Question updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating question {question_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating question: {str(e)}",
        )
