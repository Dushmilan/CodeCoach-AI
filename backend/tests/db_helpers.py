"""Dialect-aware DB helpers for tests.

The app now runs on both MySQL (local) and PostgreSQL/Supabase (primary).
Several tests promote users / truncate tables by connecting to the DB
directly. These helpers adapt to whichever DATABASE_URL is configured so
those tests work unchanged on either dialect.
"""

import os


def is_postgres() -> bool:
    url = os.environ.get("DATABASE_URL", "")
    return url.startswith("postgresql://") or url.startswith("postgresql+asyncpg://")


def test_db_url() -> str:
    """Return the configured test URL with the asyncpg driver forced for PG."""
    url = strip_pgbouncer(os.environ["DATABASE_URL"])
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def strip_pgbouncer(url: str) -> str:
    """Drop the Supabase transaction-pooler `?pgbouncer=true` param.

    asyncpg / SQLAlchemy would otherwise forward `pgbouncer` as an unknown
    connection kwarg. Direct connections (schema tooling, tests) go through
    the session pooler, so the param is meaningless here.
    """
    if "pgbouncer" not in url:
        return url
    from urllib.parse import urlsplit, urlunsplit

    scheme, netloc, path, query, fragment = urlsplit(url)
    params = [
        kv
        for kv in (query.split("&") if query else [])
        if not kv.startswith("pgbouncer")
    ]
    return urlunsplit((scheme, netloc, path, "&".join(params), fragment))


def engine_kwargs() -> dict:
    """Connect args shared by every test engine (search_path isolation on PG)."""
    kwargs = {}
    if is_postgres():
        kwargs["connect_args"] = {
            "server_settings": {
                "search_path": os.environ.get("DATABASE_SEARCH_PATH", "public")
            },
            # Supabase poolers reuse prepared-statement names across
            # connections; disable asyncpg's statement cache so DDL / DML does
            # not hit DuplicatePreparedStatementError.
            "statement_cache_size": 0,
        }
    return kwargs


async def update_user(where: str, values: dict, username: str) -> None:
    """Run an UPDATE against the users table (dialect-agnostic)."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import NullPool

    engine = create_async_engine(test_db_url(), poolclass=NullPool, **engine_kwargs())
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        await session.execute(
            text(f"UPDATE users SET {where} WHERE username=:u"),
            {**values, "u": username},
        )
        await session.commit()
    await engine.dispose()


async def promote_to_admin(username: str) -> None:
    await update_user("role='admin'", {}, username)


async def set_plan(username: str, plan: str) -> None:
    await update_user("plan=:p", {"p": plan}, username)


def truncate_course_tables_sync() -> None:
    """Remove courses/modules/lessons created by admin curriculum tests."""
    import asyncio

    asyncio.run(_truncate_course_tables_async())


async def _truncate_course_tables_async() -> None:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool

    engine = create_async_engine(test_db_url(), poolclass=NullPool, **engine_kwargs())
    async with engine.begin() as conn:
        if is_postgres():
            await conn.execute(text("SET session_replication_role = 'replica'"))
            for table in ("course_progress", "lessons", "modules", "courses"):
                await conn.execute(text(f'DELETE FROM "{table}"'))
            await conn.execute(text("SET session_replication_role = 'origin'"))
        else:
            await conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
            for table in ("course_progress", "lessons", "modules", "courses"):
                await conn.execute(text(f"TRUNCATE TABLE {table}"))
            await conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    await engine.dispose()
