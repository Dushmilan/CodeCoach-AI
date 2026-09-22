"""#240: compiler-fallback beats must carry resolvable cameras + final badge.

The planner path ships per-beat focus/panTo cameras and an outro badge via
_finalize_beats. When the planner yields nothing, build_animation falls back
to compile_family — whose beats carry no camera and no badge, so the viewer
renders a dead static camera and no complexity badge. The fallback output
must meet the same bar: beat-0 reset, per-action-beat focus on the beat's
own (cumulatively resolvable) motion target, and a final-beat badge — with
the validator and the camera/badge lint staying green.
"""

import pytest

from app.ports.code_executor import ExecutionResult
from app.services.animation_validator import AnimationValidator
from app.services.solution_animation_service import SolutionAnimationService


class FakeExecutor:
    def __init__(self, result: ExecutionResult):
        self.result = result

    async def execute(self, language, code, stdin="", version=None):
        return self.result


STACK_STDOUT = "\n".join(
    [
        '{"event":"init","data":["(",")"],"family":"stack"}',
        '{"event":"push","value":"("}',
        '{"event":"return","result":true}',
    ]
)

STACK_QUESTION = {
    "id": "valid-parentheses",
    "title": "Valid Parentheses",
    "category": "Stack & Queue",
    "description": "Determine if the input string is valid.",
    "examples": [{"input": 's = "()"', "output": "true"}],
}


def _resolvable_camera(camera, known_ids) -> bool:
    action = (camera or {}).get("action")
    if action == "reset":
        return True
    if action not in ("focus", "panTo"):
        return False
    element = (camera or {}).get("element")
    if isinstance(element, str):
        return element in known_ids
    region = (camera or {}).get("region")
    if isinstance(region, list) and region:
        for entry in region:
            if isinstance(entry, (int, float)):
                if (
                    f"cell_{int(entry)}" in known_ids
                    or f"node_{int(entry)}" in known_ids
                ):
                    return True
            elif isinstance(entry, str) and entry in known_ids:
                return True
        return False
    return False


class TestFallbackBeatsCarryCamerasAndBadge:
    @pytest.mark.asyncio
    async def test_fallback_beats_have_resolvable_cameras_and_final_badge(self):
        service = SolutionAnimationService(
            FakeExecutor(ExecutionResult(stdout=STACK_STDOUT, stderr="", exit_code=0))
        )
        # Force the compiler fallback: the planner yields nothing.
        service._try_planner = lambda *a, **k: None  # type: ignore[method-assign]
        animation = await service.build_animation(STACK_QUESTION)
        assert animation is not None
        validated, reason = AnimationValidator().validate(animation)
        assert validated is not None, reason

        steps = animation["steps"]
        assert len(steps) >= 3
        known_ids: set = set()
        for i, step in enumerate(steps):
            for shape in step.get("shapes", []):
                if shape.get("id"):
                    known_ids.add(shape["id"])
            camera = step.get("camera")
            assert camera is not None, f"beat {i} has no camera (dead static view)"
            assert _resolvable_camera(camera, known_ids), (
                f"beat {i} camera {camera} resolves against nothing "
                f"(known: {sorted(known_ids)})"
            )
        assert steps[0].get("camera", {}).get("action") == "reset"

        badge = steps[-1].get("badge")
        assert isinstance(badge, dict), "final beat has no complexity badge"
        assert badge.get("time") and badge.get("space")

        warnings = AnimationValidator().lint_quality(animation)
        assert not any("camera" in w for w in warnings), warnings
        assert not any("badge" in w for w in warnings), warnings
