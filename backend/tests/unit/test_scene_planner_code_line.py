"""Beats carry the source line of the step they choreograph (#284).

Every action beat built from a trace-backed step must expose ``code_line``
(1-based line in the canonical solution) so the dual-pane viewer can
highlight it. Beats with no traced line (intro/outro, synthesized search
steps) stay honest: the key is absent, never invented.
"""

import pytest

from app.models.animation_spec import (
    AlgorithmAnimation,
    AnimationStepSpec,
    Complexity,
    InitialState,
)
from app.services.scene_planner import plan, plan_backtrack, plan_searching


def _spec(viz, steps, array=None, target=None):
    return AlgorithmAnimation(
        algorithm="demo",
        visualization=viz,
        initialState=InitialState(array=array, target=target),
        steps=steps,
        complexity=Complexity(time="O(n)", space="O(1)"),
        title="Demo",
    )


class TestCodeLineOnBeats:
    def test_array_action_beat_carries_its_step_line(self):
        spec = _spec(
            "array",
            [
                AnimationStepSpec(action="compare", indices=[0, 1], line=8),
                AnimationStepSpec(action="swap", indices=[0, 1], line=10),
            ],
            array=[5, 1],
        )
        beats = plan(spec)
        # beats[0] is the intro; each following action beat mirrors its step.
        assert beats[1].get("code_line") == 8
        assert beats[2].get("code_line") == 10

    def test_step_without_line_leaves_the_beat_without_code_line(self):
        spec = _spec(
            "array",
            [AnimationStepSpec(action="compare", indices=[0, 1])],
            array=[5, 1],
        )
        beats = plan(spec)
        assert "code_line" not in beats[1]

    def test_intro_and_outro_beats_have_no_code_line(self):
        spec = _spec(
            "array",
            [AnimationStepSpec(action="compare", indices=[0, 1], line=8)],
            array=[5, 1],
        )
        beats = plan(spec)
        assert "code_line" not in beats[0]
        assert "code_line" not in beats[-1]

    def test_decision_beat_uses_the_compare_line(self):
        # pointer+compare chunk into one decision beat; the compare is the
        # decision the beat narrates, so its line wins.
        spec = _spec(
            "array",
            [
                AnimationStepSpec(action="pointer", index=0, line=6),
                AnimationStepSpec(action="compare", indices=[0, 1], line=7),
            ],
            array=[5, 1],
        )
        beats = plan(spec)
        assert "Compare" in beats[1]["narration"]
        assert beats[1].get("code_line") == 7

    def test_decision_beat_falls_back_to_the_pointer_line(self):
        spec = _spec(
            "array",
            [
                AnimationStepSpec(action="pointer", index=0, line=6),
                AnimationStepSpec(action="compare", indices=[0, 1]),
            ],
            array=[5, 1],
        )
        beats = plan(spec)
        assert "Compare" in beats[1]["narration"]
        assert beats[1].get("code_line") == 6

    @pytest.mark.parametrize(
        ("viz", "step", "array"),
        [
            ("stack", AnimationStepSpec(action="push", values=["x"], line=3), None),
            ("linked_list", AnimationStepSpec(action="visit", index=0, line=4), [1, 2]),
            ("tree", AnimationStepSpec(action="visit", index=0, line=5), [1, 2, 3]),
            ("graph", AnimationStepSpec(action="visit", index=0, line=6), [1, 2, 3]),
            (
                "intervals",
                AnimationStepSpec(action="visit", index=0, line=7),
                [[1, 3], [2, 5]],
            ),
            (
                "backtrack",
                AnimationStepSpec(action="choose", index=0, line=8),
                [1, 2, 3],
            ),
        ],
    )
    def test_every_family_planner_forwards_the_line(self, viz, step, array):
        beats = plan(_spec(viz, [step], array=array))
        assert beats[1].get("code_line") == step.line

    def test_searching_beats_carry_lines(self):
        spec = _spec(
            "sorted-array",
            [
                AnimationStepSpec(action="set_bounds", low=0, high=4, line=4),
                AnimationStepSpec(action="inspect_mid", index=2, line=6),
            ],
            array=[1, 3, 5, 7, 9],
            target=5,
        )
        beats = plan_searching(spec)
        assert beats[1].get("code_line") == 4
        assert beats[2].get("code_line") == 6

    def test_searching_beats_without_lines_stay_silent(self):
        spec = _spec(
            "sorted-array",
            [AnimationStepSpec(action="inspect_mid", index=2)],
            array=[1, 3, 5],
            target=5,
        )
        beats = plan_searching(spec)
        assert "code_line" not in beats[1]

    def test_backtrack_planner_forwards_the_line(self):
        spec = _spec(
            "backtrack",
            [AnimationStepSpec(action="choose", index=0, line=9)],
            array=[1, 2],
        )
        beats = plan_backtrack(spec)
        assert beats[1].get("code_line") == 9
