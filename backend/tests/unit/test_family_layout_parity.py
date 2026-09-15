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
