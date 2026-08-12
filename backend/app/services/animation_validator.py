"""AnimationValidator — semantic gate for AI-generated animation scripts.

Structural conformance is handled by the AnimationScript Pydantic model.
This service verifies that a structurally valid script is also logically
correct: indexes stay in bounds, a "match" frame really matches the target,
and a "mismatch" frame really does not. Invalid scripts are dropped so the
rest of the coaching response still renders — never partially trusted.
"""

import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

SUPPORTED_TYPES = frozenset({"linear_search"})

MAX_VALUES = 50
MAX_STEPS = 200
MAX_NARRATION = 300

_INDEX_OPS = frozenset({"compare", "visit", "mark", "swap", "move"})
_RESULT_OPS = frozenset({"compare", "mark", "visit"})


class AnimationValidator:
    """Validate the semantic correctness of an animation script dict."""

    def validate(self, script: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str]:
        """Return (validated_script, "") on success or (None, reason) on failure."""
        if not isinstance(script, dict):
            return None, "Animation is not an object"

        kind = script.get("type")
        if kind not in SUPPORTED_TYPES:
            return None, f"Unsupported animation type: {kind!r}"

        data = script.get("data")
        if not isinstance(data, dict):
            return None, "Animation data must be an object"
        values = data.get("values")
        if not isinstance(values, list) or not values:
            return None, "Animation data must contain a non-empty values list"
        if len(values) > MAX_VALUES:
            return None, f"Too many values ({len(values)} > {MAX_VALUES})"

        steps = script.get("steps")
        if not isinstance(steps, list) or not steps:
            return None, "Animation must contain a non-empty steps list"
        if len(steps) > MAX_STEPS:
            return None, f"Too many steps ({len(steps)} > {MAX_STEPS})"

        validator = _TYPE_VALIDATORS.get(kind)
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                return None, f"Step {i} is not an object"
            ok, reason = self._validate_step(step, values, data, i)
            if not ok:
                return None, reason
            if validator:
                ok, reason = validator(step, values, data, i)
                if not ok:
                    return None, reason

        return script, ""

    # ── internal ──────────────────────────────────────────────────────

    def _validate_step(
        self,
        step: Dict[str, Any],
        values: list,
        data: Dict[str, Any],
        index: int,
    ) -> Tuple[bool, str]:
        op = step.get("operation")
        if not isinstance(op, str):
            return False, f"Step {index} is missing an operation"

        narration = step.get("narration")
        if not isinstance(narration, str) or not narration.strip():
            return False, f"Step {index} is missing narration"
        if len(narration) > MAX_NARRATION:
            return False, f"Step {index} narration exceeds {MAX_NARRATION} chars"

        bounds_ok, reason = self._check_bounds(step, len(values), f"Step {index}")
        if not bounds_ok:
            return False, reason

        if op in _RESULT_OPS:
            result = step.get("result")
            if op == "compare" and result not in (
                None,
                "checking",
                "match",
                "mismatch",
            ):
                return False, f"Step {index} has invalid compare result {result!r}"

        return True, ""

    @staticmethod
    def _check_bounds(
        step: Dict[str, Any], length: int, label: str
    ) -> Tuple[bool, str]:
        for field in ("index", "from_index", "to_index"):
            value = step.get(field)
            if value is None:
                continue
            if not isinstance(value, int) or value < 0 or value >= length:
                return False, f"{label} has out-of-bounds {field}: {value!r}"
        return True, ""

    @staticmethod
    def _validate_linear_search(
        step: Dict[str, Any],
        values: list,
        data: Dict[str, Any],
        index: int,
    ) -> Tuple[bool, str]:
        target = data.get("target")
        if step.get("operation") != "compare" or step.get("result") not in (
            "match",
            "mismatch",
        ):
            return True, ""

        value_index = step.get("index")
        if value_index is None:
            return False, f"Step {index} is missing an index for a compare result"
        value = values[value_index]
        if step["result"] == "match" and value != target:
            return False, (
                f"Step {index} claims a match but values[{step['index']}] "
                f"({value!r}) does not equal target ({target!r})"
            )
        if step["result"] == "mismatch" and value == target:
            return False, (
                f"Step {index} claims a mismatch but values[{step['index']}] "
                f"({value!r}) equals target ({target!r})"
            )
        return True, ""


_TYPE_VALIDATORS = {
    "linear_search": AnimationValidator._validate_linear_search,
}

animation_validator = AnimationValidator()
