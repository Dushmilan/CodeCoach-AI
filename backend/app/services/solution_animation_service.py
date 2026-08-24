"""SolutionAnimationService — orchestrates the canonical-solution animation.

Pipeline: question → resolve catalog algorithm (exact id first, keywords as
fallback) → normalize the first public example's input into the canonical
function's kwargs → wrap the canonical optimal solution with the __trace
harness → execute it in the sandbox → parse the JSON-array trace → compile it
with the family compiler into a validated generic AnimationScript.

The user's typed code is never used, inspected, or compared: the animation is
always of the intended optimal solution for the question, exactly as decided.
Any unusable input (no question, unknown algorithm, no examples, failed
execution, empty trace, un-compilable scene) returns None so the endpoint
degrades gracefully.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from app.ports.code_executor import CodeExecutor
from app.services.trace_instrumenter import wrap_traced_solution
from app.services.trace_parser import parse_trace
from app.services.animation_inputs import parse_input_kwargs
from app.services.family_compilers import compile_family
from app.services.animation_validator import AnimationValidator
from app.models.animation_spec import (
    AlgorithmAnimation,
    AnimationStepSpec,
    Complexity,
    InitialState,
)
from app.services import scene_planner
from app.services.reference_solutions import (
    get_reference_solution,
    resolve_algorithm,
)

logger = logging.getLogger(__name__)

_FAMILY_TO_VIZ = {
    "array": "array",
    "backtrack": "backtrack",
    "stack": "stack",
    "linked_list": "linked_list",
    "tree": "tree",
    "graph": "graph",
    "grid": "grid",
    "intervals": "intervals",
}

_COMPLEXITY_BY_ALGO = {
    "binary_search": ("O(log n)", "O(1)"),
    "bubble_sort": ("O(n²)", "O(1)"),
    "linear_search": ("O(n)", "O(1)"),
}

_EVENT_TO_ACTION = {
    "compare": "compare",
    "swap": "swap",
    "write": "write",
    "pointer": "pointer",
    "mark": "mark",
    "read": "read",
    "push": "push",
    "pop": "pop",
    "visit": "visit",
    "choose": "choose",
    "backtrack": "backtrack",
    "window": "window",
    "partition": "partition",
    "edge": "edge",
    "dp_update": "dp_update",
}


class SolutionAnimationService:
    """Generate algorithm animations from the canonical solution trace."""

    def __init__(self, executor: CodeExecutor):
        self.executor = executor
        self._validator = AnimationValidator()

    async def build_animation(
        self,
        question: Optional[Dict[str, Any]],
        title: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Return a validated AnimationScript for the question, or None."""
        if not isinstance(question, dict):
            return None

        algorithm = resolve_algorithm(question)
        entry = get_reference_solution(algorithm)
        if entry is None:
            return None

        raw_input = self._example_input_value(question)
        if raw_input is None:
            return None

        kwargs = parse_input_kwargs(raw_input, entry["signature"])
        if not kwargs:
            logger.warning("Animation input for %s produced no kwargs", algorithm)
            return None

        code = wrap_traced_solution(entry["code"], entry["function"])
        try:
            result = await self.executor.execute(
                language="python",
                code=code,
                stdin=json.dumps(kwargs, separators=(",", ":")),
            )
        except HTTPException as exc:  # Piston unavailable / bad request
            logger.warning(
                "Animation execution failed for %s: %s", algorithm, exc.detail
            )
            return None

        if result.exit_code != 0:
            logger.warning(
                "Animation trace run failed (%s) stderr=%.200r",
                algorithm,
                (result.stderr or "")[:200],
            )
            return None

        try:
            events = parse_trace(result.stdout or "")
        except ValueError as exc:
            # A structurally invalid known event indicates an instrumentation
            # bug, not a user-input problem; degrade to None instead of letting
            # the trace typo turn into a 500 or an unnecessary LLM fallback.
            logger.warning("Animation trace for %s was malformed: %s", algorithm, exc)
            return None
        if not events:
            logger.warning("Animation trace for %s produced no events", algorithm)
            return None

        fallback_title = (
            title or entry.get("title") or algorithm.replace("_", " ").title()
        )

        planner_animation = self._try_planner(events, entry, algorithm, fallback_title)
        if planner_animation is not None:
            validated, reason = self._validator.validate(planner_animation)
            if validated is not None:
                return validated
            logger.warning(
                "Planner animation for %s failed validation: %s", algorithm, reason
            )

        animation = compile_family(entry["family"], events, title=fallback_title)
        if animation is None:
            logger.warning("Animation for %s could not be compiled", algorithm)
            return None

        validated, reason = self._validator.validate(animation)
        if validated is None:
            logger.warning(
                "Compiled animation for %s failed validation: %s", algorithm, reason
            )
            return None
        return validated

    def _try_planner(
        self, events, entry: Dict[str, Any], algorithm: str, title: str
    ) -> Optional[Dict[str, Any]]:
        try:
            init = next((e for e in events if e.kind == "init"), None)
            if init is None:
                return None
            values = list(init.fields.get("values") or [])
            viz = _FAMILY_TO_VIZ.get(entry["family"], "array")
            if algorithm == "binary_search":
                viz = "sorted-array"
            elif entry["family"] == "array" and algorithm in ("bubble_sort",):
                viz = "bars"
            time_c, space_c = _COMPLEXITY_BY_ALGO.get(algorithm, ("O(n)", "O(1)"))
            steps: List[AnimationStepSpec] = []
            for e in events:
                if e.kind in ("init", "return"):
                    continue
                action = _EVENT_TO_ACTION.get(e.kind, "custom")
                kwargs: Dict[str, Any] = {"action": action}
                if e.kind in ("compare", "swap"):
                    idxs = []
                    if e.has("i"):
                        idxs.append(int(e.fields["i"]))
                    if e.has("j"):
                        idxs.append(int(e.fields["j"]))
                    if idxs:
                        kwargs["indices"] = idxs
                    if e.has("i"):
                        kwargs["index"] = int(e.fields["i"])
                elif e.kind in (
                    "write",
                    "mark",
                    "read",
                    "visit",
                    "choose",
                    "backtrack",
                    "pointer",
                    "partition",
                ):
                    if e.has("i"):
                        kwargs["index"] = int(e.fields["i"])
                    if e.has("value"):
                        kwargs["values"] = [e.fields["value"]]
                elif e.kind == "window":
                    if e.has("l"):
                        kwargs["low"] = int(e.fields["l"])
                    if e.has("r"):
                        kwargs["high"] = int(e.fields["r"])
                elif e.kind == "edge":
                    idxs = []
                    if e.has("a"):
                        idxs.append(int(e.fields["a"]))
                    if e.has("b"):
                        idxs.append(int(e.fields["b"]))
                    if idxs:
                        kwargs["indices"] = idxs
                elif e.kind == "push":
                    if e.has("value"):
                        kwargs["values"] = [e.fields["value"]]
                elif e.kind == "pop":
                    if e.has("value"):
                        kwargs["values"] = [e.fields["value"]]
                steps.append(AnimationStepSpec(**kwargs))
            if not steps:
                return None
            if len(steps) > 96:
                steps = steps[:96]
            spec = AlgorithmAnimation(
                algorithm=algorithm,
                visualization=viz,  # type: ignore[arg-type]
                initialState=InitialState(array=values, extra={}),
                steps=steps,
                complexity=Complexity(time=time_c, space=space_c),
                title=title,
            )
            beats = scene_planner.plan(spec)
            if not beats or len(beats) < 3:
                return None
            return {
                "title": title,
                "data": {"family": entry["family"], "values": values},
                "steps": beats,
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("Planner for %s failed: %s", algorithm, exc)
            return None

    @staticmethod
    def _example_input_value(question: Dict[str, Any]) -> Optional[Any]:
        """Return examples[0].input exactly as the user sees it."""
        examples = question.get("examples") or []
        if not examples or not isinstance(examples[0], dict):
            return None
        return examples[0].get("input")
