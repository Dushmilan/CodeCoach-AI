"""Unit tests for AnimationValidator — the structural gate on generic scenes.

Covers: valid scenes, step/shape/motion caps, coordinate bounds, shape field
rules, hex colors, id uniqueness, motion-target resolution, and duration
bounds. Also covers the GroqService._validate_animation pipeline.
"""

from app.services.animation_validator import (
    AnimationValidator,
    MAX_MOTIONS_PER_STEP,
    MAX_SHAPES,
    MAX_SHAPES_PER_STEP,
    MAX_STEPS,
    animation_validator,
)


def _shape(**overrides):
    base = {
        "id": "cell_0",
        "type": "rect",
        "x": 0,
        "y": 0,
        "width": 88,
        "height": 88,
        "fill": "#1e293b",
        "stroke": "#334155",
    }
    base.update(overrides)
    return base


def _motion(**overrides):
    base = {"target": "cell_0", "op": "appear", "duration": 0.3}
    base.update(overrides)
    return base


def _scene(steps):
    return {"title": "Scene", "data": {}, "steps": steps}


def _step(shapes=None, motion=None, narration="checking"):
    return {
        "narration": narration,
        "shapes": shapes or [],
        "motion": motion or [],
    }


class TestValidScenes:
    def test_minimal_valid_scene(self):
        scene = _scene(
            [
                _step(
                    shapes=[_shape(), _shape(id="b", x=120)],
                    motion=[_motion(), _motion(target="b", op="appear")],
                ),
                _step(motion=[_motion(op="move", to=[100, 0])]),
                _step(motion=[_motion(target="b", op="fill", to="#22c55e")]),
            ]
        )
        validated, reason = animation_validator.validate(scene)
        assert validated is not None
        assert reason == ""

    def test_multi_step_timeline(self):
        scene = _scene(
            [
                _step(shapes=[_shape(id="a")], motion=[_motion(target="a")]),
                _step(
                    shapes=[_shape(id="b", x=100)],
                    motion=[
                        _motion(target="a", op="fill", to="#22c55e"),
                        _motion(target="b", op="move", to=[200, 0]),
                    ],
                ),
                _step(motion=[_motion(target="b", op="move", to=[300, 0])]),
            ]
        )
        validated, reason = animation_validator.validate(scene)
        assert validated is not None

    def test_polygon_and_line_shapes(self):
        scene = _scene(
            [
                _step(
                    shapes=[
                        {
                            "id": "poly",
                            "type": "polygon",
                            "x": 0,
                            "y": 0,
                            "points": [[-10, 0], [0, 20], [10, 0]],
                            "fill": "#facc15",
                        },
                        {
                            "id": "line",
                            "type": "line",
                            "x": 0,
                            "y": 0,
                            "points": [[-100, 0], [100, 0]],
                            "stroke": "#94a3b8",
                        },
                    ],
                    motion=[
                        _motion(target="poly", op="appear", duration=0.3),
                        _motion(target="line", op="appear", duration=0.3),
                    ],
                ),
                _step(motion=[_motion(target="poly", op="move", to=[50, 0])]),
                _step(motion=[_motion(target="line", op="rotate", to=45)]),
            ]
        )
        validated, reason = animation_validator.validate(scene)
        assert validated is not None

    def test_text_shape(self):
        scene = _scene(
            [
                _step(
                    shapes=[
                        {
                            "id": "txt",
                            "type": "text",
                            "x": 0,
                            "y": 200,
                            "text": "Two Sum",
                            "fontSize": 28,
                            "fill": "#e2e8f0",
                        },
                        _shape(id="box", x=-300, y=200),
                    ],
                    motion=[
                        _motion(target="txt", op="appear"),
                        _motion(target="box", op="appear"),
                    ],
                ),
                _step(motion=[_motion(target="txt", op="move", to=[0, 240])]),
                _step(motion=[_motion(target="box", op="fill", to="#22c55e")]),
            ]
        )
        validated, reason = animation_validator.validate(scene)
        assert validated is not None

    def test_motion_target_added_earlier_or_same_step(self):
        scene = _scene(
            [
                _step(
                    shapes=[_shape(id="a"), _shape(id="b", x=120)],
                    motion=[_motion(target="a"), _motion(target="b", op="appear")],
                ),
                _step(motion=[_motion(target="a", op="move", to=[50, 0])]),
                _step(motion=[_motion(target="b", op="fill", to="#22c55e")]),
            ]
        )
        validated, reason = animation_validator.validate(scene)
        assert validated is not None


