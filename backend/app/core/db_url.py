"""Database-URL helpers shared by app and alembic env.

Pure string functions so they can be unit-tested without a database or an
Alembic runtime context.
"""

from typing import Optional


def normalize_db_url(url: Optional[str]) -> Optional[str]:
    """Force the asyncpg driver for ``postgresql://`` URLs.

    Supabase/pooler URLs use the bare ``postgresql://`` scheme, which SQLAlchemy
    maps to psycopg2 by default. Async engines (the app plus alembic's
    ``run_async_migrations``) require the asyncpg driver.
    """
    if url and url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def strip_pgbouncer(url: Optional[str]) -> Optional[str]:
    """Drop the Supabase transaction-pooler ``?pgbouncer=true`` param.

    asyncpg / SQLAlchemy would otherwise forward ``pgbouncer`` as an unknown
    connection kwarg and fail to connect. Any other query params are kept.
    """
    if url is None or "pgbouncer" not in url:
        return url
    base, _, query = url.partition("?")
    kept = [kv for kv in query.split("&") if not kv.startswith("pgbouncer")]
    if not kept:
        return base
    return f"{base}?{'&'.join(kept)}"


def escape_configparser(url: Optional[str]) -> Optional[str]:
    """Escape ``%`` for alembic's ConfigParser.

    ``config.set_main_option`` writes the URL into a raw ConfigParser whose
    interpolation syntax treats ``%`` specially. Pooler passwords are often
    percent-encoded (e.g. ``%23`` for ``#``), so ``%`` must be doubled.
    """
    if url is None:
        return None
    return url.replace("%", "%%")


def pooler_connect_args() -> dict:
    """asyncpg options required by Supabase's transaction pooler.

    Pgbouncer reuses prepared-statement names across connections; asyncpg's
    default statement cache then trips ``DuplicatePreparedStatementError``.
    Disabling the cache (mirrors tests/db_helpers.py and database.py).
    """
    return {"statement_cache_size": 0}


def migration_connect_args(search_path: Optional[str] = None) -> dict:
    """Connect args for Alembic migrations: pooler-safe plus optional schema.

    ``DATABASE_SEARCH_PATH`` targets an isolated schema (local dev / tests)
    so migrations land where the app reads instead of ``public``.
    """
    args = pooler_connect_args()
    if search_path:
        args["server_settings"] = {"search_path": search_path}
    return args
