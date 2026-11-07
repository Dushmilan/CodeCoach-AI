"""Fixtures for migration tests.

Migration testing runs against the dedicated scratch database
(``codecoach_migration_test``, issue #316 — NOT the database named by
``DATABASE_URL``). The migration module drops all tables itself before
exercising the Alembic graph, so it never depends on
`Base.metadata.create_all` to build the schema — verifying the migrations
produce it end-to-end.

Dedicated test databases (``codecoach_test``, the name CI's migration job
exclusively controls) still pass through unchanged; any other name — e.g. a
local per-branch working database — is rerouted to the scratch database on
the same server so a local ``pytest tests/migrations`` can never wipe
seeded work. Set ``MIGRATION_TESTS_USE_DATABASE_URL_DB=1`` to opt back into
directly using whatever ``DATABASE_URL`` names (explicit acknowledgement of
the destructive ``DROP SCHEMA public CASCADE``).

In CI this suite runs as its own job against a dedicated, empty
``POSTGRES_DB=codecoach_test``, so there is no cross-suite interference.
"""

import os
import urllib.parse
from pathlib import Path
from typing import Iterator

import pytest
from alembic.config import Config

from app.core.db_url import escape_configparser


BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

# Scratch database the suite owns outright (see issue #316): created on the
# same server as DATABASE_URL, then dropped/recreated schema-wide by
# `_drop_all_tables`.
MIGRATION_SCRATCH_DB = "codecoach_migration_test"
# Opt-in to use the DATABASE_URL-named database verbatim (destructive).
MIGRATION_TESTS_USE_DATABASE_URL_DB = "MIGRATION_TESTS_USE_DATABASE_URL_DB"
# Databases exclusively controlled by a migration job (CI) — safe to use
# verbatim because no working data lives there.
_DEDICATED_DBS = {"codecoach_test", MIGRATION_SCRATCH_DB}


def _is_postgres(url: str) -> bool:
    return url.startswith("postgresql://") or url.startswith("postgresql+")


def _migration_url() -> str:
    base = os.environ.get(
        "DATABASE_URL",
        "postgresql://codecoach:codecoach@127.0.0.1:5432/codecoach_test",
    ).replace("host.docker.internal", "127.0.0.1")
    if not _is_postgres(base):
        raise RuntimeError(
            f"Unsupported DATABASE_URL for migrations: {base} (PostgreSQL only)"
        )
    # alembic/env.py drives migrations through an async engine, so force the
    # asyncpg driver (same as the app) for the migration runs.
    if base.startswith("postgresql://"):
        base = base.replace("postgresql://", "postgresql+asyncpg://", 1)
    return _reroute_to_scratch(base)


def _connection_params(url: str):
    normalized = url.replace("postgresql+asyncpg://", "postgresql://")
    parsed = urllib.parse.urlparse(normalized)
    return {
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "user": urllib.parse.unquote(parsed.username or ""),
        "password": urllib.parse.unquote(parsed.password or ""),
        "database": (parsed.path or "").lstrip("/").split("?")[0] or None,
    }


def _database_name(url: str) -> str | None:
    params = _connection_params(url)
    return params["database"]


def _reroute_to_scratch(url: str) -> str:
    """Point the migration URL at the scratch database (issue #316).

    Saving grace rule: a destructive suite must not follow a developer's
    working URL. Dedicated test databases pass through (CI depends on the
    exact name); everything else — least of all a per-branch working DB —
    is rerouted unless explicitly opted in.
    """
    database = _database_name(url) or ""
    if database in _DEDICATED_DBS:
        return url
    if os.environ.get(MIGRATION_TESTS_USE_DATABASE_URL_DB) == "1":
        print(
            "[migrations] WARNING: using the DATABASE_URL-named database "
            f"verbatim ({database}) — its public schema WILL be dropped "
            "(opt-out by unsetting MIGRATION_TESTS_USE_DATABASE_URL_DB)"
        )
        return url
    if database == "":
        raise RuntimeError("DATABASE_URL must name a database")
    parts = urllib.parse.urlsplit(url)
    rerouted = urllib.parse.urlunsplit(parts._replace(path=f"/{MIGRATION_SCRATCH_DB}"))
    print(
        f"[migrations] rerouting DATABASE_URL database '{database}' -> "
        f"'scratch {MIGRATION_SCRATCH_DB}' (issue #316; the original "
        "database is NOT touched)"
    )
    return rerouted


def ensure_scratch_database(url: str) -> None:
    """Create the scratch database on the same server if it is missing.

    Idempotent: `CREATE DATABASE` races and re-runs are tolerated via the
    DuplicateDatabase check (PostgreSQL has no IF NOT EXISTS).
    """
    import psycopg

    params = _connection_params(url)
    target = params["database"]
    if not target:
        raise RuntimeError("cannot create scratch: DATABASE_URL names no database")
    conn = psycopg.connect(
        host=params["host"],
        port=params["port"],
        user=params["user"],
        password=params["password"],
        dbname="postgres",
        autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (target,),
            )
            if cur.fetchone() is None:
                identifier = target.replace('"', '""')
                cur.execute(f'CREATE DATABASE "{identifier}"')
    finally:
        conn.close()


def _drop_all_tables(url: str) -> None:
    import psycopg

    params = _connection_params(url)
    conn = psycopg.connect(
        host=params["host"],
        port=params["port"],
        user=params["user"],
        password=params["password"],
        dbname=params["database"],
        autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            cur.execute("DROP SCHEMA IF EXISTS public CASCADE")
            cur.execute("CREATE SCHEMA public")
    finally:
        conn.close()


@pytest.fixture(scope="session", autouse=True)
def _reset_tables() -> Iterator[None]:
    url = _migration_url()
    ensure_scratch_database(url)
    _drop_all_tables(url)
    yield


@pytest.fixture(scope="session")
def migration_url() -> str:
    return _migration_url()


@pytest.fixture(scope="session")
def alembic_config(migration_url: str) -> Iterator[Config]:
    """Alembic Config bound to the migration schema.

    DATABASE_URL is pinned to the migration schema for the session so env.py
    (which re-reads the env var at command time) targets the right schema.
    """
    old_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = migration_url
    try:
        cfg = Config(str(BACKEND_DIR / "alembic.ini"))
        cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
        # Escape `%` (percent-encoded pooler passwords) like alembic/env.py
        # does — RawConfigParser interpolation rejects bare `%` in values.
        cfg.set_main_option("sqlalchemy.url", escape_configparser(migration_url))
        yield cfg
    finally:
        if old_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = old_url
