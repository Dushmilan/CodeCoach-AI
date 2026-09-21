from app.models.animation_spec import (
    AlgorithmAnimation,
    AnimationStepSpec,
    Complexity,
    InitialState,
)
from app.services import scene_planner


def _spec():
    return AlgorithmAnimation(
        algorithm="bubble_sort",
        visualization="bars",
        initialState=InitialState(array=[5, 1, 4], extra={}),
        steps=[
            AnimationStepSpec(action="compare", indices=[0, 1]),
            AnimationStepSpec(action="swap", indices=[0, 1]),
            AnimationStepSpec(action="write", index=0, values=[1]),
        ],
        complexity=Complexity(time="O(n²)", space="O(1)"),
        title="Bubble Sort",
    )


def test_compare_narration_includes_values():
    beats = scene_planner.plan_array(_spec())
    assert "5" in beats[1]["narration"] and "1" in beats[1]["narration"]


def test_swap_narration_includes_indices_and_values():
    beats = scene_planner.plan_array(_spec())
    assert "[0]" in beats[2]["narration"] and "[1]" in beats[2]["narration"]


def test_every_focus_beat_has_camera_and_final_has_badge():
    beats = scene_planner.plan_array(_spec())
    assert beats[0].get("camera", {}).get("action") == "reset"
    assert beats[-1].get("badge") == {"time": "O(n²)", "space": "O(1)"}


def test_no_duplicate_consecutive_narrations():
    spec = _spec()
    spec.steps = [
        AnimationStepSpec(action="compare", indices=[0, 1]),
        AnimationStepSpec(action="compare", indices=[0, 1]),
        AnimationStepSpec(action="compare", indices=[0, 1]),
    ]
    beats = scene_planner.plan_array(spec)
    narrs = [b["narration"] for b in beats[1:-1]]
    assert len(set(narrs)) == len(narrs)


def _jump_game_spec():
    # #235: jump_game emits pointer/read/mark(active) per index. The planner
    # must render every event at its own cell — never a placeholder beat.
    return AlgorithmAnimation(
        algorithm="jump_game",
        visualization="array",
        initialState=InitialState(array=[2, 3, 1, 1, 4], extra={}),
        steps=[
            AnimationStepSpec(action="pointer", index=2),
            AnimationStepSpec(action="read", index=2),
            AnimationStepSpec(action="mark", index=2, label="active"),
            AnimationStepSpec(action="visit", index=3),
        ],
        complexity=Complexity(time="O(n)", space="O(1)"),
        title="Jump Game",
    )


def test_read_beat_highlights_event_cell_not_cell_0():
    beats = scene_planner.plan_array(_jump_game_spec())
    read_beats = [b for b in beats if "Read" in (b.get("narration") or "")]
    assert len(read_beats) == 1
    assert "[2]" in read_beats[0]["narration"]
    targets = [m["target"] for m in read_beats[0]["motion"]]
    assert "cell_2" in targets
    assert "cell_0" not in targets


def test_visit_beat_highlights_event_cell_not_cell_0():
    beats = scene_planner.plan_array(_jump_game_spec())
    visit_beats = [b for b in beats if "Visit" in (b.get("narration") or "")]
    assert len(visit_beats) == 1
    assert "[3]" in visit_beats[0]["narration"]
    assert "cell_3" in [m["target"] for m in visit_beats[0]["motion"]]
    assert "cell_0" not in [m["target"] for m in visit_beats[0]["motion"]]


def test_mark_narration_uses_event_state_not_sorted():
    beats = scene_planner.plan_array(_jump_game_spec())
    mark_beats = [b for b in beats if "Mark" in (b.get("narration") or "")]
    assert len(mark_beats) == 1
    assert "sorted" not in mark_beats[0]["narration"]
    assert "active" in mark_beats[0]["narration"]


def _tree_spec():
    return AlgorithmAnimation(
        algorithm="maximum_depth_of_binary_tree",
        visualization="tree",
        initialState=InitialState(array=[3, 9, 20, None, None, 15, 7], extra={}),
        steps=[
            AnimationStepSpec(action="visit", index=0),
            AnimationStepSpec(action="visit", index=0),
            AnimationStepSpec(action="visit", index=1),
        ],
        complexity=Complexity(time="O(n)", space="O(h)"),
        title="T",
    )


def _graph_spec():
    return AlgorithmAnimation(
        algorithm="clone_graph",
        visualization="graph",
        initialState=InitialState(array=[], extra={}),
        steps=[
            AnimationStepSpec(action="visit", index=0),
            AnimationStepSpec(action="visit", index=0),
            AnimationStepSpec(action="visit", index=1),
        ],
        complexity=Complexity(time="O(V+E)", space="O(V)"),
        title="T",
    )


def test_finalize_beats_applies_to_tree_path():
    beats = scene_planner.plan(_tree_spec())
    narrs = [b["narration"] for b in beats[1:-1]]
    assert len(set(narrs)) == len(narrs)
    assert beats[0].get("camera", {}).get("action") == "reset"
    assert beats[-1].get("badge") == {"time": "O(n)", "space": "O(h)"}


def test_finalize_beats_applies_to_graph_path():
    beats = scene_planner.plan(_graph_spec())
    narrs = [b["narration"] for b in beats[1:-1]]
    assert len(set(narrs)) == len(narrs)
    assert beats[0].get("camera", {}).get("action") == "reset"
    assert beats[-1].get("badge") == {"time": "O(V+E)", "space": "O(V)"}