class TestRejections:
    def test_not_an_object(self):
        validated, reason = animation_validator.validate("scene")
        assert validated is None
        assert "not an object" in reason

    def test_empty_steps(self):
        validated, reason = animation_validator.validate(_scene([]))
        assert validated is None
        assert "non-empty steps" in reason

    def test_missing_steps(self):
        validated, reason = animation_validator.validate({"title": "x"})
        assert validated is None
        assert "steps" in reason

    def test_too_many_steps(self):
        steps = [_step(shapes=[_shape(id=f"c{i}")]) for i in range(MAX_STEPS + 1)]
        validated, reason = animation_validator.validate(_scene(steps))
        assert validated is None
        assert "Too many steps" in reason

    def test_too_many_shapes_total(self):
        steps = []
        for i in range(0, MAX_SHAPES + 1, MAX_SHAPES_PER_STEP):
            batch = [_shape(id=f"c{i + j}") for j in range(MAX_SHAPES_PER_STEP)]
            steps.append(_step(shapes=batch, motion=[_motion(target=f"c{i}")]))
        validated, reason = animation_validator.validate(_scene(steps))
        assert validated is None
        assert "Too many shapes" in reason

    def test_too_many_shapes_per_step(self):
        shapes = [_shape(id=f"c{i}") for i in range(MAX_SHAPES_PER_STEP + 1)]
        validated, reason = animation_validator.validate(
            _scene([_step(shapes=shapes, motion=[_motion(target="c0")])])
        )
        assert validated is None
        assert "too many shapes" in reason

    def test_too_many_motions_per_step(self):
        motions = [_motion() for _ in range(MAX_MOTIONS_PER_STEP + 1)]
        validated, reason = animation_validator.validate(
            _scene([_step(shapes=[_shape()], motion=motions)])
        )
        assert validated is None
        assert "too many motion ops" in reason

    def test_unsupported_shape_type(self):
        scene = _scene([_step(shapes=[_shape(type="spaceship")])])
        validated, reason = animation_validator.validate(scene)
        assert validated is None
        assert "unsupported type" in reason

    def test_rect_requires_width_and_height(self):
        shape = _shape(width=None, height=None)
        validated, reason = animation_validator.validate(
            _scene([_step(shapes=[shape])])
        )
        assert validated is None
        assert "requires width and height" in reason

    def test_out_of_range_x(self):
        shape = _shape(x=2000)
        validated, reason = animation_validator.validate(
            _scene([_step(shapes=[shape])])
        )
        assert validated is None
        assert "out of range" in reason

    def test_out_of_range_y(self):
        shape = _shape(y=-600)
        validated, reason = animation_validator.validate(
            _scene([_step(shapes=[shape])])
        )
        assert validated is None
        assert "out of range" in reason

    def test_non_numeric_size(self):
        shape = _shape(width="big")
        validated, reason = animation_validator.validate(
            _scene([_step(shapes=[shape])])
        )
        assert validated is None
        assert "positive number" in reason

    def test_non_positive_font_size(self):
        shape = {
            "id": "txt",
            "type": "text",
            "x": 0,
            "y": 0,
            "text": "hi",
            "fontSize": 0,
        }
        validated, reason = animation_validator.validate(
            _scene([_step(shapes=[shape])])
        )
        assert validated is None
        assert "positive number" in reason

    def test_invalid_color(self):
        shape = _shape(fill="red")
        validated, reason = animation_validator.validate(
            _scene([_step(shapes=[shape])])
        )
        assert validated is None
        assert "hex color" in reason

    def test_invalid_opacity(self):
        shape = _shape(opacity=3)
        validated, reason = animation_validator.validate(
            _scene([_step(shapes=[shape])])
        )
        assert validated is None
        assert "opacity" in reason

    def test_duplicate_shape_ids(self):
        scene = _scene(
            [
                _step(shapes=[_shape(id="dup"), _shape(id="dup", x=100)]),
            ]
        )
        validated, reason = animation_validator.validate(scene)
        assert validated is None
        assert "Duplicate" in reason

    def test_duplicate_ids_across_steps(self):
        scene = _scene(
            [
                _step(shapes=[_shape(id="dup")], motion=[_motion(target="dup")]),
                _step(shapes=[_shape(id="dup", x=100)]),
            ]
        )
        validated, reason = animation_validator.validate(scene)
        assert validated is None
        assert "Duplicate" in reason

    def test_missing_shape_id(self):
        shape = _shape()
        del shape["id"]
        validated, reason = animation_validator.validate(
            _scene([_step(shapes=[shape])])
        )
        assert validated is None
        assert "missing an id" in reason

    def test_unsupported_motion_op(self):
        scene = _scene([_step(shapes=[_shape()], motion=[_motion(op="explode")])])
        validated, reason = animation_validator.validate(scene)
        assert validated is None
        assert "unsupported op" in reason

    def test_motion_targets_unknown_shape(self):
        scene = _scene([_step(motion=[_motion(target="nope")])])
        validated, reason = animation_validator.validate(scene)
        assert validated is None
        assert "unknown shape id" in reason

    def test_motion_duration_too_long(self):
        scene = _scene([_step(shapes=[_shape()], motion=[_motion(duration=10)])])
        validated, reason = animation_validator.validate(scene)
        assert validated is None
        assert "duration" in reason

    def test_move_requires_xy_target(self):
        scene = _scene(
            [
                _step(
                    shapes=[_shape()],
                    motion=[_motion(op="move", to=[0, 0, 0])],
                )
            ]
        )
        validated, reason = animation_validator.validate(scene)
        assert validated is None
        assert "move requires" in reason

    def test_move_target_out_of_range(self):
        scene = _scene(
            [
                _step(
                    shapes=[_shape()],
                    motion=[_motion(op="move", to=[2000, 0])],
                )
            ]
        )
        validated, reason = animation_validator.validate(scene)
        assert validated is None
        assert "out of range" in reason

    def test_fill_requires_hex_color(self):
        scene = _scene(
            [
                _step(
                    shapes=[_shape()],
                    motion=[_motion(op="fill", to="green")],
                )
            ]
        )
        validated, reason = animation_validator.validate(scene)
        assert validated is None
        assert "hex color" in reason

    def test_scale_must_be_positive(self):
        scene = _scene(
            [
                _step(
                    shapes=[_shape()],
                    motion=[_motion(op="scale", to=0)],
                )
            ]
        )
        validated, reason = animation_validator.validate(scene)
        assert validated is None
        assert "scale" in reason

    def test_narration_too_long(self):
        scene = _scene([_step(narration="x" * 301)])
        validated, reason = animation_validator.validate(scene)
        assert validated is None
        assert "narration" in reason

    def test_too_few_steps(self):
        scene = _scene(
            [
                _step(
                    shapes=[_shape(), _shape(id="b", x=120)],
                    motion=[_motion(), _motion(target="b", op="appear")],
                ),
            ]
        )
        validated, reason = animation_validator.validate(scene)
        assert validated is None
        assert "Too few steps" in reason

    def test_too_few_shapes_total(self):
        scene = _scene(
            [
                _step(shapes=[_shape()], motion=[_motion()]),
                _step(motion=[_motion(op="move", to=[100, 0])]),
                _step(motion=[_motion(op="fill", to="#22c55e")]),
            ]
        )
        validated, reason = animation_validator.validate(scene)
        assert validated is None
        assert "Too few shapes" in reason

    def test_step_without_motion_rejected(self):
        scene = _scene(
            [
                _step(shapes=[_shape()], motion=[_motion()]),
                _step(shapes=[_shape(id="b", x=100)]),
                _step(motion=[_motion(target="b", op="move", to=[100, 0])]),
            ]
        )
        validated, reason = animation_validator.validate(scene)
        assert validated is None
        assert "no motion" in reason

    def test_appear_only_step_rejected(self):
        """Fading shapes in is not an animation — every step must transform
        an existing shape (move/fill/stroke/scale/rotate)."""
        scene = _scene(
            [
                _step(
                    shapes=[_shape(), _shape(id="b", x=120)],
                    motion=[_motion(), _motion(target="b", op="appear")],
                ),
                _step(
                    shapes=[_shape(id="c", x=240)],
                    motion=[_motion(target="c", op="appear")],
                ),
                _step(
                    shapes=[_shape(id="d", x=360)],
                    motion=[_motion(target="d", op="appear")],
                ),
            ]
        )
        validated, reason = animation_validator.validate(scene)
        assert validated is None
        assert "transform" in reason

    def test_disappear_only_step_rejected(self):
        scene = _scene(
            [
                _step(
                    shapes=[_shape(), _shape(id="b", x=120)],
                    motion=[_motion(), _motion(target="b", op="appear")],
                ),
                _step(
                    motion=[
                        _motion(target="b", op="move", to=[200, 0]),
                        _motion(target="cell_0", op="disappear"),
                    ]
                ),
                _step(
                    motion=[_motion(target="b", op="disappear")],
                ),
            ]
        )
        validated, reason = animation_validator.validate(scene)
        assert validated is None
        assert "transform" in reason

    def test_label_op_counts_as_transform(self):
        """Changing a shape's content is a real visual change — it satisfies
        the per-step transform rule the same way move/fill/scale do."""
        scene = _scene(
            [
                _step(
                    shapes=[_shape(), _shape(id="b", x=120)],
                    motion=[_motion(), _motion(target="b", op="appear")],
                ),
                _step(
                    motion=[
                        _motion(target="b", op="label", to="9"),
                        _motion(target="b", op="fill", to="#22c55e"),
                    ]
                ),
                _step(motion=[_motion(target="cell_0", op="move", to=[100, 0])]),
            ]
        )
        validated, reason = animation_validator.validate(scene)
        assert validated is not None

    def test_label_op_requires_to(self):
        scene = _scene(
            [
                _step(shapes=[_shape()], motion=[_motion()]),
                _step(motion=[_motion(op="label")]),
                _step(motion=[_motion(op="move", to=[50, 0])]),
            ]
        )
        validated, reason = animation_validator.validate(scene)
        assert validated is None
        assert "to" in reason or "label" in reason


