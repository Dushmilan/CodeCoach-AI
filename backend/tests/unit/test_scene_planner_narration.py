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
