"""Unit tests for #287 intent annotations in the scene planner.

A step that carries ``annotation`` (originating from a real ``intent`` field
on its trace event) must ride its beat as ``{"text": ...}``; beats built
from un-annotated steps must not grow the key at all. Intro/outro beats are
never annotated. Chained decision beats (pointer+compare chunked into one
beat) take the compare's annotation — the comparison is the decision.
"""

from app.models.animation_spec import (
    AlgorithmAnimation,
    AnimationStepSpec,
    Complexity,
    InitialState,
)
from app.services import scene_planner


def _complexity():
    return Complexity(time="O(n)", space="O(1)")


def _searching(steps):
    return AlgorithmAnimation(
        algorithm="binary_search",
        visualization="sorted-array",
        initialState=InitialState(array=[1, 3, 5, 7, 9], target=7),
        steps=steps,
        complexity=_complexity(),
    )


def _array(steps):
    return AlgorithmAnimation(
        algorithm="two_sum_ii",
        visualization="array",
        initialState=InitialState(array=[2, 7, 11, 15], target=9),
        steps=steps,
        complexity=_complexity(),
    )


def _annotated(beats):
    return [b for b in beats if "annotation" in b]


class TestSearchingAnnotations:
    def test_inspect_mid_beat_carries_the_intent_text(self):
        beats = scene_planner.plan(
            _searching(
                [
                    AnimationStepSpec(action="set_bounds", low=0, high=4),
                    AnimationStepSpec(
                        action="inspect_mid",
                        index=2,
                        annotation="5 < 7 → search right →",
                    ),
                ]
            )
        )
        tagged = _annotated(beats)
        assert len(tagged) == 1
        assert tagged[0]["annotation"] == {"text": "5 < 7 → search right →"}
        assert "Inspect mid [2]" in tagged[0]["narration"]

    def test_steps_without_intent_add_no_annotation_key(self):
        beats = scene_planner.plan(
            _searching(
                [
                    AnimationStepSpec(action="set_bounds", low=0, high=4),
                    AnimationStepSpec(action="inspect_mid", index=2),
                    AnimationStepSpec(action="discard_right", index=2, until=3),
                ]
            )
        )
        assert _annotated(beats) == []
        # Intro and outro are synthesized beats — they never annotate.
        assert "annotation" not in beats[0]
        assert "annotation" not in beats[-1]


class TestArrayAnnotations:
    def test_chunked_decision_beat_takes_the_compares_annotation(self):
        # pointer + compare over an overlapping index chunk into ONE beat;
        # the comparison is the decision, so its intent wins.
        beats = scene_planner.plan(
            _array(
                [
                    AnimationStepSpec(action="pointer", index=0),
                    AnimationStepSpec(
                        action="compare",
                        indices=[0, 3],
                        annotation="sum 17 > 9 → move right pointer left",
                    ),
                ]
            )
        )
        tagged = _annotated(beats)
        assert len(tagged) == 1
        assert tagged[0]["annotation"]["text"] == "sum 17 > 9 → move right pointer left"

    def test_window_beat_carries_the_shrink_intent(self):
        beats = scene_planner.plan(
            _array(
                [
                    AnimationStepSpec(
                        action="window",
                        low=1,
                        high=3,
                        annotation="'a' repeats at [0] → window now [1..3]",
                    ),
                ]
            )
        )
        tagged = _annotated(beats)
        assert len(tagged) == 1
        assert (
            tagged[0]["annotation"]["text"] == "'a' repeats at [0] → window now [1..3]"
        )

    def test_plain_compare_beat_stays_unannotated(self):
        beats = scene_planner.plan(
            _array([AnimationStepSpec(action="compare", indices=[0, 1])])
        )
        assert _annotated(beats) == []