class TestGroqIntegration:
    def test_valid_animation_is_kept(self):
        from app.services.groq_service import GroqService

        data = {
            "summary": "Keep coaching",
            "hints": [],
            "animation": _scene(
                [
                    _step(shapes=[_shape(id="a")], motion=[_motion(target="a")]),
                    _step(
                        shapes=[_shape(id="b", x=100)],
                        motion=[
                            _motion(target="b"),
                            _motion(target="a", op="fill", to="#22c55e"),
                        ],
                    ),
                    _step(motion=[_motion(target="b", op="move", to=[200, 0])]),
                ]
            ),
        }
        result = GroqService._validate_animation(data)
        assert "animation" in result
        assert result["animation"]["title"] == "Scene"

    def test_legacy_typed_animation_is_dropped(self):
        from app.services.groq_service import GroqService

        data = {
            "summary": "Keep coaching",
            "hints": [],
            "animation": {
                "type": "linear_search",
                "title": "Searching for 4",
                "steps": [{"operation": "compare", "index": 0, "narration": "x"}],
            },
        }
        result = GroqService._validate_animation(data)
        assert "animation" not in result
        assert result["summary"] == "Keep coaching"

    def test_legacy_operation_steps_dropped_without_type(self):
        from app.services.groq_service import GroqService

        data = {
            "summary": "Keep coaching",
            "hints": [],
            "animation": {
                "title": "Your code vs the solution",
                "steps": [{"operation": "compare_code", "narration": "x"}],
            },
        }
        result = GroqService._validate_animation(data)
        assert "animation" not in result
        assert result["summary"] == "Keep coaching"

    def test_invalid_animation_is_dropped(self):
        from app.services.groq_service import GroqService

        data = {
            "summary": "Keep coaching",
            "hints": [],
            "animation": {
                "title": "broken",
                "steps": [{"narration": "x", "shapes": [_shape(x=5000)]}],
            },
        }
        result = GroqService._validate_animation(data)
        assert "animation" not in result
        assert result["summary"] == "Keep coaching"

    def test_animation_absent_is_untouched(self):
        from app.services.groq_service import GroqService

        data = {"summary": "plain", "hints": []}
        result = GroqService._validate_animation(data)
        assert result == data

    def test_validator_raising_is_swallowed(self):
        from unittest.mock import patch

        from app.services.groq_service import GroqService

        data = {
            "summary": "Keep coaching",
            "hints": [],
            "animation": _scene([_step(shapes=[_shape()])]),
        }
        with patch(
            "app.services.animation_validator.AnimationValidator.validate",
            side_effect=RuntimeError("boom"),
        ):
            result = GroqService._validate_animation(data)
        assert "animation" not in result
        assert result["summary"] == "Keep coaching"


class TestValidatorInstance:
    def test_module_level_singleton(self):
        assert isinstance(animation_validator, AnimationValidator)
