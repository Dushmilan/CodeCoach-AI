"""Attempt-history endpoints (submissions)."""

from fastapi import APIRouter, Depends, HTTPException, Query
import logging

from app.api.auth_deps import get_current_user
from app.api.dependencies import get_submission_repo
from app.models.auth_schemas import UserResponse
from app.models.submission_schemas import SubmissionsListResponse
from app.ports.submission_repository import SubmissionRepository

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me", response_model=SubmissionsListResponse)
async def get_my_submissions(
    limit: int = Query(50, ge=1, le=200, description="Max attempts to return"),
    current_user: UserResponse = Depends(get_current_user),
    submissions: SubmissionRepository = Depends(get_submission_repo),
):
    """Return the authenticated user's recent graded attempts, newest first."""
    try:
        items = await submissions.list_by_user(current_user.id, limit=limit)
        return SubmissionsListResponse(
            submissions=list(items),
            total=len(items),
        )
    except Exception:
        logger.exception("Failed to list submissions for user %s", current_user.id)
        raise HTTPException(status_code=500, detail="Failed to list submissions")
