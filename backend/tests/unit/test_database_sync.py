"""Unit tests for the database sync tool (local SQL -> Supabase/PostgreSQL).

These cover the pure, DB-agnostic logic: table ordering, row normalization,
and count validation. Live sync behavior is exercised by the integration
tests in tests/integration/test_database_sync.py (gated on env vars).
"""

import pytest
from datetime import date, datetime

from app.services.database_sync import (
    TABLE_ORDER,
    FLUSH_ORDER,
    parse_row,
    validate_counts,
    column_names,
)


class TestTableOrdering:
    def test_copy_order_is_fk_safe(self):
        # parents before children
        assert TABLE_ORDER.index("users") < TABLE_ORDER.index("course_progress")
        assert TABLE_ORDER.index("courses") < TABLE_ORDER.index("modules")
        assert TABLE_ORDER.index("modules") < TABLE_ORDER.index("lessons")
        assert TABLE_ORDER.index("questions") < TABLE_ORDER.index("lessons")
        assert TABLE_ORDER.index("users") < TABLE_ORDER.index("user_usage_events")
        assert TABLE_ORDER.index("users") < TABLE_ORDER.index("user_daily_usage")

    def test_flush_order_is_reverse_of_copy(self):
        assert FLUSH_ORDER == list(reversed(TABLE_ORDER))

    def test_all_expected_tables_present(self):
        assert set(TABLE_ORDER) == {
            "users",
            "courses",
            "questions",
            "modules",
            "lessons",
            "course_progress",
            "user_usage_events",
            "user_daily_usage",
        }


class TestParseRow:
    def test_parses_json_string_columns(self):
        row = {
            "id": "q1",
            "company_tags": '["Google", "Meta"]',
            "starter_code": '{"python": "x"}',
            "examples": '[{"input": "1"}]',
            "test_cases": '[{"input": "1", "expected_output": "2"}]',
            "hints": '["a"]',
            "constraints": '["n<=10"]',
            "title": "Two Sum",
        }
        parsed = parse_row("questions", row)
        assert parsed["company_tags"] == ["Google", "Meta"]
        assert parsed["starter_code"] == {"python": "x"}
        assert parsed["examples"] == [{"input": "1"}]
        assert parsed["test_cases"] == [{"input": "1", "expected_output": "2"}]
        assert parsed["hints"] == ["a"]
        assert parsed["constraints"] == ["n<=10"]
        assert parsed["title"] == "Two Sum"

    def test_handles_already_parsed_json(self):
        row = {"id": "q1", "company_tags": ["Google"], "hints": ["a"]}
        parsed = parse_row("questions", row)
        assert parsed["company_tags"] == ["Google"]

    def test_handles_null_json(self):
        row = {"id": "q1", "validation_status": None, "company_tags": None}
        parsed = parse_row("questions", row)
        assert parsed["validation_status"] is None
        assert parsed["company_tags"] is None

    def test_handles_non_json_columns(self):
        row = {"id": "u1", "username": "alice", "is_active": 1}
        parsed = parse_row("users", row)
        assert parsed == {"id": "u1", "username": "alice", "is_active": 1}

    def test_converts_date_to_datetime(self):
        row = {"id": "d1", "usage_date": date(2026, 8, 1)}
        parsed = parse_row("user_daily_usage", row)
        assert isinstance(parsed["usage_date"], datetime)

    def test_boolean_int_columns_kept(self):
        row = {"key": "k", "enabled": 1, "rollout_pct": 50}
        parsed = parse_row("feature_flags", row)
        assert parsed["enabled"] is True


class TestValidateCounts:
    def test_matching_counts_pass(self):
        counts = {"users": 16, "questions": 22}
        validate_counts(counts, counts)

    def test_mismatch_raises(self):
        with pytest.raises(RuntimeError, match="users"):
            validate_counts({"users": 16}, {"users": 15})

    def test_missing_target_table_raises(self):
        with pytest.raises(RuntimeError, match="courses"):
            validate_counts({"users": 1, "courses": 5}, {"users": 1})


class TestColumnNames:
    def test_known_table_columns(self):
        cols = column_names("users")
        assert "username" in cols
        assert "hashed_password" in cols

    def test_unknown_table_returns_empty(self):
        assert column_names("nope") == []
