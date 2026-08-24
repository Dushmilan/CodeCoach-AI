"""Mistake-memory endpoints (per-user error graph)."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth_deps import get_current_user
from app.api.dependencies import get_error_graph_service
from app.models.auth_schemas import UserResponse
from app.models.mistake_schemas import ErrorGraphResponse
from app.services.error_graph_service import ErrorGraphService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/graph", response_model=ErrorGraphResponse)
async def get_my_mistake_graph(
    current_user: UserResponse = Depends(get_current_user),
    service: ErrorGraphService = Depends(get_error_graph_service),
):
    """Return the authenticated user's error graph, most recurring first."""
    try:
        return await service.graph(user_id=current_user.id)
    except Exception:
        logger.exception("Failed to derive mistake graph for user %s", current_user.id)
        raise HTTPException(status_code=500, detail="Failed to derive mistake graph")
