"""Learning-analytics signals (Ideas #1 residual) — read-only plateau detection."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.api.auth_deps import get_current_user
from app.api.dependencies import get_analytics_service
from app.models.analytics_schemas import AnalyticsSignalsResponse
from app.models.auth_schemas import UserResponse
from app.services.learning_analytics_service import LearningAnalyticsService

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/signals", response_model=AnalyticsSignalsResponse)
async def get_signals(
    service: LearningAnalyticsService = Depends(get_analytics_service),
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        return await service.signals(
            user_id=current_user.id, now=datetime.now(timezone.utc)
        )
    except Exception:
        logger.exception(
            "Failed to derive analytics signals for user %s", current_user.id
        )
        return AnalyticsSignalsResponse(signals=[], total=0)
