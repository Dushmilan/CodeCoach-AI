"""Unit tests for SolutionAnimationService — orchestrates the
canonical-optimal-solution → trace → scene pipeline.

The executor is a double: no Piston is touched in these tests. The service
must ignore the user's typed code entirely (it only reads the question) and
return None on any unusable input so the endpoint can degrade gracefully.
"""

import json

import pytest
from fastapi import HTTPException

from app.ports.code_executor import ExecutionResult
from app.services.solution_animation_service import SolutionAnimationService
from app.services.animation_validator import AnimationValidator

BUBBLE_STDOUT = "\n".join(
    [
        '{"event":"init","values":[5,1,4,2,8],"family":"array"}',
        '{"event":"pointer","name":"j","index":0}',
        '{"event":"compare","i":0,"j":1}',
        '{"event":"swap","i":0,"j":1}',
        '{"event":"pointer","name":"j","index":1}',
        '{"event":"compare","i":1,"j":2}',
        '{"event":"swap","i":1,"j":2}',
        '{"event":"mark","i":4,"state":"sorted"}',
        '{"event":"return","result":[1,2,4,5,8]}',
    ]
)


class FakeExecutor:
    def __init__(self, result: ExecutionResult):
        self.result = result
        self.calls = []

    async def execute(self, language, code, stdin="", version=None):
        self.calls.append({"language": language, "code": code, "stdin": stdin})
        return self.result


_MISSING = object()


def _question(
    title="Bubble Sort",
    examples=_MISSING,
    description="Sort the array using bubble sort.",
    qid=None,
):
    return {
        "id": qid,
        "title": title,
        "category": "sorting",
        "description": description,
        "examples": (
            [{"input": "[5,1,4,2,8]", "output": "[1,2,4,5,8]"}]
            if examples is _MISSING
            else examples
        ),
    }


def _ok_result(stdout=BUBBLE_STDOUT):
    return ExecutionResult(stdout=stdout, stderr="", exit_code=0)


class TestBuildAnimation:
    @pytest.mark.asyncio
    async def test_bubble_sort_question_produces_valid_scene(self):
        executor = FakeExecutor(_ok_result())
        service = SolutionAnimationService(executor=executor)
        animation = await service.build_animation(_question())

        assert animation is not None
        validated, reason = AnimationValidator().validate(animation)
        assert validated is not None, reason
        assert animation["title"] == "Bubble Sort"
        assert animation["data"]["values"] == [5, 1, 4, 2, 8]
        # The user's code is never involved: only the canonical solution runs.
        assert executor.calls[0]["code"].count("def bubble_sort") == 1
        assert "def bubble_sort" in executor.calls[0]["code"]
        assert "sys.stdin" in executor.calls[0]["code"]
        assert json.loads(executor.calls[0]["stdin"]) == {"values": [5, 1, 4, 2, 8]}

    @pytest.mark.asyncio
    async def test_exit_code_nonzero_returns_none(self):
        executor = FakeExecutor(ExecutionResult(stdout="", stderr="boom", exit_code=1))
        service = SolutionAnimationService(executor=executor)
        assert await service.build_animation(_question()) is None

    @pytest.mark.asyncio
    async def test_no_question_returns_none(self):
        service = SolutionAnimationService(FakeExecutor(_ok_result()))
        assert await service.build_animation(None) is None
        assert await service.build_animation("nope") is None

    @pytest.mark.asyncio
    async def test_no_matching_algorithm_returns_none(self):
        executor = FakeExecutor(_ok_result())
        service = SolutionAnimationService(executor=executor)
        q = _question(
            title="Invented challenge", description="No known algorithm here."
        )
        assert await service.build_animation(q) is None
        assert executor.calls == []  # nothing ran

    @pytest.mark.asyncio
    async def test_missing_examples_returns_none(self):
        service = SolutionAnimationService(FakeExecutor(_ok_result()))
        assert await service.build_animation(_question(examples=[])) is None
        assert await service.build_animation(_question(examples=None)) is None

    @pytest.mark.asyncio
    async def test_example_input_object_is_serialized(self):
        executor = FakeExecutor(_ok_result())
        service = SolutionAnimationService(executor=executor)
        q = _question(examples=[{"input": {"values": [5, 1, 4, 2, 8]}, "output": "x"}])
        await service.build_animation(q)
        parsed = json.loads(executor.calls[0]["stdin"])
        assert parsed == {"values": [5, 1, 4, 2, 8]}

    @pytest.mark.asyncio
    async def test_kwargs_assignment_input_is_parsed(self):
        executor = FakeExecutor(_ok_result())
        service = SolutionAnimationService(executor=executor)
        q = _question(
            examples=[{"input": "nums = [5,1,4,2,8], target = 3", "output": "x"}]
        )
        await service.build_animation(q)
        parsed = json.loads(executor.calls[0]["stdin"])
        assert parsed == {"nums": [5, 1, 4, 2, 8], "target": 3}

    @pytest.mark.asyncio
    async def test_executor_error_returns_none(self):
        class RaisingExecutor(FakeExecutor):
            async def execute(self, *a, **k):
                raise HTTPException(status_code=500)

        service = SolutionAnimationService(RaisingExecutor(_ok_result()))
        assert await service.build_animation(_question()) is None

    @pytest.mark.asyncio
    async def test_empty_trace_returns_none(self):
        executor = FakeExecutor(_ok_result(stdout=""))
        service = SolutionAnimationService(executor=executor)
        assert await service.build_animation(_question()) is None

    @pytest.mark.asyncio
    async def test_malformed_known_event_returns_none_not_raise(self):
        # A known event kind missing a required field makes parse_trace raise
        # ValueError; build_animation must degrade to None (no 500, no LLM
        # fallback triggered by a curated-solution typo).
        bad_stdout = '{"event":"swap","i":0}'  # j missing
        executor = FakeExecutor(_ok_result(stdout=bad_stdout))
        service = SolutionAnimationService(executor=executor)
        assert await service.build_animation(_question()) is None

    @pytest.mark.asyncio
    async def test_title_falls_back_to_algorithm_name(self):
        executor = FakeExecutor(_ok_result())
        service = SolutionAnimationService(executor=executor)
        q = _question(title="")
        animation = await service.build_animation(q)
        assert animation["title"]  # non-empty fallback

    @pytest.mark.asyncio
    async def test_stack_family_question_dispatches_to_stack_compiler(self):
        stdout = "\n".join(
            [
                '{"event":"init","data":["(",")"],"family":"stack"}',
                '{"event":"push","value":"("}',
                '{"event":"return","result":true}',
            ]
        )
        executor = FakeExecutor(_ok_result(stdout=stdout))
        service = SolutionAnimationService(executor=executor)
        q = {
            "id": "valid-parentheses",
            "title": "Valid Parentheses",
            "category": "Stack & Queue",
            "description": "Determine if the input string is valid.",
            "examples": [{"input": 's = "()"', "output": "true"}],
        }
        animation = await service.build_animation(q)
        assert animation is not None
        validated, reason = AnimationValidator().validate(animation)
        assert validated is not None, reason
        # #141: the cinematic planner path now validates for stack, so it wins
        # over the family-compiler fallback (stack_box). Pin the planner scene.
        targets = {op["target"] for step in animation["steps"] for op in step["motion"]}
        assert "stack_base" in targets
        assert AnimationValidator().lint_quality(animation) == []
