"""Issue #141 — animation quality gates (RED phase).

Covers the four backend quality gaps without touching the frontend renderer:
1. planner path validates for all non-array families
2. complexity resolves per-algo/family instead of O(n)/O(1) default
3. long traces downsample instead of hard-cutting the tail
4. semantic lint surfaces missing camera/badge/narration quality
"""

from app.models.animation_spec import (
    AlgorithmAnimation,
    AnimationStepSpec,
    Complexity,
    InitialState,
)
from app.services import scene_planner as planner
from app.services.animation_validator import AnimationValidator
from app.services.solution_animation_service import (
    SolutionAnimationService,
    resolve_complexity,
    downsample_steps,
)


def _spec(viz, steps, array=(5, 2, 8, 1, 3)):
    return AlgorithmAnimation(
        algorithm=f"test-{viz}",
        visualization=viz,  # type: ignore[arg-type]
        initialState=InitialState(array=list(array), extra={}),
        steps=steps,
        complexity=Complexity(time="O(n)", space="O(1)"),
        title=f"Test {viz}",
    )


def _visit_steps(n=3):
    return [AnimationStepSpec(action="visit", index=i) for i in range(n)]


class TestPlannerPathValidates:
    def _assert_valid(self, beats):
        validated, reason = AnimationValidator().validate(
            {"title": "T", "steps": beats}
        )
        assert validated is not None, reason

    def test_stack_planner_validates(self):
        spec = _spec(
            "stack",
            [
                AnimationStepSpec(action="push", values=[1]),
                AnimationStepSpec(action="push", values=[2]),
                AnimationStepSpec(action="pop", values=[2]),
            ],
        )
        self._assert_valid(planner.plan_stack(spec))

    def test_tree_planner_validates(self):
        spec = _spec("tree", _visit_steps(3))
        self._assert_valid(planner.plan_tree(spec))

    def test_graph_planner_validates(self):
        spec = _spec("graph", _visit_steps(3))
        self._assert_valid(planner.plan_graph(spec, "graph"))

    def test_intervals_planner_validates(self):
        spec = _spec("intervals", _visit_steps(3))
        self._assert_valid(planner.plan_intervals(spec))

    def test_backtrack_planner_validates(self):
        spec = _spec("backtrack", _visit_steps(3))
        self._assert_valid(planner.plan_backtrack(spec))


class TestComplexityResolution:
    def test_sorting_gets_nlogn_not_default(self):
        time_c, space_c = resolve_complexity({"family": "array"}, "merge_sort")
        assert time_c == "O(n log n)"

    def test_graph_bfs_gets_vertex_edge_complexity(self):
        time_c, _ = resolve_complexity({"family": "graph"}, "clone_graph")
        assert time_c == "O(V+E)"

    def test_entry_complexity_takes_precedence(self):
        entry = {"family": "array", "complexity": ("O(n)", "O(n)")}
        assert resolve_complexity(entry, "two_sum") == ("O(n)", "O(n)")

    def test_unknown_array_falls_back_to_family_default(self):
        time_c, space_c = resolve_complexity({"family": "array"}, "some_unknown_algo")
        assert time_c and space_c


class TestDownsampling:
    def test_long_trace_keeps_key_events(self):
        steps = [
            AnimationStepSpec(action="compare", indices=[0, 1]) for _ in range(200)
        ]
        steps.append(AnimationStepSpec(action="mark", index=0))
        capped = downsample_steps(steps, limit=96)
        assert len(capped) <= 96
        assert any(s.action == "mark" for s in capped)

    def test_service_cap_helper_exists(self):
        assert callable(downsample_steps)
        assert len(downsample_steps(_visit_steps(3), limit=96)) == 3


class TestSemanticLint:
    def test_lint_flags_missing_camera_and_badge(self):
        script = {
            "title": "T",
            "steps": [
                {"narration": "a", "shapes": [], "motion": []},
                {"narration": "a", "shapes": [], "motion": []},
                {"narration": "", "shapes": [], "motion": []},
            ],
        }
        warnings = AnimationValidator().lint_quality(script)
        assert any("camera" in w.lower() for w in warnings)
        assert any("badge" in w.lower() for w in warnings)
        assert any("narration" in w.lower() for w in warnings)

    def test_lint_quiet_on_cinematic_beats(self):
        beats = planner.plan_array(
            _spec(
                "array",
                [
                    AnimationStepSpec(action="compare", indices=[0, 1]),
                    AnimationStepSpec(action="swap", indices=[0, 1]),
                    AnimationStepSpec(action="mark", index=2),
                ],
                array=[3, 1, 2],
            )
        )
        warnings = AnimationValidator().lint_quality({"title": "T", "steps": beats})
        assert warnings == []

    def test_service_exposes_resolve_complexity(self):
        assert callable(SolutionAnimationService.resolve_complexity) or callable(
            resolve_complexity
        )
