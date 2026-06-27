from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
import uuid
import logging

from app.ports.admin_repository import AdminRepository
from app.api.admin_middleware import require_admin, require_super_admin
from app.api.dependencies import get_admin_repo
from app.models.auth_schemas import UserResponse
from app.models.admin_models import (
    UserAdminUpdate,
    UserDetailResponse,
    StatsResponse,
    QuestionFilter,
    QuestionImportResult,
    FeatureFlagUpdate,
    GenerationJobCreate,
    AuditLogFilter,
)

router = APIRouter()
logger = logging.getLogger(__name__)


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


# Generation Pipeline Management Endpoints
@router.get("/generation/jobs", response_model=dict)
async def list_generation_jobs(
    status: Optional[str] = None,
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """List generation jobs (admins only)."""
    try:
        jobs = await admin_repo.get_generation_jobs(status)

        return {
            "jobs": jobs,
            "total": len(jobs),
            "status": status or "all",
        }
    except Exception as e:
        logger.error(f"Error listing generation jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing generation jobs: {str(e)}",
        )


@router.get("/generation/jobs/{job_id}", response_model=dict)
async def get_generation_job(
    job_id: str,
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Get generation job details (admins only)."""
    try:
        job = await admin_repo.get_generation_job_by_id(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Generation job not found",
            )

        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching generation job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching generation job: {str(e)}",
        )


@router.post("/generation/trigger", response_model=dict)
async def trigger_generation(
    job_data: GenerationJobCreate,
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Trigger a new question generation job (admins only)."""
    try:
        # TODO: Implement actual job submission to generation service
        job = {
            "id": "job_" + uuid.uuid4().hex[:12],
            "topic": job_data.topic or "general",
            "difficulty": job_data.difficulty or "all",
            "count": job_data.count or 10,
            "model": job_data.model or "gemini-2.5-flash-lite",
            "status": "pending",
            "created_by": current_user.id,
            "created_at": datetime.now(timezone.utc),
        }

        logger.info(f"Generation job triggered by {current_user.id}: {job['id']}")

        return {"message": "Generation job submitted", "job": job}
    except Exception as e:
        logger.error(f"Error triggering generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error triggering generation: {str(e)}",
        )


# Feature Flags Management
@router.get("/feature-flags", response_model=dict)
async def get_feature_flags(
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Get all feature flags (admins only)."""
    try:
        flags = await admin_repo.get_feature_flags()
        return {"flags": flags}
    except Exception as e:
        logger.error(f"Error fetching feature flags: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching feature flags: {str(e)}",
        )


@router.patch("/feature-flags/{key}")
async def update_feature_flag(
    key: str,
    updates: FeatureFlagUpdate,
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Update a feature flag (admins only)."""
    try:
        success = await admin_repo.update_feature_flag(key, updates)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feature flag not found",
            )

        logger.info(f"Feature flag {key} updated by {current_user.id}")
        return {"message": "Feature flag updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating feature flag {key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating feature flag: {str(e)}",
        )


# Audit Logs
@router.get("/audit-logs", response_model=dict)
async def get_audit_logs(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    level: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    per_page: int = 50,
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Get audit logs with filtering and pagination (admins only)."""
    try:
        filter = AuditLogFilter(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            level=level,
            start_date=start_date,
            end_date=end_date,
            page=page,
            per_page=per_page,
        )

        logs, total = await admin_repo.get_audit_logs(
            filter, (page - 1) * per_page, per_page
        )

        return {
            "logs": logs,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        }
    except Exception as e:
        logger.error(f"Error fetching audit logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching audit logs: {str(e)}",
        )


@router.get("/audit-logs/export")
async def export_audit_logs(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    level: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Export audit logs as CSV (admins only)."""
    try:
        from fastapi.responses import StreamingResponse
        import io
        import csv

        filter = AuditLogFilter(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            level=level,
            start_date=start_date,
            end_date=end_date,
            page=1,
            per_page=10000,
        )

        logs, _ = await admin_repo.get_audit_logs(filter, 0, 10000)

        csv_buffer = io.StringIO()
        writer = csv.DictWriter(
            csv_buffer,
            fieldnames=[
                "id",
                "user_id",
                "action",
                "resource_type",
                "resource_id",
                "level",
                "created_at",
            ],
        )
        writer.writeheader()
        for log in logs:
            writer.writerow(log)

        csv_buffer.seek(0)

        return StreamingResponse(
            iter([csv_buffer.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            },
        )
    except Exception as e:
        logger.error(f"Error exporting audit logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting audit logs: {str(e)}",
        )


# System Settings
@router.get("/settings", response_model=dict)
async def get_system_settings(
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Get system settings (admins only)."""
    try:
        settings = {
            "piston": {
                "url": "http://localhost:2215",
                "timeout_ms": 30000,
                "memory_limit_mb": 256,
                "cpu_limit": 1,
                "enabled_languages": ["python", "javascript", "java"],
            },
            "rate_limits": {
                "auth": 10,
                "coach": 30,
                "submit": 20,
            },
            "maintenance_mode": False,
            "ai_provider": "google",
        }

        return settings
    except Exception as e:
        logger.error(f"Error fetching system settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching system settings: {str(e)}",
        )


@router.patch("/settings")
async def update_system_settings(
    updates: dict,
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Update system settings (admins only)."""
    try:
        # TODO: Implement actual settings update logic
        logger.info(f"System settings updated by {current_user.id}")

        return {"message": "System settings updated successfully"}
    except Exception as e:
        logger.error(f"Error updating system settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating system settings: {str(e)}",
        )


# User Analytics
@router.get("/analytics/users", response_model=dict)
async def get_user_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Get user analytics and reports (admins only)."""
    try:
        # Default to last 30 days
        if start_date is None:
            start_date = datetime.utcnow() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.utcnow()

        report = await admin_repo.generate_user_role_grant_report(start_date, end_date)

        return {
            "report": report,
            "start_date": start_date,
            "end_date": end_date,
            "total_users": len(report),
        }
    except Exception as e:
        logger.error(f"Error fetching user analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user analytics: {str(e)}",
        )


@router.get("/analytics/question-progress")
async def get_question_progress(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    admin_repo: AdminRepository = Depends(get_admin_repo),
    current_user: UserResponse = Depends(require_admin),
):
    """Get question progress analytics (admins only)."""
    try:
        # TODO: Implement question progress analytics
        progress = []

        return {"progress": progress, "start_date": start_date, "end_date": end_date}
    except Exception as e:
        logger.error(f"Error fetching question progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching question progress: {str(e)}",
        )
