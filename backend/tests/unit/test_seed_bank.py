"""Unit gate for the inline seed bank (backend/tests/conftest.py).

The animation-coverage integration test only runs when the inventory holds
>=50 questions spanning all 8 visual families. This DB-free test pins that
invariant: every seed must validate as a Question and resolve to a known
algorithm + reference solution, so the coverage gate can never silently
skip again because of seed rot.
"""

import pytest

pytestmark = pytest.mark.unit

from app.models.schemas import Question  # noqa: E402
from app.services.reference_solutions import (  # noqa: E402
    get_reference_solution,
    resolve_algorithm,
)
from tests.conftest import _TEST_QUESTIONS  # noqa: E402

EXPECTED_FAMILIES = {
    "array",
    "stack",
    "linked_list",
    "tree",
    "grid",
    "graph",
    "intervals",
    "backtrack",
}


def _as_question_dict(item: dict) -> dict:
    q = Question(**item)
    return {
        "id": q.id,
        "title": q.title,
        "category": q.category,
        "description": q.description,
        "examples": [
            e.model_dump() if hasattr(e, "model_dump") else e for e in q.examples
        ],
    }


def test_seed_bank_has_minimum_inventory():
    assert len(_TEST_QUESTIONS) >= 50, (
        f"seed bank has {len(_TEST_QUESTIONS)} questions; "
        "animation coverage gate needs >= 50"
    )


def test_seed_bank_ids_are_unique():
    ids = [item["id"] for item in _TEST_QUESTIONS]
    assert len(ids) == len(set(ids)), "duplicate seed question ids"


def test_every_seed_resolves_to_a_reference_solution():
    failures = []
    for item in _TEST_QUESTIONS:
        question = _as_question_dict(item)
        algo = resolve_algorithm(question)
        if not algo or not get_reference_solution(algo):
            failures.append(f"{question['id']} | {question['title']} | unresolved")
    assert not failures, "unresolved seeds:\n" + "\n".join(failures)


def test_seed_bank_covers_all_visual_families():
    families = set()
    for item in _TEST_QUESTIONS:
        algo = resolve_algorithm(_as_question_dict(item))
        entry = get_reference_solution(algo) if algo else None
        if entry:
            families.add(entry["family"])
    missing = EXPECTED_FAMILIES - families
    assert not missing, f"families without seed questions: {sorted(missing)}"
