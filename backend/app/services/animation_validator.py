"""Structural gate for generic declarative animation scenes.

A scene is fully data-driven: the AI authors the subject AND the algorithm
visuals as vector primitives (shapes) plus a per-step motion timeline. There
are no algorithm-type or subject-kind catalogs — every scene is validated
against the same structural rules so a bad script can never reach the viewer.

The validator enforces the cross-cutting rules (bounds, uniqueness, caps,
motion-target resolution). Field-level shape typing is handled by the
AnimationScript Pydantic model downstream.
"""

import logging
import re
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

MAX_STEPS = 100
MAX_SHAPES = 120
MAX_SHAPES_PER_STEP = 40
MAX_MOTIONS_PER_STEP = 30
MAX_SHAPE_ID = 64
MAX_NARRATION = 300
MAX_TEXT_LENGTH = 200

MIN_STEPS = 3
MIN_SHAPES_TOTAL = 2

BOUND_X = 960.0  # canvas is 1920 wide, center origin
BOUND_Y = 540.0  # canvas is 1080 tall, center origin
BOUND_POINT = 2000.0  # relative vertex offsets from the node origin

MIN_DURATION = 0.1
MAX_DURATION = 5.0

SHAPE_TYPES = frozenset({"rect", "ellipse", "line", "polygon", "text"})
MOTION_OPS = frozenset(
    {
        "appear",
        "disappear",
        "move",
        "fill",
        "stroke",
        "scale",
        "rotate",
        "label",
    }
)
# Ops that change an existing shape's geometry/color/content — appearing or
# disappearing a shape is not animation by itself, so every step must include
# at least one of these.
TRANSFORM_OPS = frozenset({"move", "fill", "stroke", "scale", "rotate", "label"})

HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


