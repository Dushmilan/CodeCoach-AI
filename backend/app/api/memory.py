"""Memory graph endpoint — forgetting-curve dashboard (Idea #3)."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth_deps import get_current_user
from app.api.dependencies import get_memory_graph_service
from app.models.auth_schemas import UserResponse
from app.models.memory_schemas import MemoryGraphResponse
from app.services.memory_graph_service import MemoryGraphService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/graph", response_model=MemoryGraphResponse)
async def get_memory_graph(
    current_user: UserResponse = Depends(get_current_user),
    service: MemoryGraphService = Depends(get_memory_graph_service),
) -> MemoryGraphResponse:
    """Return the user's forgetting-curve memory graph."""
    try:
        return await service.graph(
            user_id=current_user.id, now=datetime.now(timezone.utc)
        )
    except Exception:
        logger.exception("Failed to build memory graph for user %s", current_user.id)
        raise HTTPException(status_code=500, detail="Failed to build memory graph")
