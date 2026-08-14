"""alembic URL handling helpers.

env.py must feed a Supabase-pooler `postgresql://` URL to the async engine and
to alembic's ConfigParser without tripping interpolation syntax on `%`
characters (common in pooler passwords). These helpers are pure functions so
they can be unit-tested without a database connection.
"""

from app.core.db_url import (
    escape_configparser,
    normalize_db_url,
    pooler_connect_args,
    strip_pgbouncer,
)


def test_normalize_db_url_forces_asyncpg():
    assert (
        normalize_db_url("postgresql://user:pass@db:5432/postgres")
        == "postgresql+asyncpg://user:pass@db:5432/postgres"
    )


def test_normalize_db_url_keeps_asyncpg():
    url = "postgresql+asyncpg://user:pass@db:5432/postgres"
    assert normalize_db_url(url) == url


def test_escape_configparser_no_percent():
    url = "postgresql+asyncpg://user:pass@db:5432/postgres"
    assert escape_configparser(url) == url


def test_escape_configparser_escapes_percent():
    url = "postgresql+asyncpg://user:p%ss@db:5432/postgres"
    assert escape_configparser(url) == (
        "postgresql+asyncpg://user:p%%ss@db:5432/postgres"
    )


def test_strip_pgbouncer_drops_param():
    url = "postgresql+asyncpg://u:p@db:6543/postgres?pgbouncer=true"
    assert strip_pgbouncer(url) == "postgresql+asyncpg://u:p@db:6543/postgres"


def test_strip_pgbouncer_keeps_other_params():
    url = "postgresql+asyncpg://u:p@db:6543/postgres?application_name=codecoach&pgbouncer=true"
    assert strip_pgbouncer(url) == (
        "postgresql+asyncpg://u:p@db:6543/postgres?application_name=codecoach"
    )


def test_strip_pgbouncer_noop_without_param():
    url = "postgresql+asyncpg://u:p@db:5432/postgres"
    assert strip_pgbouncer(url) == url


def test_pooler_connect_args_disables_statement_cache():
    assert pooler_connect_args() == {"statement_cache_size": 0}