class AnimationValidator:
    """Validate the structural correctness of an animation scene dict."""

    def validate(self, script: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str]:
        """Return (validated_script, "") on success or (None, reason) on failure."""
        if not isinstance(script, dict):
            return None, "Animation is not an object"

        steps = script.get("steps")
        if not isinstance(steps, list) or not steps:
            return None, "Animation must contain a non-empty steps list"
        if len(steps) > MAX_STEPS:
            return None, f"Too many steps ({len(steps)} > {MAX_STEPS})"

        known_ids: set[str] = set()
        total_shapes = 0
        no_transform_step: Optional[int] = None
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                return None, f"Step {i} is not an object"

            narration = step.get("narration")
            if narration is not None and (
                not isinstance(narration, str) or len(narration) > MAX_NARRATION
            ):
                return None, f"Step {i} narration must be under {MAX_NARRATION} chars"

            shapes = step.get("shapes") or []
            if not isinstance(shapes, list):
                return None, f"Step {i} shapes must be a list"
            if len(shapes) > MAX_SHAPES_PER_STEP:
                return (
                    None,
                    f"Step {i} has too many shapes "
                    f"({len(shapes)} > {MAX_SHAPES_PER_STEP})",
                )

            for j, shape in enumerate(shapes):
                if not isinstance(shape, dict):
                    return None, f"Step {i} shape {j} is not an object"
                ok, reason = self._validate_shape(shape, f"Step {i} shape {j}")
                if not ok:
                    return None, reason
                sid = shape.get("id")
                if not isinstance(sid, str) or not sid.strip():
                    return None, f"Step {i} shape {j} is missing an id"
                if len(sid) > MAX_SHAPE_ID:
                    return (
                        None,
                        f"Step {i} shape {j} id exceeds {MAX_SHAPE_ID} chars",
                    )
                if sid in known_ids:
                    return None, f"Duplicate shape id {sid!r}"
                known_ids.add(sid)

            total_shapes += len(shapes)

            motion = step.get("motion") or []
            if not isinstance(motion, list):
                return None, f"Step {i} motion must be a list"
            if not motion:
                return (
                    None,
                    f"Step {i} has no motion ops (every step must animate the "
                    "algorithm forward)",
                )
            if len(motion) > MAX_MOTIONS_PER_STEP:
                return (
                    None,
                    f"Step {i} has too many motion ops "
                    f"({len(motion)} > {MAX_MOTIONS_PER_STEP})",
                )

            for k, op in enumerate(motion):
                if not isinstance(op, dict):
                    return None, f"Step {i} motion {k} is not an object"
                ok, reason = self._validate_motion(
                    op, known_ids, f"Step {i} motion {k}"
                )
                if not ok:
                    return None, reason

            # The first step may legitimately set up the initial state by
            # appearing shapes, but every later step must visibly transform an
            # existing shape — fading shapes in/out is not animation. Record the
            # violation here and report it after the hard caps so a caps error
            # takes precedence.
            if (
                i > 0
                and no_transform_step is None
                and not any(op.get("op") in TRANSFORM_OPS for op in motion)
            ):
                no_transform_step = i

        if total_shapes > MAX_SHAPES:
            return None, f"Too many shapes ({total_shapes} > {MAX_SHAPES})"
        if total_shapes < MIN_SHAPES_TOTAL:
            return None, f"Too few shapes ({total_shapes} < {MIN_SHAPES_TOTAL})"
        if len(steps) < MIN_STEPS:
            return None, f"Too few steps ({len(steps)} < {MIN_STEPS})"
        if no_transform_step is not None:
            return (
                None,
                f"Step {no_transform_step} has no transform op "
                "(appearing/disappearing shapes is not animation — "
                "move/fill/stroke/scale/rotate an existing shape)",
            )

        return script, ""

    # ── internal ──────────────────────────────────────────────────────

    @staticmethod
    def _validate_shape(shape: Dict[str, Any], label: str) -> Tuple[bool, str]:
        kind = shape.get("type")
        if kind not in SHAPE_TYPES:
            return False, f"{label} has unsupported type {kind!r}"

        for field, bound in (("x", BOUND_X), ("y", BOUND_Y)):
            value = shape.get(field, 0)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return False, f"{label} {field} must be a number"
            if not -bound <= value <= bound:
                return False, f"{label} {field} out of range ({value!r})"

        if kind in ("rect", "ellipse"):
            if shape.get("width") is None or shape.get("height") is None:
                return False, f"{label} {kind} requires width and height"

        if kind in ("line", "polygon"):
            points = shape.get("points")
            if not isinstance(points, list) or len(points) < 2:
                return False, f"{label} {kind} requires at least 2 points"
            for point in points:
                if (
                    not isinstance(point, (list, tuple))
                    or len(point) != 2
                    or any(
                        isinstance(c, bool) or not isinstance(c, (int, float))
                        for c in point
                    )
                ):
                    return False, f"{label} has an invalid point {point!r}"
                if any(abs(c) > BOUND_POINT for c in point):
                    return False, f"{label} has an out-of-range point"

        if kind == "text":
            text = shape.get("text")
            if not isinstance(text, str) or not text.strip():
                return False, f"{label} text requires a non-empty text string"
            if len(text) > MAX_TEXT_LENGTH:
                return False, f"{label} text exceeds {MAX_TEXT_LENGTH} chars"

        for size_field in ("width", "height", "fontSize", "lineWidth"):
            value = shape.get(size_field)
            if value is None:
                continue
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or value <= 0
            ):
                return False, f"{label} {size_field} must be a positive number"

        radius = shape.get("radius")
        if radius is not None:
            if (
                isinstance(radius, bool)
                or not isinstance(radius, (int, float))
                or radius < 0
            ):
                return False, f"{label} radius must be a non-negative number"

        for color_field in ("fill", "stroke"):
            value = shape.get(color_field)
            if value is None:
                continue
            if not isinstance(value, str) or not HEX_COLOR.match(value):
                return False, f"{label} {color_field} must be a #rrggbb hex color"

        opacity = shape.get("opacity")
        if opacity is not None:
            if (
                isinstance(opacity, bool)
                or not isinstance(opacity, (int, float))
                or not 0 <= opacity <= 1
            ):
                return False, f"{label} opacity must be between 0 and 1"

        return True, ""

    @staticmethod
    def _validate_motion(
        op: Dict[str, Any], known_ids: set[str], label: str
    ) -> Tuple[bool, str]:
        op_name = op.get("op")
        if op_name not in MOTION_OPS:
            return False, f"{label} has unsupported op {op_name!r}"

        target = op.get("target")
        if not isinstance(target, str) or target not in known_ids:
            return False, f"{label} targets unknown shape id {target!r}"

        duration = op.get("duration", 0.3)
        if (
            isinstance(duration, bool)
            or not isinstance(duration, (int, float))
            or not MIN_DURATION <= duration <= MAX_DURATION
        ):
            return False, f"{label} duration out of range ({duration!r})"

        to = op.get("to")
        if op_name == "move":
            if (
                not isinstance(to, (list, tuple))
                or len(to) != 2
                or any(
                    isinstance(c, bool) or not isinstance(c, (int, float)) for c in to
                )
            ):
                return False, f"{label} move requires an [x, y] target"
            if abs(to[0]) > BOUND_X or abs(to[1]) > BOUND_Y:
                return False, f"{label} move target out of range"
        elif op_name in ("fill", "stroke"):
            if not isinstance(to, str) or not HEX_COLOR.match(to):
                return False, f"{label} {op_name} requires a #rrggbb hex color"
        elif op_name in ("scale", "rotate"):
            if isinstance(to, bool) or not isinstance(to, (int, float)):
                return False, f"{label} {op_name} requires a number"
            if op_name == "scale" and to <= 0:
                return False, f"{label} scale must be positive"
        elif op_name == "label":
            if not isinstance(to, str) or not to:
                return False, f"{label} label requires a non-empty text string"
            if len(to) > MAX_TEXT_LENGTH:
                return False, f"{label} label text exceeds {MAX_TEXT_LENGTH} chars"

        return True, ""


animation_validator = AnimationValidator()
