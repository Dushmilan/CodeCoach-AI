"""Database sync adapters.

- :class:`MySQLSyncSource` reads rows from the local MySQL database.
- :class:`PrismaSyncTarget` writes rows to Supabase/PostgreSQL via Prisma.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from prisma import Prisma, fields

from app.services.database_sync import JSON_COLUMNS, SyncSource, SyncTarget, column_names

logger = logging.getLogger(__name__)

# Prisma client model attribute per table name.
_TABLE_MODEL = {
    "users": "user",
    "courses": "course",
    "questions": "question",
    "modules": "module",
    "lessons": "lesson",
    "course_progress": "courseprogress",
    "user_usage_events": "userusageevent",
    "user_daily_usage": "userdailyusage",
    "feature_flags": "featureflag",
    "audit_logs": "auditlog",
    "generation_jobs": "generationjob",
}


def prisma_model(client: Prisma, table: str):
    attr = _TABLE_MODEL[table]
    return getattr(client, attr)


class MySQLSyncSource(SyncSource):
    def __init__(self, url: str):
        self.url = url

    async def connect(self):
        import aiomysql
        from urllib.parse import urlparse

        parsed = urlparse(self.url.replace("mysql+aiomysql://", "mysql://"))
        self._conn = await aiomysql.connect(
            host=parsed.hostname,
            port=parsed.port or 3306,
            user=parsed.username,
            password=parsed.password,
            db=parsed.path.lstrip("/") or None,
            autocommit=True,
            cursorclass=aiomysql.cursors.DictCursor,
        )

    async def close(self):
        if hasattr(self, "_conn") and self._conn:
            self._conn.close()

    async def read_all(self, table: str) -> List[Dict[str, Any]]:
        cur = await self._conn.cursor()
        try:
            await cur.execute(f"SELECT * FROM `{table}`")
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            await cur.close()


def build_prisma(target_url: str) -> Prisma:
    """Build a Prisma client pinned to the given Supabase/PostgreSQL URL.

    The datasource override decouples the sync tool from the app's runtime
    ``DATABASE_URL`` (which tests may repoint at a throwaway database).
    """
    from prisma._types import DatasourceOverride

    return Prisma(datasource=DatasourceOverride(url=target_url))


class PrismaSyncTarget(SyncTarget):
    def __init__(self, client: Prisma):
        self.client = client

    async def flush(self, table: str) -> None:
        model = prisma_model(self.client, table)
        await model.delete_many()

    async def create_many(self, table: str, rows: List[Dict[str, Any]]) -> int:
        model = prisma_model(self.client, table)
        cols = column_names(table)
        json_cols = JSON_COLUMNS.get(table, set())
        data = []
        for row in rows:
            item = {k: row[k] for k in cols if k in row}
            for col in json_cols:
                if col in item and item[col] is not None:
                    item[col] = fields.Json(item[col])
                elif col in item:
                    # Nullable Json columns must be omitted (prisma-client-py
                    # rejects explicit None for Json fields).
                    del item[col]
            data.append(item)
        if not data:
            return 0
        return await model.create_many(data=data)

    async def count(self, table: str) -> int:
        model = prisma_model(self.client, table)
        return await model.count()
