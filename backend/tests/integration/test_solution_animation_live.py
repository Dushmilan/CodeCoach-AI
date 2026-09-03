"""Integration tests: the solution-animation pipeline against a LIVE Piston.

Exercises the exact production path the ANIMATION validation gate uses —
reference solution → trace harness → sandbox execution → trace parse →
family compile → validator — for representative seeded questions.

Skipped when Piston is unreachable (CI provides it via docker compose).
Unit tests with a fake executor cover logic; these tests prove the
instrumented code really runs in the sandbox and yields valid animations.
"""

import os

import httpx
import pytest

from app.services.animation_validator import AnimationValidator
from app.services.piston_service import PistonService
from app.services.solution_animation_service import SolutionAnimationService

PISTON_URL = os.environ.get("PISTON_API_URL", "http://127.0.0.1:2000/api/v2")


def _piston_available() -> bool:
    try:
        res = httpx.get(f"{PISTON_URL}/runtimes", timeout=5)
        return res.status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _piston_available(), reason="Piston unavailable — skipping live animation tests"
)


def _question(qid, title, category, description, example_input, example_output=""):
    return {
        "id": qid,
        "title": title,
        "category": category,
        "description": description,
        "examples": [{"input": example_input, "output": example_output}],
    }


QUESTIONS = [
    _question(
        "contains-duplicate",
        "Contains Duplicate",
        "arrays",
        "Given an integer array nums, return true if any value appears at least twice.",
        "[1,2,3,1]",
        "true",
    ),
    _question(
        "two-sum",
        "Two Sum",
        "arrays",
        "Given an array of integers nums and an integer target, return indices of the two numbers that add up to target.",
        "[2,7,11,15], 9",
        "[0,1]",
    ),
    _question(
        "binary-search",
        "Binary Search",
        "binary-search",
        "Given a sorted integer array nums and a target, return its index or -1.",
        "[-1,0,3,5,9,12], 9",
        "4",
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("question", QUESTIONS, ids=[q["id"] for q in QUESTIONS])
async def test_live_animation_is_valid_with_enough_steps(question):
    service = SolutionAnimationService(PistonService())
    script = await service.build_animation(question, title=question["title"])

    assert script is not None, f"no animation produced for {question['id']}"
    steps = script.get("steps", [])
    # The ANIMATION gate requires a green beat count (animation.steps >= 3).
    assert len(steps) >= 3, f"only {len(steps)} steps for {question['id']}"
    assert script.get("title"), "missing title"
    assert (script.get("data") or {}).get("family"), "missing family attribution"

    validated, reason = AnimationValidator().validate(script)
    assert validated is not None, f"validator rejected {question['id']}: {reason}"


@pytest.mark.asyncio
async def test_live_animation_degrades_to_none_for_unknown_question():
    service = SolutionAnimationService(PistonService())
    script = await service.build_animation(
        _question(
            "nope-zzz",
            "Flibbertigibbet Quandaries",
            "misc",
            "Do something indescribable with zzzTop.",
            "???",
        ),
        title="Flibbertigibbet Quandaries",
    )
    assert script is None
