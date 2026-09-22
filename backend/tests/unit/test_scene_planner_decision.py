"""TDD red for #240 follow-up — decision beats, window band, result climax.

plan_array maps one trace step to one beat, narrating mechanical
'Pointer → [i]' / 'Compare [i] vs [j]' steps, drops return.result, and the
final beat is a no-op scale on cell_0. These tests pin the pedagogy fixes:

- pointer + compare on an overlapping index chunk into ONE decision beat,
- window steps emit a persistent window-band shape (array family),
- an index return closes with a found climax beat (not_found on miss),
- the outro beat narrates the actual result next to the complexity badge.
"""

from app.models.animation_spec import (
    AlgorithmAnimation,
    AnimationStepSpec,
    Complexity,
    InitialState,
)
from app.services.animation_validator import AnimationValidator
from app.services.scene_planner import plan


def _spec(steps, array=(5, 1, 4), target=None, extra=None):
    return AlgorithmAnimation(
        algorithm="bubble-sort",
        visualization="array",
        initialState=InitialState(array=list(array), target=target, extra=extra or {}),
        steps=steps,
        complexity=Complexity(time="O(n)", space="O(1)"),
        title="Array Story",
    )


def _narrations(beats):
    return [b.get("narration") or "" for b in beats]


def test_pointer_compare_merge_into_single_decision_beat():
    beats = plan(
        _spec(
            [
                AnimationStepSpec(action="pointer", index=0),
                AnimationStepSpec(action="compare", indices=[0, 1]),
            ]
        )
    )
    assert len(beats) == 3  # intro + merged decision + outro
    assert beats[1]["narration"] == "Compare [0]=5 vs [1]=1"
    assert not any(n.startswith("Pointer") for n in _narrations(beats))


def test_non_overlapping_pointer_compare_stays_separate():
    beats = plan(
        _spec(
            [
                AnimationStepSpec(action="pointer", index=2),
                AnimationStepSpec(action="compare", indices=[0, 1]),
            ]
        )
    )
    assert len(beats) == 4  # intro + pointer + compare + outro
    assert any(n.startswith("Pointer") for n in _narrations(beats))


def test_window_beat_emits_persistent_band():
    beats = plan(_spec([AnimationStepSpec(action="window", low=1, high=2)]))
    beat = beats[1]
    bands = [s for s in beat["shapes"] if s["id"].startswith("window_band")]
    assert len(bands) == 1
    band = bands[0]
    assert band["type"] == "rect"
    assert band["width"] > 0 and band["height"] > 0
    # Band spans cells 1..2 (cell pitch is 100): it must cover the range
    # without swallowing the whole row.
    assert band["x"] > -400 and band["x"] < 400
    validated, reason = AnimationValidator().validate(
        {"title": "t", "data": {}, "steps": beats}
    )
    assert validated is not None, reason


def test_repeated_window_ranges_do_not_duplicate_band_ids():
    beats = plan(
        _spec(
            [
                AnimationStepSpec(action="window", low=0, high=1),
                AnimationStepSpec(action="window", low=1, high=2),
                AnimationStepSpec(action="window", low=1, high=2),
            ]
        )
    )
    ids = [s["id"] for b in beats for s in b["shapes"]]
    assert len(ids) == len(set(ids))
    validated, reason = AnimationValidator().validate(
        {"title": "t", "data": {}, "steps": beats}
    )
    assert validated is not None, reason


def test_found_beat_highlights_result_cell():
    beats = plan(
        _spec([AnimationStepSpec(action="found", index=2)], array=(5, 1, 4), target=4)
    )
    assert "Found 4 at [2]" in _narrations(beats)
    found = next(b for b in beats if "Found 4 at [2]" in (b.get("narration") or ""))
    targets = [op["target"] for op in found["motion"]]
    assert "cell_2" in targets
    validated, reason = AnimationValidator().validate(
        {"title": "t", "data": {}, "steps": beats}
    )
    assert validated is not None, reason


def test_not_found_beat_narrates_target():
    beats = plan(_spec([AnimationStepSpec(action="not_found")], target=9))
    assert any("9 not in array" in n for n in _narrations(beats))
    validated, reason = AnimationValidator().validate(
        {"title": "t", "data": {}, "steps": beats}
    )
    assert validated is not None, reason


def test_outro_narrates_result_with_badge():
    beats = plan(
        _spec(
            [AnimationStepSpec(action="compare", indices=[0, 1])],
            extra={"result": [1, 4, 5]},
        )
    )
    outro = beats[-1]
    assert "Result [1, 4, 5]" in (outro.get("narration") or "")
    assert outro.get("badge") == {"time": "O(n)", "space": "O(1)"}
