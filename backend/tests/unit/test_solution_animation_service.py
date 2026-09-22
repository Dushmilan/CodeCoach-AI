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
    async def test_pointer_beats_carry_event_index(self):
        # #153: pointer events carry the scan position in the `index` field
        # (trace schema), not `i`. The planner mapped `i` only, so every
        # pointer beat clamped to cell_0 and the scan highlight never moved.
        # #240: pointer+compare now chunk into one decision beat, so the
        # mechanical "Pointer →" narration is gone — but the pointer index
        # must still drive the beat (stroke on the pointed cell, never a
        # cell_0 clamp).
        executor = FakeExecutor(_ok_result())
        service = SolutionAnimationService(executor=executor)
        animation = await service.build_animation(_question())

        assert animation is not None
        narrations = [s.get("narration") or "" for s in animation["steps"]]
        assert not any(n.startswith("Pointer") for n in narrations)
        decision_beats = [
            s
            for s in animation["steps"]
            if "Compare [0]=5 vs [1]=1" in (s.get("narration") or "")
        ]
        assert len(decision_beats) == 1
        ops = decision_beats[0]["motion"]
        strokes = [op for op in ops if op["op"] == "stroke"]
        assert "cell_0" in [op["target"] for op in strokes]
        assert {op["target"] for op in ops} == {"cell_0", "cell_1"}

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

    @pytest.mark.asyncio
    async def test_jump_game_beats_render_each_event_at_its_own_cell(self):
        # #235: jump_game traces pointer/read/mark(active) per index. Every
        # beat must animate its own cell — a read of index 3 must never
        # render as a scale on cell_0, and a greedy "active" mark must never
        # claim the cell is "sorted".
        stdout = "\n".join(
            [
                '{"event":"init","values":[2,3,1,1,4],"family":"array"}',
                '{"event":"pointer","name":"i","index":3}',
                '{"event":"read","i":3}',
                '{"event":"mark","i":3,"state":"active"}',
                '{"event":"return","result":true}',
            ]
        )
        executor = FakeExecutor(_ok_result(stdout=stdout))
        service = SolutionAnimationService(executor=executor)
        q = {
            "id": "jump-game",
            "title": "Jump Game",
            "category": "Array",
            "description": "Return true if you can reach the last index.",
            "examples": [{"input": "nums = [2,3,1,1,4]", "output": "true"}],
        }
        animation = await service.build_animation(q)
        assert animation is not None
        validated, reason = AnimationValidator().validate(animation)
        assert validated is not None, reason
        read_beats = [
            s
            for s in animation["steps"]
            if (s.get("narration") or "").startswith("Read")
        ]
        assert len(read_beats) == 1
        assert "[3]" in read_beats[0]["narration"]
        assert "cell_3" in [op["target"] for op in read_beats[0]["motion"]]
        mark_beats = [
            s for s in animation["steps"] if "active" in (s.get("narration") or "")
        ]
        assert len(mark_beats) == 1
        assert "sorted" not in mark_beats[0]["narration"]

    @pytest.mark.asyncio
    async def test_binary_search_beats_narrate_true_bounds_mid_discard(self):
        # #243: the binary_search reference traces pointer(low/high/mid) +
        # compare + mark(match). _try_planner mapped those 1:1 to generic
        # pointer/compare/mark actions, which plan_searching does not
        # understand — every step fell into the placeholder branch (a no-op
        # scale on cell_0 narrated with the raw action name). Beats must
        # instead narrate the true search-region state of each iteration.
        stdout = "\n".join(
            [
                '{"event":"init","values":[1,3,5,7,9],"family":"array"}',
                '{"event":"pointer","name":"low","index":0}',
                '{"event":"pointer","name":"high","index":4}',
                '{"event":"pointer","name":"mid","index":2}',
                '{"event":"compare","i":2}',
                '{"event":"pointer","name":"low","index":3}',
                '{"event":"pointer","name":"high","index":4}',
                '{"event":"pointer","name":"mid","index":3}',
                '{"event":"compare","i":3}',
                '{"event":"mark","i":3,"state":"match"}',
                '{"event":"return","result":3}',
            ]
        )
        executor = FakeExecutor(_ok_result(stdout=stdout))
        service = SolutionAnimationService(executor=executor)
        q = {
            "id": "binary-search",
            "title": "Binary Search",
            "category": "Binary Search",
            "description": "Find the target with binary search.",
            "examples": [{"input": "nums = [1,3,5,7,9], target = 7", "output": "3"}],
        }
        animation = await service.build_animation(q)
        assert animation is not None
        validated, reason = AnimationValidator().validate(animation)
        assert validated is not None, reason

        narrations = [s.get("narration") or "" for s in animation["steps"]]
        # No placeholder beats: raw action names must never narrate a beat.
        assert not any(
            n.strip() in ("compare", "pointer", "mark", "custom") for n in narrations
        )
        # Iteration 1 searched [0..4] and inspected mid [2] = 5.
        assert any("Search region [0..4]" in n for n in narrations)
        assert any("Inspect mid [2]" in n for n in narrations)
        # 5 < 7 discarded the left half; iteration 2 searched [3..4].
        assert any("discard" in n.lower() for n in narrations)
        assert any("Search region [3..4]" in n for n in narrations)
        assert any("Inspect mid [3]" in n for n in narrations)
        # The match at index 3 closes the story with the true target.
        assert any("Found 7 at [3]" in n for n in narrations)

    @pytest.mark.asyncio
    async def test_binary_search_miss_narrates_final_discard_then_not_found(self):
        # #243: when the loop exits without a match, the last bound change
        # is never traced (pointers emit at loop top only). The closing
        # discard is still a fact about the data (values[mid] vs target),
        # so the story must end discard → not found, never a placeholder.
        stdout = "\n".join(
            [
                '{"event":"init","values":[1,3,5,7,9],"family":"array"}',
                '{"event":"pointer","name":"low","index":0}',
                '{"event":"pointer","name":"high","index":4}',
                '{"event":"pointer","name":"mid","index":2}',
                '{"event":"compare","i":2}',
                '{"event":"pointer","name":"low","index":3}',
                '{"event":"pointer","name":"high","index":4}',
                '{"event":"pointer","name":"mid","index":3}',
                '{"event":"compare","i":3}',
                '{"event":"return","result":-1}',
            ]
        )
        executor = FakeExecutor(_ok_result(stdout=stdout))
        service = SolutionAnimationService(executor=executor)
        q = {
            "id": "binary-search",
            "title": "Binary Search",
            "category": "Binary Search",
            "description": "Find the target with binary search.",
            "examples": [{"input": "nums = [1,3,5,7,9], target = 6", "output": "-1"}],
        }
        animation = await service.build_animation(q)
        assert animation is not None
        validated, reason = AnimationValidator().validate(animation)
        assert validated is not None, reason

        narrations = [s.get("narration") or "" for s in animation["steps"]]
        assert not any(
            n.strip() in ("compare", "pointer", "mark", "custom") for n in narrations
        )
        # 7 > 6 discarded the right half before the miss closed the story.
        assert any("discard right ←" in n for n in narrations)
        assert any("6 not in array" in n for n in narrations)

    @pytest.mark.asyncio
    async def test_linear_search_hit_ends_in_result_climax(self):
        # #240: the returned index must close with a found climax beat on
        # the real cell — no trailing mark(match) duplicate, no placeholder.
        stdout = "\n".join(
            [
                '{"event":"init","values":[4,1,7],"family":"array"}',
                '{"event":"pointer","name":"i","index":0}',
                '{"event":"compare","i":0}',
                '{"event":"pointer","name":"i","index":1}',
                '{"event":"compare","i":1}',
                '{"event":"pointer","name":"i","index":2}',
                '{"event":"compare","i":2}',
                '{"event":"mark","i":2,"state":"match"}',
                '{"event":"return","result":2}',
            ]
        )
        executor = FakeExecutor(_ok_result(stdout=stdout))
        service = SolutionAnimationService(executor=executor)
        q = {
            "id": "linear-search",
            "title": "Linear Search",
            "category": "Array",
            "description": "Find the target with linear search.",
            "examples": [{"input": "values = [4,1,7], target = 7", "output": "2"}],
        }
        animation = await service.build_animation(q)
        assert animation is not None
        validated, reason = AnimationValidator().validate(animation)
        assert validated is not None, reason

        narrations = [s.get("narration") or "" for s in animation["steps"]]
        assert any("Found 7 at [2]" in n for n in narrations)
        # The mark(match) beat folds into the climax — exactly one success
        # beat for cell 2, and no mechanical pointer beats remain.
        assert not any("Mark [2]" in n for n in narrations)
        assert not any(n.startswith("Pointer") for n in narrations)

    @pytest.mark.asyncio
    async def test_linear_search_miss_ends_not_found(self):
        stdout = "\n".join(
            [
                '{"event":"init","values":[4,1,7],"family":"array"}',
                '{"event":"pointer","name":"i","index":0}',
                '{"event":"compare","i":0}',
                '{"event":"pointer","name":"i","index":1}',
                '{"event":"compare","i":1}',
                '{"event":"pointer","name":"i","index":2}',
                '{"event":"compare","i":2}',
                '{"event":"return","result":-1}',
            ]
        )
        executor = FakeExecutor(_ok_result(stdout=stdout))
        service = SolutionAnimationService(executor=executor)
        q = {
            "id": "linear-search",
            "title": "Linear Search",
            "category": "Array",
            "description": "Find the target with linear search.",
            "examples": [{"input": "values = [4,1,7], target = 9", "output": "-1"}],
        }
        animation = await service.build_animation(q)
        assert animation is not None
        validated, reason = AnimationValidator().validate(animation)
        assert validated is not None, reason

        narrations = [s.get("narration") or "" for s in animation["steps"]]
        assert any("9 not in array" in n for n in narrations)

    @pytest.mark.asyncio
    async def test_sorted_result_narrated_in_outro(self):
        # #240: a list result cannot highlight one cell — the outro beat
        # carries the actual result next to the complexity badge.
        executor = FakeExecutor(_ok_result())
        service = SolutionAnimationService(executor=executor)
        animation = await service.build_animation(_question())

        assert animation is not None
        validated, reason = AnimationValidator().validate(animation)
        assert validated is not None, reason
        outro = animation["steps"][-1]
        assert "Result [1, 2, 4, 5, 8]" in (outro.get("narration") or "")
        assert outro.get("badge") == {"time": "O(n²)", "space": "O(1)"}
