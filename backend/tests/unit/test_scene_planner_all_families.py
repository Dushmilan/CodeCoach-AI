"""Coverage for all 8 families — every algo dispatch returns cinematic beats."""

from app.models.animation_spec import (
    AlgorithmAnimation,
    AnimationStepSpec,
    Complexity,
    InitialState,
)
from app.services import scene_planner as planner


def _spec(viz, steps, array=[5, 2, 8, 1, 3], target=None):
    return AlgorithmAnimation(
        algorithm=f"test-{viz}",
        visualization=viz,
        initialState=InitialState(array=array, target=target, extra={}),
        steps=steps,
        complexity=Complexity(time="O(n)", space="O(1)"),
        title=f"Test {viz}",
    )


def test_array_bars_sorting_beats():
    spec = _spec(
        "bars",
        [
            AnimationStepSpec(action="compare", indices=[0, 1]),
            AnimationStepSpec(action="swap", indices=[0, 1]),
            AnimationStepSpec(action="mark", index=4),
            AnimationStepSpec(action="window", low=0, high=2),
        ],
        array=[5, 2, 8],
    )
    beats = planner.plan(spec)
    assert len(beats) >= 5  # intro + 4 steps + badge
    assert any("Compare" in b["narration"] for b in beats)
    assert any("Swap" in b["narration"] for b in beats)


def test_array_dp_write_and_partition():
    spec = _spec(
        "array",
        [
            AnimationStepSpec(action="write", index=2, values=[9]),
            AnimationStepSpec(action="partition", index=3),
        ],
        array=[1, 2, 3],
    )
    beats = planner.plan_array(spec)
    assert any(m["op"] == "label" for b in beats for m in b["motion"])
    assert any("Partition" in b["narration"] for b in beats)


def test_stack_push_pop():
    spec = _spec(
        "stack",
        [
            AnimationStepSpec(action="push", values=[1]),
            AnimationStepSpec(action="push", values=[2]),
            AnimationStepSpec(action="pop", values=[2]),
        ],
    )
    beats = planner.plan_stack(spec)
    assert any("Push" in b["narration"] for b in beats)
    assert any("Pop" in b["narration"] for b in beats)


def test_linked_list_visit():
    spec = _spec(
        "linked_list",
        [
            AnimationStepSpec(action="visit", index=0),
            AnimationStepSpec(action="pointer", index=2),
        ],
        array=[1, 2, 3, 4],
    )
    beats = planner.plan_linked_list(spec)
    assert any("Visit node" in b["narration"] for b in beats)
    assert any("Pointer" in b["narration"] for b in beats)


def test_tree_backtrack():
    spec = _spec(
        "tree",
        [
            AnimationStepSpec(action="visit", index=0),
            AnimationStepSpec(action="choose", index=1),
            AnimationStepSpec(action="backtrack", index=1),
        ],
    )
    beats = planner.plan_tree(spec)
    assert any("Visit" in b["narration"] for b in beats)
    assert any("Backtrack" in b["narration"] for b in beats)


def test_graph_edge_visit():
    spec = _spec(
        "graph",
        [
            AnimationStepSpec(action="visit", index=0),
            AnimationStepSpec(action="edge", indices=[0, 1]),
            AnimationStepSpec(action="visit", index=1),
        ],
    )
    beats = planner.plan_graph(spec, "graph")
    assert any("Edge" in b["narration"] for b in beats)


def test_grid_visit():
    spec = _spec("grid", [AnimationStepSpec(action="visit", index=5)], array=[0] * 9)
    beats = planner.plan_graph(spec, "grid")
    assert len(beats) >= 3


def test_intervals():
    spec = _spec(
        "intervals",
        [
            AnimationStepSpec(action="partition", indices=[0, 2]),
            AnimationStepSpec(action="visit", index=1),
        ],
    )
    beats = planner.plan_intervals(spec)
    assert any("partition" in b["narration"].lower() for b in beats)


def test_backtrack_choose_backtrack():
    spec = _spec(
        "backtrack",
        [
            AnimationStepSpec(action="choose", index=0),
            AnimationStepSpec(action="choose", index=1),
            AnimationStepSpec(action="backtrack", index=1),
        ],
    )
    beats = planner.plan_backtrack(spec)
    assert any("Choose" in b["narration"] for b in beats)
    assert any("Backtrack" in b["narration"] for b in beats)


def test_dispatch_covers_all_visualizations():
    for viz in [
        "sorted-array",
        "bars",
        "array",
        "stack",
        "queue",
        "linked_list",
        "tree",
        "graph",
        "grid",
        "intervals",
        "backtrack",
    ]:
        spec = _spec(viz, [AnimationStepSpec(action="visit", index=0)])
        beats = planner.plan(spec)
        assert len(beats) >= 3, f"{viz} returned {len(beats)} beats"
        assert beats[0].get("camera", {}).get("action") == "reset"
        assert beats[-1].get("badge") is not None
