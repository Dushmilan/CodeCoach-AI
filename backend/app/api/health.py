from fastapi import APIRouter, Depends, Request
from datetime import datetime, timedelta, timezone
import os

from app.api.dependencies import get_usage_repo
from app.core.database import get_db
from app.ports.usage_repository import UsageRepository

router = APIRouter()


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
            "questions_db": "loaded",
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
        breakdown_by_user=lambda s: usage_repo.rate_limit_event_breakdown(
            s, "user_id"
        ),
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