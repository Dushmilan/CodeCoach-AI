"""Unit tests for the generic scene animation schema + question input."""

from app.models.schemas import (
    AnimateRequest,
    AnimationScript,
    AnimationStep,
    MotionOp,
    QuestionInput,
    SceneShape,
)


class TestSceneShape:
    def test_rect_shape_round_trips(self):
        shape = SceneShape(
            id="cell_0",
            type="rect",
            x=-240,
            y=0,
            width=88,
            height=88,
            radius=12,
            fill="#1e293b",
            stroke="#334155",
        )
        assert shape.id == "cell_0"
        assert shape.type == "rect"
        assert shape.width == 88

    def test_text_shape_round_trips(self):
        shape = SceneShape(
            id="label",
            type="text",
            x=0,
            y=200,
            text="Two Sum",
            fontSize=28,
            fill="#e2e8f0",
        )
        assert shape.text == "Two Sum"
        assert shape.fontSize == 28

    def test_polygon_points_round_trips(self):
        shape = SceneShape(
            id="ptr",
            type="polygon",
            x=-240,
            y=-80,
            points=[[-12, -30], [0, -60], [12, -30]],
            fill="#facc15",
        )
        assert shape.points == [[-12, -30], [0, -60], [12, -30]]

    def test_opacity_is_bounded(self):
        SceneShape(id="a", type="rect", x=0, y=0, width=10, height=10, opacity=0.5)

    def test_invalid_color_rejected(self):
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SceneShape(id="a", type="rect", x=0, y=0, width=10, height=10, fill="red")


class TestMotionOp:
    def test_move_op_round_trips(self):
        op = MotionOp(target="cell_0", op="move", to=[120, -80], duration=0.35)
        assert op.op == "move"
        assert op.to == [120, -80]

    def test_duration_defaults(self):
        op = MotionOp(target="cell_0", op="appear")
        assert op.duration == 0.3


class TestAnimationStep:
    def test_shapes_and_motion_round_trip(self):
        step = AnimationStep(
            narration="Need 7 to reach 9.",
            shapes=[
                SceneShape(
                    id="cell_0",
                    type="rect",
                    x=-240,
                    y=0,
                    width=88,
                    height=88,
                    fill="#1e293b",
                )
            ],
            motion=[MotionOp(target="cell_0", op="appear")],
        )
        assert len(step.shapes) == 1
        assert len(step.motion) == 1
        assert step.shapes[0].id == "cell_0"

    def test_defaults_are_empty(self):
        step = AnimationStep(narration="x")
        assert step.shapes == []
        assert step.motion == []


class TestAnimationScript:
    def test_generic_scene_round_trips(self):
        script = AnimationScript(
            title="Two Sum",
            data={"values": [2, 7], "target": 9},
            steps=[AnimationStep(narration="start")],
        )
        assert script.title == "Two Sum"
        assert len(script.steps) == 1
        assert "steps" in script.model_dump()

    def test_defaults(self):
        script = AnimationScript()
        assert script.title == ""
        assert script.data == {}
        assert script.steps == []

    def test_old_typed_fields_are_ignored_gracefully(self):
        step = AnimationStep(operation="compare", index=0)
        assert step.shapes == []
        assert step.motion == []
        assert not hasattr(step, "operation")


class TestQuestionInput:
    def test_curated_subset_round_trips(self):
        q = QuestionInput(
            title="Two Sum",
            description="Find two numbers that add up to target.",
            category="hash_map",
            difficulty="medium",
            examples=[{"input": "[2,7,11,15], 9", "output": "[0,1]"}],
            test_cases=[{"input": "[3,3], 6", "output": "[0,1]"}],
            constraints=["1 <= n <= 1000"],
            starter={"python": "def two_sum(nums, target): pass"},
        )
        assert q.title == "Two Sum"
        assert q.starter["python"].startswith("def two_sum")

    def test_defaults(self):
        q = QuestionInput()
        assert q.examples == []
        assert q.test_cases == []
        assert q.constraints == []
        assert q.starter is None


class TestAnimateRequest:
    def test_question_is_optional(self):
        req = AnimateRequest(problem="P", code="c", language="python")
        assert req.question is None

    def test_question_is_accepted(self):
        req = AnimateRequest(
            problem="P",
            code="c",
            language="python",
            question=QuestionInput(title="Two Sum"),
        )
        assert req.question is not None
        assert req.question.title == "Two Sum"
