from fastapi import APIRouter, Depends, Request
from datetime import datetime, timedelta, timezone
import asyncio
import logging
import os
from sqlalchemy import text

from app.api.dependencies import get_usage_repo
from app.core.database import async_session_maker, get_db
from app.ports.usage_repository import UsageRepository

router = APIRouter()
logger = logging.getLogger(__name__)

_DB_PROBE_TIMEOUT_S = 1.0


async def db_reachable(timeout: float = _DB_PROBE_TIMEOUT_S) -> str:
    """Probe the database with a bounded timeout.

    Returns "ok" when the database answers `SELECT 1`, otherwise
    "unavailable" — the endpoint never fails hard on a DB outage so it can
    report the truth while staying up itself.
    """
    try:
        async with asyncio.timeout(timeout):
            async with async_session_maker() as session:
                await session.execute(text("SELECT 1"))
        return "ok"
    except asyncio.CancelledError:
        # Cancellation (e.g. the probe's own deadline or the client task being
        # torn down) means we could not confirm the DB; report it truthfully
        # instead of surfacing a 500. CancelledError is a BaseException, so a
        # bare `except Exception` would let it escape.
        logger.debug("Health DB probe cancelled")
        return "unavailable"
    except Exception as exc:  # noqa: BLE001 - any probe failure means unreachable
        # A failing DB is expected while an outage lasts (the healthcheck runs
        # every 30s), so log the cause at debug and a one-line warning — no
        # traceback spam.
        logger.debug("Health DB probe failed", exc_info=True)
        logger.warning("Health DB probe failed: %s", exc)
        return "unavailable"


@router.get("/")
async def health_check(request: Request):
    rate_limiting_enabled = hasattr(request.app.state, "limiter")
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "features": {
            "ai_coaching": "enabled",
            "code_execution": "enabled",
            "questions_api": "enabled",
            "rate_limiting": "enabled" if rate_limiting_enabled else "disabled",
        },
        "dependencies": {
            "groq": "configured" if os.getenv("GROQ_API_KEY") else "not_configured",
            "piston_api": "configured",
            "questions_db": await db_reachable(),
        },
    }


@router.get("/monitoring")
async def monitoring_check(
    request: Request,
    db=Depends(get_db),
    usage_repo: UsageRepository = Depends(get_usage_repo),
):
    """Deep health + abuse-posture snapshot for uptime dashboards.

    Runs lightweight probes against Redis and the database, plus the abuse
    detector over the last 24h of rate-limit events. `healthy` is false when
    a dependency is unreachable or a high-severity abuse flag is present.
    """
    from app.services.abuse_detection import AbuseDetectionService
    from app.services.monitoring import MonitoringService

    cache = getattr(request.app.state, "redis_cache", None)
    monitoring = MonitoringService(redis_cache=cache)
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    service = AbuseDetectionService(
        total_events_getter=usage_repo.count_rate_limit_events,
        breakdown_by_ip=lambda s: usage_repo.rate_limit_event_breakdown(s, "ip"),
        breakdown_by_user=lambda s: usage_repo.rate_limit_event_breakdown(s, "user_id"),
        recent_events=usage_repo.recent_rate_limit_events,
    )
    report = await service.analyze(since)
    snapshot = await monitoring.render(db_session=db, abuse_report=report)

    # Fire alert webhook (no-op unless ALERT_WEBHOOK_URL configured).
    from app.services.monitoring import AlertService

    alert_fired = await AlertService().alert_abuse(report)

    return {
        "status": "ok" if snapshot.healthy else "degraded",
        "timestamp": snapshot.timestamp,
        "healthy": snapshot.healthy,
        "dependencies": [
            {"name": d.name, "ok": d.ok, "detail": d.detail}
            for d in snapshot.dependencies
        ],
        "abuse": {
            "flags": snapshot.abuse_flag_count,
            "severity": snapshot.abuse_severity_max,
        },
        "alert_fired": alert_fired,
    }
