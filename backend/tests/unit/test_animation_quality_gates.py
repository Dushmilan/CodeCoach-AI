"""Animation quality gates (A4): lint checks + corpus gate over fixtures.

The lint unit test pins the non-blocking `lint_quality` contract (camera,
badge, duplicate narration). The service-level gate builds animations for a
small curated subset (array/stack/tree) with a fake executor — no Piston, no
network — and asserts zero quality warnings. It stays under the 60s budget by
construction (3 fixtures, capped traces).
"""

import json
import time

import pytest

from app.ports.code_executor import ExecutionResult
from app.services.animation_validator import AnimationValidator
from app.services.solution_animation_service import SolutionAnimationService


def test_lint_quality_flags_missing_camera_and_badge():
    v = AnimationValidator()
    script = {
        "steps": [
            {
                "narration": "Intro",
                "shapes": [],
                "motion": [{"target": "a", "op": "scale", "to": 1.0, "duration": 0.25}],
            },
            {
                "narration": "Intro",
                "shapes": [],
                "motion": [{"target": "a", "op": "scale", "to": 1.0, "duration": 0.25}],
            },
        ]
    }
    warnings = v.lint_quality(script)
    assert any("camera" in w for w in warnings)
    assert any("badge" in w for w in warnings)
    assert any("duplicate" in w for w in warnings)


class FakeExecutor:
    def __init__(self, result: ExecutionResult):
        self.result = result

    async def execute(self, language, code, stdin="", version=None):
        return self.result


def _ok(stdout: str) -> ExecutionResult:
    return ExecutionResult(stdout=stdout, stderr="", exit_code=0)


def _trace(events):
    return "\n".join(json.dumps(e) for e in events)


# Curated corpus subset: one canonical examples[0]-style fixture per family.
# Questions resolve via catalog match_keys; traces mirror the instrumented
# reference solutions (init + events + return).
FIXTURES = [
    {
        "family": "array",
        "question": {
            "id": "bubble-sort",
            "title": "Bubble Sort",
            "category": "sorting",
            "description": "Sort the array using bubble sort.",
            "examples": [{"input": "[5,1,4,2,8]", "output": "[1,2,4,5,8]"}],
        },
        "stdout": _trace(
            [
                {"event": "init", "values": [5, 1, 4, 2, 8], "family": "array"},
                {"event": "pointer", "name": "j", "index": 0},
                {"event": "compare", "i": 0, "j": 1},
                {"event": "swap", "i": 0, "j": 1},
                {"event": "pointer", "name": "j", "index": 1},
                {"event": "compare", "i": 1, "j": 2},
                {"event": "swap", "i": 1, "j": 2},
                {"event": "mark", "i": 4, "state": "sorted"},
                {"event": "return", "result": [1, 2, 4, 5, 8]},
            ]
        ),
    },
    {
        "family": "stack",
        "question": {
            "id": "valid-parentheses",
            "title": "Valid Parentheses",
            "category": "stack",
            "description": "Check whether the bracket string has valid parentheses ordering.",
            "examples": [{"input": '"()[]{}"', "output": "true"}],
        },
        "stdout": _trace(
            [
                {
                    "event": "init",
                    "values": ["(", ")", "[", "]", "{", "}"],
                    "family": "stack",
                },
                {"event": "visit", "i": 0},
                {"event": "push", "value": "("},
                {"event": "visit", "i": 1},
                {"event": "pop", "value": "("},
                {"event": "visit", "i": 2},
                {"event": "push", "value": "["},
                {"event": "visit", "i": 3},
                {"event": "pop", "value": "["},
                {"event": "visit", "i": 4},
                {"event": "push", "value": "{"},
                {"event": "visit", "i": 5},
                {"event": "pop", "value": "{"},
                {"event": "return", "result": True},
            ]
        ),
    },
    {
        "family": "tree",
        "question": {
            "id": "maximum-depth-of-binary-tree",
            "title": "Maximum Depth of Binary Tree",
            "category": "trees",
            "description": "Compute the maximum depth of binary tree.",
            "examples": [{"input": '"[3,9,20,null,null,15,7]"', "output": "3"}],
        },
        "stdout": _trace(
            [
                {
                    "event": "init",
                    "values": [3, 9, 20, None, None, 15, 7],
                    "family": "tree",
                },
                {"event": "visit", "i": 0},
                {"event": "visit", "i": 1},
                {"event": "visit", "i": 2},
                {"event": "mark", "i": 2, "state": "active"},
                {"event": "visit", "i": 5},
                {"event": "visit", "i": 6},
                {"event": "return", "result": 3},
            ]
        ),
    },
]


@pytest.mark.asyncio
async def test_corpus_gate_zero_quality_warnings():
    started = time.monotonic()
    validator = AnimationValidator()
    for fixture in FIXTURES:
        service = SolutionAnimationService(
            executor=FakeExecutor(_ok(fixture["stdout"]))
        )
        animation = await service.build_animation(fixture["question"])
        assert animation is not None, f"no animation for {fixture['family']}"
        warnings = validator.lint_quality(animation)
        assert warnings == [], f"{fixture['family']} warnings: {warnings}"
    assert time.monotonic() - started < 60
