"""Unit tests for the test-database host guard (tests/db_guard.py).

These tests must not import tests.conftest (that would trigger the schema
setup); db_guard.py is side-effect free by design.
"""

import pytest

from tests.db_guard import assert_test_db_allowed


def test_allows_loopback_ipv4():
    assert_test_db_allowed(
        "postgresql://codecoach:codecoach@127.0.0.1:5433/codecoach_test"
    )


def test_allows_localhost():
    assert_test_db_allowed(
        "postgresql://codecoach:codecoach@localhost:5432/codecoach_test"
    )


def test_allows_asyncpg_scheme():
    assert_test_db_allowed(
        "postgresql+asyncpg://codecoach:codecoach@127.0.0.1:5433/codecoach_test"
    )


def test_allows_pgbouncer_query_param():
    assert_test_db_allowed(
        "postgresql://codecoach:codecoach@127.0.0.1:5433/codecoach_test?pgbouncer=true"
    )


def test_refuses_supabase_pooler_host():
    with pytest.raises(RuntimeError, match="non-local database host"):
        assert_test_db_allowed(
            "postgresql://postgres.ref@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres"
        )


def test_refuses_generic_remote_host():
    with pytest.raises(RuntimeError, match="non-local database host"):
        assert_test_db_allowed("postgresql://u:p@db.example.com:5432/codecoach_test")


def test_allow_production_escape_hatch():
    assert_test_db_allowed(
        "postgresql://u:p@db.example.com:5432/codecoach_test",
        allow_production="1",
    )


def test_missing_host_raises_value_error():
    with pytest.raises(ValueError):
        assert_test_db_allowed("not-a-url")
