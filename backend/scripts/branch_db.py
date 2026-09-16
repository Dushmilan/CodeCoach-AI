#!/usr/bin/env python3
"""Per-branch temporary databases with versioned promotion to live (#168).

Working data lives in a local PostgreSQL server. Every git branch gets its
own database (``codecoach_<slug>``) as a scratch workspace: implementation is
tested there first, then promoted to the live database through
version-controlled migrations + this script's upsert-only copy.

Fail-safe direction gates (no flag can override the wrong direction):
- ``pull`` (live -> local) REFUSES any destination that is not localhost.
- ``promote`` (local -> live) REFUSES localhost targets AND requires
  ``PROMOTE_TO_LIVE=YES-I-AM-SURE``.

Every write is ``merge()`` (select-then-insert/update), so re-runs and
re-promotions change nothing. Schema for fresh branch DBs comes from the ORM
``Base.metadata`` (single source of truth); live schema moves via alembic.

Usage:
    python scripts/branch_db.py init --url <LOCAL_URL>
    python scripts/branch_db.py pull --from <LIVE_URL> --to <LOCAL_URL>
    python scripts/branch_db.py status --url <LOCAL_URL>
    PROMOTE_TO_LIVE=YES-I-AM-SURE python scripts/branch_db.py promote \\
        --from <LOCAL_URL> --to <LIVE_URL>
"""

import argparse
import asyncio
import hashlib
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bcrypt
from sqlalchemy import func, select
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.models.orm import (
    Base,
    CourseORM,
    LessonORM,
    ModuleORM,
    QuestionORM,
    UserORM,
)

# Tables copied live -> local -> live, in FK-safe order: courses before
# modules/lessons (course_id), questions before lessons (question_id),
# modules before lessons (module_id). Courses carry nullable owner_id
# (SET NULL), so no users need to travel with the curriculum.
COPY_TABLES = ["courses", "questions", "modules", "lessons"]

TABLE_MODELS = {
    "questions": QuestionORM,
    "courses": CourseORM,
    "modules": ModuleORM,
    "lessons": LessonORM,
}

PROMOTE_CONFIRM_TOKEN = "YES-I-AM-SURE"
PROMOTE_CONFIRM_ENV = "PROMOTE_TO_LIVE"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}

_BRANCH_TYPE_PREFIXES = {"feat", "fix", "chore", "docs", "refactor", "test"}


def branch_db_name(branch: str) -> str:
    """Derive a safe Postgres database name from a git branch name.

    ``chore/168-local-postgres-branch-db`` -> ``codecoach_168_local_...``.
    Always prefixed, charset-safe, and capped at the 63-char identifier
    limit (long slugs truncate deterministically with a hash suffix).
    """
    parts = re.split(r"[^a-z0-9]+", branch.lower())
    parts = [p for p in parts if p]
    if parts and parts[0] in _BRANCH_TYPE_PREFIXES:
        parts = parts[1:]
    stem = "_".join(parts) or "default"
    name = f"codecoach_{stem}"
    if len(name) > 63:
        digest = hashlib.sha1(branch.encode("utf-8")).hexdigest()[:8]
        name = f"{name[: 63 - 9]}_{digest}"
    return name


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def pull_allowed(dest_url: str) -> bool:
    """Pull may only write to a local database — never back to live."""
    return _host(dest_url) in LOCAL_HOSTS


def promote_allowed(live_url: str, confirm_token: str | None) -> bool:
    """Promote needs the explicit confirm token AND a non-local target."""
    return confirm_token == PROMOTE_CONFIRM_TOKEN and _host(live_url) not in LOCAL_HOSTS


def _redact(url: str) -> str:
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "?"
        path = parsed.path or ""
        return f"{parsed.scheme}://{host}{path}"
    except Exception:
        return "<unparseable-url>"


def _to_async(url: str) -> str:
    url = url.split("?pgbouncer=true")[0].rstrip("?&")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def _engine(url: str):
    return create_async_engine(
        _to_async(url),
        poolclass=NullPool,
        pool_pre_ping=True,
        connect_args={"statement_cache_size": 0},
    )


async def init_db(db_url: str) -> str:
    """CREATE DATABASE (if missing) + create ORM schema. Idempotent."""
    parsed = urlparse(db_url)
    db_name = parsed.path.lstrip("/")
    maint_url = f"{parsed.scheme}://{parsed.netloc}/postgres"
    engine = _engine(maint_url)
    async with engine.connect() as conn:
        await conn.execution_options(isolation_level="AUTOCOMMIT")
        try:
            await conn.exec_driver_sql(f'CREATE DATABASE "{db_name}"')
        except ProgrammingError as exc:
            if "already exists" not in str(exc.orig):
                raise
    await engine.dispose()

    schema_engine = _engine(db_url)
    async with schema_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await schema_engine.dispose()
    return db_name


