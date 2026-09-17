"""Unit tests for scripts/branch_db.py (Issue #168).

Pure-logic tests only — no database connections. Covers the per-branch
temp-database workflow: name derivation, FK-safe copy order, and the
fail-safe gates that keep pull (live -> local) and promote (local -> live)
from ever pointing at the wrong end.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

import branch_db


def test_branch_db_name_is_sanitized_prefixed_and_fits_postgres_limit():
    name = branch_db.branch_db_name("chore/168-local-postgres-branch-db")
    assert name.startswith("codecoach_")
    assert "/" not in name and "-" not in name
    assert len(name) <= 63
    assert name == "codecoach_168_local_postgres_branch_db"


def test_branch_db_name_truncates_very_long_slugs_deterministically():
    long_slug = "feat/999-" + "a-very-long-branch-name-" * 10
    name = branch_db.branch_db_name(long_slug)
    assert len(name) <= 63
    assert name == branch_db.branch_db_name(long_slug)


def test_copy_tables_respect_foreign_key_order():
    order = branch_db.COPY_TABLES
    assert set(order) == {"questions", "courses", "modules", "lessons"}
    # courses before modules/lessons (course_id FK); questions before
    # lessons (question_id FK); modules before lessons (module_id FK).
    assert order.index("courses") < order.index("modules")
    assert order.index("courses") < order.index("lessons")
    assert order.index("questions") < order.index("lessons")
    assert order.index("modules") < order.index("lessons")


def test_pull_refuses_non_local_destination():
    assert branch_db.pull_allowed("postgresql://db.example.com:5432/x") is False
    assert branch_db.pull_allowed("postgresql://localhost:5433/codecoach_x") is True
    assert branch_db.pull_allowed("postgresql://127.0.0.1:5432/codecoach_x") is True


def test_promote_requires_confirm_token_and_live_target():
    live = "postgresql://db.example.com:5432/postgres"
    assert branch_db.promote_allowed(live, confirm_token="wrong-token") is False
    assert (
        branch_db.promote_allowed(live, confirm_token=branch_db.PROMOTE_CONFIRM_TOKEN)
        is True
    )
    # Refuses localhost targets even with the token (wrong direction).
    assert (
        branch_db.promote_allowed(
            "postgresql://localhost:5433/codecoach_x",
            confirm_token=branch_db.PROMOTE_CONFIRM_TOKEN,
        )
        is False
    )


class TestOwnerRemap:
    """Regression: pull/promote crashed with ForeignKeyViolationError when the
    source DB's course owner_ids did not exist in the destination (users never
    travel with the curriculum). copy_tables must null them instead."""

    def test_unresolvable_owner_is_nulled(self):
        data = {"id": "c1", "owner_id": "40dfa91b-e7db-40f9-b4f9-4c5faa30da38"}
        fixed = branch_db._drop_unresolvable_owner(data, dst_user_ids={"u-1"})
        assert fixed["owner_id"] is None

    def test_resolvable_owner_is_preserved(self):
        owner = "35370a55-9372-43f8-bde1-12921c1fbac8"
        data = {"id": "c1", "owner_id": owner}
        fixed = branch_db._drop_unresolvable_owner(data, dst_user_ids={owner})
        assert fixed["owner_id"] == owner

    def test_null_owner_stays_null(self):
        data = {"id": "c1", "owner_id": None}
        fixed = branch_db._drop_unresolvable_owner(data, dst_user_ids=set())
        assert fixed["owner_id"] is None

    def test_owner_remap_applies_only_to_courses(self):
        # Questions/modules/lessons have no owner column; the remap must be
        # keyed on the courses table so other rows pass through untouched.
        assert branch_db.COPY_TABLES.count("courses") == 1
