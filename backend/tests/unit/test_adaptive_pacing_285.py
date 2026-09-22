"""Adaptive pacing (#285, Workstream C) — role-tagged beats, role-aware durations.

The scene planner tags each beat with a transient ``role`` (intro = first,
loop = default, climax = found / base case / final return, outro = badge
beat); ``apply_pacing`` rewrites the beat's motion durations within the
validator's 0.1-5.0s window and strips ``role`` so it never reaches the
validated script. Beats without a role keep their durations (covered by the
foundation tests in test_animation_pacing.py).
"""

import pytest

from app.models.animation_spec import (
    AlgorithmAnimation,
    AnimationStepSpec,
    Complexity,
    InitialState,
)
from app.ports.code_executor import ExecutionResult
from app.services import scene_planner
from app.services.animation_pacing import (
    DEFAULT_PROFILE,
    MAX_DURATION,
    MIN_DURATION,
)
from app.services.animation_validator import AnimationValidator
from app.services.scene_planner import _finalize_beats, plan
from app.services.solution_animation_service import SolutionAnimationService


def _binary_spec():
    return AlgorithmAnimation(
        algorithm="binary-search",
        visualization="sorted-array",
        initialState=InitialState(array=[2, 4, 7, 9, 13, 18, 21], target=13),
        steps=[
            AnimationStepSpec(action="set_bounds", low=0, high=6),
            AnimationStepSpec(action="inspect_mid", index=3),
            AnimationStepSpec(action="discard_left", until=4, index=3),
            AnimationStepSpec(action="inspect_mid", index=5),
            AnimationStepSpec(action="discard_right", until=4, index=5),
            AnimationStepSpec(action="found", index=4),
        ],
        complexity=Complexity(time="O(log n)", space="O(1)"),
        title="Binary Search",
    )


def _durations(beat):
    return [
        op["duration"]
        for op in beat.get("motion") or []
        if isinstance(op, dict) and "duration" in op
    ]


def _all_durations(beats):
    return [d for beat in beats for d in _durations(beat)]


class TestPlannerTagsAndPacesRoles:
    def test_intro_climax_and_outro_beats_paced_by_profile(self):
        beats = plan(_binary_spec())
        assert len(beats) >= 8
        intro, outro = beats[0], beats[-1]
        assert _durations(intro), "intro beat must carry motion"
        assert set(_durations(intro)) == {DEFAULT_PROFILE.intro}
        climax = next(
            b for b in beats[1:-1] if (b.get("narration") or "").startswith("Found")
        )
        assert set(_durations(climax)) == {DEFAULT_PROFILE.climax}
        assert "badge" in outro
        assert _durations(outro)
        assert set(_durations(outro)) == {DEFAULT_PROFILE.outro}

    def test_loop_beat_defaults_to_loop_duration(self):
        # The discard beat animates with dim duration (0.3s) — tagging it
        # as the rhythmic loop must rewrite it to the loop profile value.
        beats = plan(_binary_spec())
        loop = next(
            b for b in beats[1:-1] if "discard" in (b.get("narration") or "").lower()
        )
        assert _durations(loop)
        assert set(_durations(loop)) == {DEFAULT_PROFILE.loop}

    def test_climax_beat_slower_than_loop_beat(self):
        # Spec §9: climax beat duration > loop beat duration.
        beats = plan(_binary_spec())
        climax = next(
            b for b in beats[1:-1] if (b.get("narration") or "").startswith("Found")
        )
        loop = next(
            b for b in beats[1:-1] if "discard" in (b.get("narration") or "").lower()
        )
        assert min(_durations(climax)) > max(_durations(loop))

    def test_role_never_survives_into_planner_output(self):
        beats = plan(_binary_spec())
        assert all("role" not in beat for beat in beats)

    def test_every_duration_stays_within_validator_window(self):
        for beat in plan(_binary_spec()):
            for duration in _durations(beat):
                assert MIN_DURATION <= duration <= MAX_DURATION

    def test_paced_beats_still_validate(self):
        beats = plan(_binary_spec())
        validated, reason = AnimationValidator().validate(
            {"title": "Binary Search", "data": {}, "steps": beats}
        )
        assert validated is not None, reason

    def test_preexisting_role_wins_over_inferred_role(self):
        # Planners may pre-tag a beat; the finalize pass must honor it
        # instead of overwriting with the positional default.
        beat = {
            "narration": "Found 7 at [2]",
            "shapes": [],
            "motion": [
                {"target": "cell_2", "op": "fill", "to": "#14532d", "duration": 0.3}
            ],
            "role": "outro",
        }
        outro = {
            "narration": "O(n) · O(1)",
            "shapes": [],
            "motion": [
                {"target": "cell_0", "op": "scale", "to": 1.0, "duration": 0.25}
            ],
        }
        beats = _finalize_beats(
            [beat, dict(outro), dict(outro)], Complexity(time="O(n)", space="O(1)")
        )
        assert "role" not in beats[0]
        assert set(_durations(beats[0])) == {DEFAULT_PROFILE.outro}

    def test_dedupe_suffix_does_not_defeat_climax_detection(self):
        # _finalize_beats dedupes identical middle narrations with a
        # " (cont.)" suffix before tagging roles. The suffixed beat must
        # still detect as climax — plan_array self-finalizes, so a second
        # pass must re-tag the same roles instead of flipping an already
        # paced climax (0.5s) back to the loop duration (0.35s).
        intro = {
            "narration": "Two Sum — Array",
            "shapes": [],
            "motion": [{"target": "cell_0", "op": "appear", "duration": 0.4}],
        }
        mark = {
            "narration": "Mark [2]=7 match",
            "shapes": [],
            "motion": [
                {"target": "cell_2", "op": "fill", "to": "#14532d", "duration": 0.3}
            ],
        }
        outro = {
            "narration": "O(n) · O(1)",
            "shapes": [],
            "motion": [
                {"target": "cell_0", "op": "scale", "to": 1.0, "duration": 0.25}
            ],
            "badge": {"time": "O(n)", "space": "O(1)"},
        }
        beats = _finalize_beats(
            [intro, mark, dict(mark), outro], Complexity(time="O(n)", space="O(1)")
        )
        assert " (cont.)" in beats[2]["narration"]  # dedupe fired
        assert set(_durations(beats[1])) == {DEFAULT_PROFILE.climax}
        assert set(_durations(beats[2])) == {DEFAULT_PROFILE.climax}


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


