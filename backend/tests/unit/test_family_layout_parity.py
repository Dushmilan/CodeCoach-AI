from app.models.animation_spec import (
    AlgorithmAnimation,
    AnimationStepSpec,
    Complexity,
    InitialState,
)
from app.services import scene_planner


def _beats(viz, steps):
    spec = AlgorithmAnimation(
        algorithm="x",
        visualization=viz,
        initialState=InitialState(array=[1, 2, 3], extra={}),
        steps=[AnimationStepSpec(action=a) for a in steps],
        complexity=Complexity(time="O(n)", space="O(1)"),
        title="T",
    )
    return scene_planner.plan(spec)


def test_tree_beats_use_level_layout_and_camera_badge():
    beats = _beats("tree", ["visit", "choose", "backtrack"])
    assert len(beats) >= 3
    assert beats[0].get("camera", {}).get("action") == "reset"
    assert beats[-1].get("badge") is not None
    xs = [s["x"] for b in beats for s in b["shapes"] if "x" in s]
    assert len(set(xs)) > 1  # not all stacked at same x


def test_graph_beats_spread_nodes():
    beats = _beats("graph", ["visit", "edge", "visit"])
    xs = [s["x"] for b in beats for s in b["shapes"] if "x" in s]
    assert len(set(xs)) > 1


def test_linked_list_intro_stays_within_validator_caps_and_bounds():
    spec = AlgorithmAnimation(
        algorithm="x",
        visualization="linked_list",
        initialState=InitialState(array=list(range(100)), extra={}),
        steps=[AnimationStepSpec(action="visit", index=0)],
        complexity=Complexity(time="O(n)", space="O(1)"),
        title="T",
    )
    beats = scene_planner.plan(spec)
    intro = beats[0]
    assert len(intro["shapes"]) <= 40
    assert len(intro["motion"]) <= 30
    assert all(
        abs(s.get("x", 0)) <= 960 and abs(s.get("y", 0)) <= 540 for s in intro["shapes"]
    )


def test_intervals_beats_use_scaled_bars_with_visit_mark():
    spec = AlgorithmAnimation(
        algorithm="merge_intervals",
        visualization="intervals",
        initialState=InitialState(array=[[1, 3], [2, 6], [8, 10]], extra={}),
        steps=[
            AnimationStepSpec(action="visit", index=0),
            AnimationStepSpec(action="mark", index=0),
            AnimationStepSpec(action="visit", index=1),
            AnimationStepSpec(action="mark", index=1),
        ],
        complexity=Complexity(time="O(n log n)", space="O(n)"),
        title="T",
    )
    beats = scene_planner.plan(spec)
    assert len(beats) >= 3
    bars = [
        s
        for s in beats[0]["shapes"]
        if s["id"].startswith("bar_") and s.get("type") == "rect"
    ]
    assert len(bars) >= 2
    assert len({s["x"] for s in bars}) > 1  # scaled positions, not stacked
    assert len({s["width"] for s in bars}) > 1  # scaled widths, not uniform
    assert all(abs(s["x"]) <= 960 and abs(s["y"]) <= 540 for s in beats[0]["shapes"])
    assert beats[0].get("camera", {}).get("action") == "reset"
    assert beats[-1].get("badge") is not None


def test_intervals_without_pairs_still_renders_beats():
    spec = AlgorithmAnimation(
        algorithm="merge_intervals",
        visualization="intervals",
        initialState=InitialState(array=[], extra={}),
        steps=[
            AnimationStepSpec(action="visit", index=0),
            AnimationStepSpec(action="mark", index=0),
        ],
        complexity=Complexity(time="O(n log n)", space="O(n)"),
        title="T",
    )
    beats = scene_planner.plan(spec)
    assert len(beats) >= 3
    assert beats[0].get("camera", {}).get("action") == "reset"
    assert beats[-1].get("badge") is not None
