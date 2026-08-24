"""TDD red for Scene Planner — searching (binary search) beats."""

from app.models.animation_spec import AlgorithmAnimation, AnimationStepSpec, Complexity, InitialState
from app.services.scene_planner import plan_searching, plan


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


def test_plan_searching_beats_include_camera_and_hierarchy():
    spec = _binary_spec()
    beats = plan_searching(spec)
    # Beat 0 array appears + title + target
    assert len(beats) >= 8  # 1 intro + 6 steps + 1 complexity
    assert "Find 13" in beats[0]["narration"]
    assert beats[0]["camera"]["action"] == "reset"
    # set_bounds focuses region
    assert beats[1]["camera"]["action"] == "focus"
    assert beats[1]["camera"]["region"] == [0, 6]
    # inspect_mid highlights mid
    assert any(m["target"] == "cell_3" for m in beats[2]["motion"])
    # discard_left dims [0..3]
    assert any(m["target"] == "cell_0" for m in beats[3]["motion"])
    assert beats[3]["camera"]["action"] == "panTo"
    # found highlights success
    assert "Found 13" in beats[6]["narration"]


def test_plan_dispatch_sorted_array():
    spec = _binary_spec()
    beats = plan(spec)
    assert len(beats) > 0


def test_plan_empty_array_returns_empty():
    spec = AlgorithmAnimation(
        algorithm="binary-search",
        visualization="sorted-array",
        initialState=InitialState(array=[], target=1),
        steps=[AnimationStepSpec(action="set_bounds", low=0, high=0)],
        complexity=Complexity(time="O(log n)", space="O(1)"),
    )
    assert plan_searching(spec) == []
