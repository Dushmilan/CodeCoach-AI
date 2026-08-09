"""Database sync tool: copy application data from a local SQL source
(MySQL) to a Supabase/PostgreSQL target.

Design goals:
- Table copy/flush order is foreign-key safe (parents before children).
- JSON columns are normalised to Python objects for Prisma.
- Row counts are validated after the copy; mismatches raise.
- The orchestrator accepts any object implementing ``SyncSource`` /
  ``SyncTarget`` so the copy logic is unit-testable without a live DB.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Protocol

logger = logging.getLogger(__name__)

# FK-safe copy order: parents before children.
TABLE_ORDER: List[str] = [
    "users",
    "courses",
    "questions",
    "modules",
    "lessons",
    "course_progress",
    "user_usage_events",
    "user_daily_usage",
]

# Flush deletes children first.
FLUSH_ORDER: List[str] = list(reversed(TABLE_ORDER))

# Which columns hold JSON per table (MySQL returns them as text).
JSON_COLUMNS: Dict[str, set] = {
    "questions": {
        "company_tags",
        "starter_code",
        "examples",
        "test_cases",
        "hints",
        "constraints",
        "validation_status",
    },
    "course_progress": {"completed_lessons"},
    "feature_flags": {"target_roles"},
    "audit_logs": {"metadata"},
    "generation_jobs": {"result"},
}

# Date columns that must become Python datetimes for Prisma.
DATE_COLUMNS: Dict[str, set] = {
    "user_daily_usage": {"usage_date"},
}

# Columns stored as MySQL int but Boolean in the Prisma schema.
BOOL_COLUMNS: Dict[str, set] = {
    "feature_flags": {"enabled"},
}


def column_names(table: str) -> List[str]:
    """Return the DB column names for a known table (used by tests)."""
    return _TABLES.get(table, [])


_TABLES: Dict[str, List[str]] = {
    "users": [
        "id",
        "username",
        "email",
        "hashed_password",
        "created_at",
        "is_active",
        "oauth_provider",
        "oauth_id",
        "role",
        "plan",
    ],
    "courses": ["id", "title", "description", "language", "icon", "order"],
    "questions": [
        "id",
        "title",
        "difficulty",
        "category",
        "company_tags",
        "description",
        "starter_code",
        "examples",
        "test_cases",
        "hints",
        "solution",
        "time_complexity",
        "space_complexity",
        "constraints",
        "is_interactive",
        "validation_status",
    ],
    "modules": ["id", "course_id", "title", "description", "order"],
    "lessons": [
        "id",
        "course_id",
        "module_id",
        "title",
        "type",
        "content",
        "order",
        "starter_code",
        "test_cases",
        "question_id",
        "language",
    ],
    "course_progress": [
        "id",
        "user_id",
        "course_id",
        "completed_lessons",
        "last_accessed_lesson_id",
        "started_at",
        "last_accessed_at",
    ],
    "user_usage_events": [
        "id",
        "user_id",
        "provider",
        "model",
        "endpoint",
        "input_tokens",
        "output_tokens",
        "created_at",
    ],
    "user_daily_usage": [
        "id",
        "user_id",
        "usage_date",
        "input_tokens",
        "output_tokens",
        "updated_at",
    ],
    "feature_flags": [
        "key",
        "enabled",
        "rollout_pct",
        "target_roles",
        "description",
        "created_at",
        "updated_at",
    ],
    "audit_logs": [
        "id",
        "user_id",
        "action",
        "resource_type",
        "resource_id",
        "metadata",
        "ip_address",
        "user_agent",
        "level",
        "created_at",
    ],
    "generation_jobs": [
        "id",
        "topic",
        "difficulty",
        "count",
        "model",
        "status",
        "result",
        "error",
        "started_at",
        "completed_at",
        "created_by",
        "created_at",
    ],
}


def parse_row(table: str, row: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise a raw source row into a Prisma-friendly payload.

    - JSON columns: parse text back into Python objects.
    - Date columns: convert ``date`` to ``datetime``.
    - Bool columns: convert MySQL int to Python bool.
    """
    out: Dict[str, Any] = {}
    json_cols = JSON_COLUMNS.get(table, set())
    date_cols = DATE_COLUMNS.get(table, set())
    bool_cols = BOOL_COLUMNS.get(table, set())

    for key, value in row.items():
        if key in json_cols and value is not None:
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    logger.warning("Invalid JSON in %s.%s: %r", table, key, value)
        elif (
            key in date_cols
            and isinstance(value, date)
            and not isinstance(value, datetime)
        ):
            value = datetime.combine(value, datetime.min.time())
        elif key in bool_cols:
            value = bool(value)
        out[key] = value
    return out


def validate_counts(
    source_counts: Dict[str, int], target_counts: Dict[str, int]
) -> None:
    """Raise if any table count differs between source and target."""
    for table, expected in source_counts.items():
        actual = target_counts.get(table)
        if actual is None:
            raise RuntimeError(f"Target has no table '{table}' to validate")
        if actual != expected:
            raise RuntimeError(
                f"Row count mismatch for '{table}': source={expected} target={actual}"
            )


class SyncSource(Protocol):
    async def read_all(self, table: str) -> List[Dict[str, Any]]: ...


class SyncTarget(Protocol):
    async def flush(self, table: str) -> None: ...

    async def create_many(self, table: str, rows: List[Dict[str, Any]]) -> int: ...

    async def count(self, table: str) -> int: ...


@dataclass
class SyncReport:
    source_counts: Dict[str, int] = field(default_factory=dict)
    target_counts: Dict[str, int] = field(default_factory=dict)
    flushed: List[str] = field(default_factory=list)


async def run_sync(
    source: SyncSource,
    target: SyncTarget,
    *,
    flush: bool = True,
    confirm: bool = False,
    dry_run: bool = False,
) -> SyncReport:
    """Copy all tables from ``source`` to ``target``.

    - ``flush`` empties target tables (children first) before copying.
    - ``confirm`` must be True when ``flush`` is True (destructive guard).
    - ``dry_run`` reads and reports counts without writing anything.
    """
    if flush and not confirm:
        raise RuntimeError("Refusing to flush target without --confirm")

    report = SyncReport()

    # Read source counts up-front (also used to validate the copy).
    for table in TABLE_ORDER:
        rows = await source.read_all(table)
        report.source_counts[table] = len(rows)

    if dry_run:
        logger.info("Dry run: target not modified.")
        return report

    if flush:
        for table in FLUSH_ORDER:
            await target.flush(table)
            report.flushed.append(table)
        logger.info("Flushed %d target tables.", len(report.flushed))

    for table in TABLE_ORDER:
        rows = await source.read_all(table)
        if rows:
            await target.create_many(table, [parse_row(table, r) for r in rows])

    # Validate counts post-copy.
    for table in TABLE_ORDER:
        report.target_counts[table] = await target.count(table)
    validate_counts(report.source_counts, report.target_counts)
    logger.info("Sync complete: %d tables validated.", len(TABLE_ORDER))
    return report
