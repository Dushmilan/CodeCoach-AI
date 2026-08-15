#!/usr/bin/env python3
"""One-time bootstrap: sync local question + curriculum JSON into the database.

Reads ``questions/sample_questions.json`` and ``data/courses/**`` and upserts
them into the connected database. Idempotent and non-destructive: rows that
are missing are inserted, rows that already exist are updated, and no existing
database data is deleted.

Usage:
    python scripts/sync_local_to_db.py [--url DATABASE_URL]

Defaults to DATABASE_URL from the environment (PostgreSQL/Supabase, or local
MySQL if configured). Safe to re-run.
"""

import argparse
import asyncio
import os
import sys
import urllib.parse
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

load_dotenv(find_dotenv())

from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.services.local_sync import sync  # noqa: E402


def _strip_pgbouncer(url: str) -> str:
    """Drop the Supabase transaction-pooler `?pgbouncer=true` param.

    asyncpg would otherwise forward `pgbouncer` as an unknown connection kwarg.
    """
    if "pgbouncer" not in url:
        return url
    scheme, netloc, path, query, fragment = urllib.parse.urlsplit(url)
    params = [
        kv
        for kv in (query.split("&") if query else [])
        if not kv.startswith("pgbouncer")
    ]
    return urllib.parse.urlunsplit((scheme, netloc, path, "&".join(params), fragment))


def _get_database_url() -> str:
    url = _strip_pgbouncer(os.getenv("DATABASE_URL"))
    if not url:
        raise SystemExit(
            "ERROR: DATABASE_URL is required (Supabase/PostgreSQL connection "
            "string); no local fallback is allowed."
        )
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def _redact(url: str) -> str:
    """Mask the password component of a database URL for logging."""
    try:
        parsed = urllib.parse.urlsplit(url)
        netloc = parsed.hostname or ""
        if parsed.username:
            netloc = f"{parsed.username}:***@{netloc}"
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        return urllib.parse.urlunsplit(
            (parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment)
        )
    except ValueError:
        return "<redacted>"


async def main(database_url: str) -> int:
    base_dir = Path(__file__).resolve().parent.parent
    questions_path = base_dir / "questions" / "sample_questions.json"
    courses_dir = base_dir / "data" / "courses"

    print(f"Syncing local content into: {_redact(database_url)}")
    print(f"  Question bank: {questions_path}")
    print(f"  Curriculum:    {courses_dir}")
    print()

    engine_kwargs = {}
    # Supabase pgbouncer poolers reuse prepared-statement names across
    # connections; disable asyncpg's statement cache so DDL / DML does not hit
    # DuplicatePreparedStatementError.
    if database_url.startswith("postgresql"):
        engine_kwargs["connect_args"] = {"statement_cache_size": 0}

    engine = create_async_engine(database_url, echo=False, **engine_kwargs)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        report = await sync(session, questions_path, courses_dir)
        await session.commit()
    await engine.dispose()

    print("Sync complete.")
    print("  " + report.summary())
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sync local question/curriculum JSON into the database"
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="Database URL (overrides DATABASE_URL env var)",
    )
    args = parser.parse_args()

    if args.url:
        os.environ["DATABASE_URL"] = args.url

    sys.exit(asyncio.run(main(_get_database_url())))
