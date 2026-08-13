"""Integration test: every question in the live inventory resolves to a
curated animation algorithm and produces a validated scene.

Requires the Supabase-backed DATABASE_URL (see tests/conftest.py); skipped
when the database is unreachable OR the question inventory is not populated
(<50 rows), so local/CI runs without the seeded schema stay green while the
full environment asserts 100% coverage.
"""

import pytest

pytestmark = pytest.mark.integration

from sqlalchemy import select  # noqa: E402

from app.core.database import async_session_maker  # noqa: E402
from app.models.orm import QuestionORM  # noqa: E402
from app.services.reference_solutions import (  # noqa: E402
    get_reference_solution,
    resolve_algorithm,
)


def _db_unreachable(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(
        marker in text
        for marker in (
            "could not connect",
            "connection refused",
            "timeout",
            "cannot connect",
        )
    )


async def _questions():
    async with async_session_maker() as session:
        rows = (await session.execute(select(QuestionORM))).scalars().all()
        return rows


async def test_every_question_resolves_to_a_known_algorithm():
    try:
        rows = await _questions()
    except Exception as exc:  # noqa: BLE001
        if _db_unreachable(exc):
            pytest.skip(f"Supabase unreachable: {exc}")
        raise

    if len(rows) < 50:
        pytest.skip(
            f"question inventory not populated ({len(rows)} < 50); needs seeded DB"
        )
    failures = []
    for row in rows:
        question = {
            "id": row.id,
            "title": row.title,
            "category": row.category,
            "description": row.description,
            "examples": row.examples or [],
        }
        algo = resolve_algorithm(question)
        if not algo or not get_reference_solution(algo):
            failures.append(f"{row.id} | {row.title} | unresolved")
    assert not failures, "unresolved questions:\n" + "\n".join(failures)


async def test_all_questions_have_a_visual_family():
    try:
        rows = await _questions()
    except Exception as exc:  # noqa: BLE001
        if _db_unreachable(exc):
            pytest.skip(f"Supabase unreachable: {exc}")
        raise

    if len(rows) < 50:
        pytest.skip(
            f"question inventory not populated ({len(rows)} < 50); needs seeded DB"
        )

    families = set()
    for row in rows:
        question = {
            "id": row.id,
            "title": row.title,
            "category": row.category,
            "description": row.description,
            "examples": row.examples or [],
        }
        algo = resolve_algorithm(question)
        entry = get_reference_solution(algo)
        if entry:
            families.add(entry["family"])
    for expected in (
        "array",
        "stack",
        "linked_list",
        "tree",
        "grid",
        "graph",
        "intervals",
        "backtrack",
    ):
        assert expected in families, f"family {expected} has no questions in the DB"
