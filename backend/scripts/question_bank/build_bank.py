"""Build the 100-question bank emitted as backend/questions/sample_questions.json.

This is a deterministic, self-verifying builder. Every question is defined with
a reference solution; expected outputs are computed by running the reference so
they are guaranteed correct and consistent with the suite-runner calling
convention used by app/adapters/code_wrappers.

Test-case input encoding follows the suite-runner rules:
  - single-arg questions: one JSON value per line
  - two-arg questions: two lines (second kept raw if it is a bare string)
  - multi-arg questions: one JSON value per line, spread as *args

Run from the backend/ directory:
    python -m scripts.question_bank.build_bank
"""

from __future__ import annotations

import json
import copy
from pathlib import Path
from typing import Any, Callable, Dict, List

from app.models.schemas import Difficulty, Question

OUT_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "questions"
    / "sample_questions.json"
)

TARGET_DIFFICULTY = {"easy": 30, "medium": 50, "hard": 20}
TARGET_TOTAL = 100
MIN_TESTS = 6


class QuestionSpec:
    """A single question definition with a reference solution."""

    def __init__(
        self,
        id: str,
        title: str,
        difficulty: str,
        category: str,
        companies: List[str],
        description: str,
        examples: List[Dict[str, str]],
        tests: List[tuple],
        ref: Callable,
        starter: Dict[str, str],
        hints: List[str],
        solution: str,
        time_complexity: str,
        space_complexity: str,
        constraints: List[str],
        in_place: bool = False,
    ):
        self.id = id
        self.title = title
        self.difficulty = difficulty
        self.category = category
        self.companies = companies
        self.description = description
        self.examples = examples
        self.tests = tests
        self.ref = ref
        self.starter = starter
        self.hints = hints
        self.solution = solution
        self.time_complexity = time_complexity
        self.space_complexity = space_complexity
        self.constraints = constraints
        self.in_place = in_place


def _encode(value: Any) -> str:
    """Serialize a value the way the suite runners print it."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (list, dict)):
        return json.dumps(value, separators=(",", ":"))
    if isinstance(value, str):
        return json.dumps(value)
    return str(value)


def _input_line(value: Any) -> str:
    """Encode a single argument as one input line (JSON if parseable)."""
    if isinstance(value, (list, dict, bool, int, float)):
        return json.dumps(value, separators=(",", ":"))
    return json.dumps(value)


def _encode_input(args: tuple) -> str:
    """Encode a full test-case input following the runner conventions.

    - 1 arg: single line.
    - 2 args: two lines; a bare-string second arg stays raw (the Python runner
      only json-decodes line 2 when it looks numeric/array).
    - 3+ args: one JSON value per line, spread via *args.
    """
    if len(args) == 1:
        return _input_line(args[0])
    if len(args) == 2:
        first = _input_line(args[0])
        second = args[1]
        if isinstance(second, (list, dict, bool, int, float)):
            second_line = json.dumps(second, separators=(",", ":"))
        else:
            second_line = str(second)
        return first + "\n" + second_line
    return "\n".join(_input_line(a) for a in args)


def _expected_from(ref: Callable, args: tuple) -> str:
    """Run the reference and serialize the expected output like a runner.

    A deep copy is used so in-place reference solutions never mutate the
    original test args shared by validation and serialization passes.
    """
    result = ref(*copy.deepcopy(args))
    if result is None:
        # in-place mutation: expected = mutated first arg
        return _encode(copy.deepcopy(args[0]))
    return _encode(result)


def build_test_cases(spec: QuestionSpec) -> List[Dict[str, Any]]:
    test_cases = []
    for i, (args, hidden) in enumerate(spec.tests):
        args_copy = copy.deepcopy(args)
        test_cases.append(
            {
                "input": _encode_input(args_copy),
                "expected_output": _expected_from(spec.ref, args_copy),
                "hidden": bool(hidden),
            }
        )
    return test_cases


def to_question(spec: QuestionSpec) -> Dict[str, Any]:
    return {
        "id": spec.id,
        "title": spec.title,
        "difficulty": spec.difficulty,
        "category": spec.category,
        "company_tags": spec.companies,
        "description": spec.description,
        "examples": spec.examples,
        "test_cases": build_test_cases(spec),
        "starter": spec.starter,
        "hints": spec.hints,
        "solution": spec.solution,
        "time_complexity": spec.time_complexity,
        "space_complexity": spec.space_complexity,
        "constraints": spec.constraints,
        "is_interactive": False,
    }


def validate(specs: List[QuestionSpec]) -> None:
    ids = [s.id for s in specs]
    assert len(ids) == len(set(ids)), (
        f"duplicate ids: {sorted({i for i in ids if ids.count(i) > 1})}"
    )
    assert len(specs) == TARGET_TOTAL, (
        f"expected {TARGET_TOTAL} questions, got {len(specs)}"
    )

    counts = {"easy": 0, "medium": 0, "hard": 0}
    for s in specs:
        Difficulty(s.difficulty)  # raises ValueError if invalid
        counts[s.difficulty] += 1
        assert len(specs_tests(s)) >= MIN_TESTS, f"{s.id} has too few tests"
        Question(**to_question(s))  # schema check
    assert counts == TARGET_DIFFICULTY, (
        f"difficulty distribution {counts} != {TARGET_DIFFICULTY}"
    )


def specs_tests(spec: QuestionSpec) -> List[tuple]:
    return spec.tests


def main() -> None:
    from . import ALL_SPECS

    specs = ALL_SPECS
    validate(specs)
    bank = [to_question(s) for s in specs]
    OUT_PATH.write_text(
        json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(bank)} questions to {OUT_PATH}")


if __name__ == "__main__":
    main()