async def copy_tables(source_url: str, dest_url: str) -> dict:
    """Upsert COPY_TABLES from source to dest. Returns per-table counts."""
    src = _engine(source_url)
    dst = _engine(dest_url)
    src_session = async_sessionmaker(src, expire_on_commit=False)
    dst_session = async_sessionmaker(dst, expire_on_commit=False)
    counts: dict = {}
    try:
        async with src_session() as s, dst_session() as d:
            for table in COPY_TABLES:
                model = TABLE_MODELS[table]
                rows = (await s.execute(select(model))).scalars().all()
                n = 0
                for row in rows:
                    data = {c.key: getattr(row, c.key) for c in model.__table__.columns}
                    await d.merge(model(**data))
                    n += 1
                counts[table] = n
            await d.commit()
    finally:
        await src.dispose()
        await dst.dispose()
    return counts


async def table_counts(db_url: str) -> dict:
    """Row counts for COPY_TABLES + users (read-only status)."""
    engine = _engine(db_url)
    session = async_sessionmaker(engine, expire_on_commit=False)
    counts: dict = {}
    try:
        async with session() as s:
            for table in COPY_TABLES + ["users"]:
                model = TABLE_MODELS.get(table, UserORM)
                counts[table] = (
                    await s.execute(select(func.count()).select_from(model))
                ).scalar_one()
    finally:
        await engine.dispose()
    return counts


async def seed_local_admin(db_url: str) -> dict:
    """Ensure the local working admin exists. Password comes from
    ``LOCAL_ADMIN_PASSWORD`` (dev default ``admin123``); secrets stay in the
    environment, never in files or logs. Idempotent."""
    password = os.getenv("LOCAL_ADMIN_PASSWORD", "admin123")
    engine = _engine(db_url)
    session = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session() as s:
            existing = (
                await s.execute(select(UserORM).where(UserORM.username == "admin"))
            ).scalar_one_or_none()
            if existing is None:
                s.add(
                    UserORM(
                        id=str(uuid.uuid4()),
                        username="admin",
                        email="admin@codecoach.local",
                        hashed_password=bcrypt.hashpw(
                            password.encode("utf-8"), bcrypt.gensalt()
                        ).decode("utf-8"),
                        created_at=datetime.now(timezone.utc),
                        is_active=1,
                        role="admin",
                    )
                )
                await s.commit()
                return {"admin": "created"}
            return {"admin": "exists"}
    finally:
        await engine.dispose()


async def _cmd_init(args) -> int:
    name = await init_db(args.url)
    print(f"init: database '{name}' ready at {_redact(args.url)}")
    admin = await seed_local_admin(args.url)
    print(f"init: local admin user: {admin['admin']}")
    counts = await table_counts(args.url)
    print("init: counts:", counts)
    return 0


async def _cmd_pull(args) -> int:
    if not pull_allowed(args.to):
        print(
            f"REFUSED: pull destination must be local, got {_redact(args.to)}",
            file=sys.stderr,
        )
        return 2
    await init_db(args.to)
    counts = await copy_tables(args.source_url, args.to)
    print(f"pull: {_redact(args.source_url)} -> {_redact(args.to)}:", counts)
    return 0


async def _cmd_promote(args) -> int:
    token = os.getenv(PROMOTE_CONFIRM_ENV)
    if not promote_allowed(args.to, token):
        print(
            "REFUSED: promote needs a non-local target and "
            f"{PROMOTE_CONFIRM_ENV}={PROMOTE_CONFIRM_TOKEN}",
            file=sys.stderr,
        )
        return 2
    counts = await copy_tables(args.source_url, args.to)
    print(
        f"promote: {_redact(args.source_url)} -> {_redact(args.to)}:",
        counts,
    )
    return 0


async def _cmd_status(args) -> int:
    print(f"status: {_redact(args.url)}:", await table_counts(args.url))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="create branch database + schema")
    p_init.add_argument("--url", required=True, help="local branch DB URL")
    p_init.set_defaults(fn=_cmd_init)

    p_pull = sub.add_parser("pull", help="copy live curriculum -> local")
    p_pull.add_argument("--from", dest="source_url", required=True)
    p_pull.add_argument("--to", required=True)
    p_pull.set_defaults(fn=_cmd_pull)

    p_promote = sub.add_parser("promote", help="copy local curriculum -> live")
    p_promote.add_argument("--from", dest="source_url", required=True)
    p_promote.add_argument("--to", required=True)
    p_promote.set_defaults(fn=_cmd_promote)

    p_status = sub.add_parser("status", help="row counts for a database")
    p_status.add_argument("--url", required=True)
    p_status.set_defaults(fn=_cmd_status)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return asyncio.run(args.fn(args))


if __name__ == "__main__":
    sys.exit(main())