class _FakeExecutor:
    def __init__(self, result: ExecutionResult):
        self.result = result
        self.calls = []

    async def execute(self, language, code, stdin="", version=None):
        self.calls.append({"language": language, "code": code, "stdin": stdin})
        return self.result


def _question():
    return {
        "id": None,
        "title": "Bubble Sort",
        "category": "sorting",
        "description": "Sort the array using bubble sort.",
        "examples": [{"input": "[5,1,4,2,8]", "output": "[1,2,4,5,8]"}],
    }


class TestServiceBoundaryStripsTransientRoles:
    @pytest.mark.asyncio
    async def test_unfinalized_planner_role_never_reaches_output(self, monkeypatch):
        # Simulate a planner path that forgets to run apply_pacing: the
        # service runs it where beats are finalized, so a transient `role`
        # must be consumed (and its duration honored) before validation.
        real_plan = scene_planner.plan

        def plan_leaving_a_role_behind(spec):
            beats = real_plan(spec)
            beats[1]["role"] = "climax"
            return beats

        monkeypatch.setattr(scene_planner, "plan", plan_leaving_a_role_behind)
        executor = _FakeExecutor(
            ExecutionResult(stdout=BUBBLE_STDOUT, stderr="", exit_code=0)
        )
        service = SolutionAnimationService(executor=executor)
        animation = await service.build_animation(_question())

        assert animation is not None
        steps = animation["steps"]
        assert all("role" not in step for step in steps)
        injected = _durations(steps[1])
        assert injected, "the injected beat must carry motion"
        assert set(injected) == {DEFAULT_PROFILE.climax}
        for duration in _all_durations(steps):
            assert MIN_DURATION <= duration <= MAX_DURATION
        validated, reason = AnimationValidator().validate(animation)
        assert validated is not None, reason

    @pytest.mark.asyncio
    async def test_malformed_planner_payload_fails_safe(self, monkeypatch):
        # The pacing boundary must not KeyError (500) when a planner path
        # returns a payload without `steps` — skip pacing and let the
        # validator reject it so the pipeline degrades to the fallback.
        monkeypatch.setattr(
            SolutionAnimationService,
            "_try_planner",
            lambda self, *a, **k: {"title": "t", "data": {}},
        )
        executor = _FakeExecutor(
            ExecutionResult(stdout=BUBBLE_STDOUT, stderr="", exit_code=0)
        )
        service = SolutionAnimationService(executor=executor)
        result = await service.build_animation(_question())
        assert result is None or isinstance(result, dict)
