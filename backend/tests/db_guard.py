"""Guard that prevents the test suite from running against non-local databases.

The suite creates/drops an isolated schema and runs DDL at import time; running
it against the production Supabase pooler (as `backend/.env` would) is dangerous
and slow. This module is intentionally side-effect free so it can be unit-tested
without triggering the conftest DB setup.
"""

import urllib.parse
from typing import Optional

_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "0.0.0.0"})

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


def _host_of(database_url: str) -> str:
    """Return the hostname from a postgresql:// or postgresql+...:// URL."""
    parsed = urllib.parse.urlsplit(database_url)
    host = parsed.hostname
    if not host:
        raise ValueError(f"Could not parse host from DATABASE_URL: {database_url!r}")
    return host


def assert_test_db_allowed(
    database_url: str,
    allow_production: Optional[str] = None,
) -> None:
    """Raise unless the test database URL points at a local Postgres host.

    ``allow_production`` mirrors the ``ALLOW_PRODUCTION_TEST_DB`` env var and is
    the explicit escape hatch for CI or developer machines that intentionally
    target a remote Postgres (still never the production schema).
    """
    host = _host_of(database_url)
    if host in _LOCAL_HOSTS:
        return
    if allow_production and allow_production.strip().lower() in _TRUE_VALUES:
        return
    raise RuntimeError(
        "Refusing to run the test suite against non-local database host "
        f"{host!r}. Point DATABASE_URL at a local Postgres "
        "(see backend/tests/README.md) or set ALLOW_PRODUCTION_TEST_DB=1 to "
        "override (NOT recommended)."
    )
