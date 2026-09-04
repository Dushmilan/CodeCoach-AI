"""Lightweight operational monitoring and alerting.

- `MonitoringService` probes dependencies (Redis, DB session) and the abuse
  posture, rendering a snapshot for `/health/monitoring`.
- `AlertService` fires a webhook when high-severity abuse flags are present;
  it is a no-op unless `ALERT_WEBHOOK_URL` is configured, keeping the default
  deployment self-contained (no external dependencies).
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx
from sqlalchemy import text

logger = logging.getLogger(__name__)

ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", "")
ALERT_SEVERITY_MIN = os.getenv("ALERT_MIN_SEVERITY", "high")


@dataclass
class DependencyStatus:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class MonitoringReport:
    healthy: bool
    timestamp: str
    dependencies: list[DependencyStatus] = field(default_factory=list)
    abuse_flag_count: int = 0
    abuse_severity_max: str = "none"


class MonitoringService:
    def __init__(self, redis_cache=None):
        self._redis = redis_cache

    async def probe_redis(self) -> DependencyStatus:
        if self._redis is None:
            return DependencyStatus(name="redis", ok=False, detail="disabled")
        try:
            if getattr(self._redis, "_enabled", True) is False:
                return DependencyStatus(name="redis", ok=False, detail="disabled")
            # Round-trip through the cache — exercises pool + connectivity.
            await self._redis.get("__monitor_probe__")
            return DependencyStatus(name="redis", ok=True, detail="ok")
        except Exception as e:  # pragma: no cover - defensive
            return DependencyStatus(name="redis", ok=False, detail=str(e))

    async def probe_db(self, session) -> DependencyStatus:
        try:
            await session.execute(text("SELECT 1"))
            return DependencyStatus(name="database", ok=True, detail="ok")
        except Exception as e:
            logger.warning("Monitoring DB probe failed: %s", e)
            return DependencyStatus(name="database", ok=False, detail=str(e))

    async def render(
        self, *, db_session=None, abuse_report=None, since_hours: int = 24
    ) -> MonitoringReport:
        deps = [await self.probe_redis()]
        if db_session is not None:
            deps.append(await self.probe_db(db_session))
        else:
            deps.append(
                DependencyStatus(name="database", ok=False, detail="no session")
            )

        flags = list(abuse_report.flags) if abuse_report else []
        severity_order = {"none": 0, "warning": 1, "high": 2}
        max_sev = "none"
        for f in flags:
            if severity_order.get(f.severity, 0) > severity_order.get(max_sev, 0):
                max_sev = f.severity

        healthy = all(d.ok for d in deps) and max_sev != "high"
        return MonitoringReport(
            healthy=healthy,
            timestamp=datetime.now(timezone.utc).isoformat() + "Z",
            dependencies=deps,
            abuse_flag_count=len(flags),
            abuse_severity_max=max_sev,
        )


def min_severity_threshold() -> int:
    return {"none": 0, "warning": 1, "high": 2}.get(ALERT_SEVERITY_MIN, 2)


class AlertService:
    """Fire a webhook when high-severity abuse flags appear (no-op if unset)."""

    def __init__(self, webhook_url: str = ALERT_WEBHOOK_URL):
        self.webhook_url = webhook_url

    @property
    def configured(self) -> bool:
        return bool(self.webhook_url)

    async def alert_abuse(self, report) -> bool:
        """POST an alert to the webhook if any flag meets the severity bar.

        Returns True only when a webhook was actually called; false for
        no-op cases (no URL, nothing to report, or suppressed). Never raises.
        """
        threshold = min_severity_threshold()
        flags = [f for f in report.flags if severity_value(f.severity) >= threshold]
        if not self.configured or not flags:
            return False
        payload = {
            "event": "rate_limit_abuse",
            "severity": max((severity_value(f.severity) for f in flags), default=0),
            "flag_details": [
                {"rule": f.rule, "key": f.key, "count": f.count, "detail": f.detail}
                for f in report.flags
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.post(self.webhook_url, json=payload)
                resp.raise_for_status()
            logger.info(
                "Abuse alert sent to %s (%d flags)", self.webhook_url, len(flags)
            )
            return True
        except Exception as e:
            logger.warning("Failed to send abuse alert: %s", e)
            return False


def severity_value(sev: str) -> int:
    return {"none": 0, "warning": 1, "high": 2}.get(sev, 0)
