"""Per-plan daily request limit enforcement.

`enforce_daily_request_cap` is a FastAPI dependency (middleware for the coach
routes) that reserves a request slot against the user's daily quota using an
atomic Redis counter (DailyLimitService). On denial it returns 429 with
standard X-RateLimit-* headers and records a rate-limit event for analytics
and abuse detection.

The dependency is applied to the AI endpoints in `app/api/coach.py`; it is
deliberately not a raw ASGI middleware because resolving the authenticated
user (JWT) is cleaner through FastAPI dependencies.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.auth_deps import get_current_user
from app.api.dependencies import get_redis_cache, get_usage_repo
from app.models.auth_schemas import UserResponse
from app.ports.usage_repository import UsageRepository
from app.services.daily_limit_service import DailyLimitService
from app.services.redis_service import RedisCache

logger = logging.getLogger(__name__)

router = APIRouter()


def cap_for_plan(plan: str) -> int:
    """Return the daily request cap for a user plan (paid plans get a high cap).

    Premium (the paywalled coach tier from PR #89) is treated as paid, so it
    bypasses the free daily cap in practice: the guard only becomes a
    secondary safety net against runaway usage for paid users.
    """
    from app.core.config import get_settings

    settings = get_settings()
    if plan in ("pro", "premium"):
        return settings.PRO_DAILY_REQUEST_CAP
    return settings.FREE_DAILY_REQUEST_CAP


def _reset_at(now: datetime) -> datetime:
    return (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


def daily_limit_headers(
    cap: int, remaining: int, plan: str, now: Optional[datetime] = None
) -> dict:
    """Build X-RateLimit-* headers plus request-remaining usage header."""
    now = now or datetime.now(timezone.utc)
    reset = _reset_at(now)
    return {
        "X-RateLimit-Limit": str(cap),
        "X-RateLimit-Remaining": str(max(0, remaining)),
        "X-RateLimit-Reset": str(int(reset.timestamp())),
        "X-RateLimit-Policy": plan,
        "X-Usage-Remaining-Requests": str(max(0, remaining)),
    }


async def enforce_daily_request_cap(
    request: Request,
    user: UserResponse = Depends(get_current_user),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
    usage_repo: UsageRepository = Depends(get_usage_repo),
) -> None:
    """Reserve one daily request slot; raise 429 when the plan cap is hit."""
    cap = cap_for_plan(user.plan)
    service = DailyLimitService(cache=cache, repo=usage_repo)
    allowed, remaining = await service.consume(user.id, cap)
    request.state.daily_limit_headers = daily_limit_headers(cap, remaining, user.plan)
    if not allowed:
        await _record_denial(usage_repo, request, user, "daily_cap")
        headers = dict(request.state.daily_limit_headers)
        now = datetime.now(timezone.utc)
        headers["Retry-After"] = str(max(1, int((_reset_at(now) - now).total_seconds())))
        raise HTTPException(status_code=429, detail="Daily request limit reached", headers=headers)


async def _record_denial(
    usage_repo: UsageRepository, request: Request, user: UserResponse, reason: str
) -> None:
    """Best-effort persistence of a denial; never fails the request."""
    try:
        await usage_repo.add_rate_limit_event(
            user_id=user.id,
            ip=request.client.host if request.client else "unknown",
            reason=reason,
            endpoint=request.url.path,
        )
    except Exception:
        logger.debug("Failed to record rate limit event", exc_info=True)


@router.get("")
async def get_usage(
    request: Request,
    user: UserResponse = Depends(get_current_user),
    cache: Optional[RedisCache] = Depends(get_redis_cache),
    usage_repo: UsageRepository = Depends(get_usage_repo),
) -> dict:
    """Return the authenticated user's current plan usage and daily quota."""
    cap = cap_for_plan(user.plan)
    service = DailyLimitService(cache=cache, repo=usage_repo)
    now = datetime.now(timezone.utc)
    remaining = await service.remaining(user.id, cap, now=now)
    return {
        "plan": user.plan,
        "daily_limit": cap,
        "daily_used": max(0, cap - remaining),
        "daily_remaining": remaining,
        "reset_at": _reset_at(now).isoformat(),
    }
