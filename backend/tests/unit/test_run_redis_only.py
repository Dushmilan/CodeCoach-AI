"""Issue #264: /run is Redis-only — no Postgres persists on the hot path."""

import inspect

from app.api.run import execute_code


def test_execute_code_has_no_db_dependencies():
    """Free runs must not touch Postgres; only /submit persists attempts."""
    params = inspect.signature(execute_code).parameters
    assert "jobs" not in params, (
        "execute_code must not depend on ExecutionJobRepository"
    )
    assert "submissions" not in params, (
        "execute_code must not depend on SubmissionRepository"
    )
    assert "reviews" not in params, "execute_code must not depend on ReviewService"
