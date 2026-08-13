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
from typing import Any, Dict, Optional

from fastapi import HTTPException

from app.ports.code_executor import CodeExecutor
from app.services.trace_instrumenter import wrap_traced_solution
from app.services.trace_parser import parse_trace
from app.services.animation_inputs import parse_input_kwargs
from app.services.family_compilers import compile_family
from app.services.animation_validator import AnimationValidator
from app.services.reference_solutions import (
    get_reference_solution,
    resolve_algorithm,
)

logger = logging.getLogger(__name__)


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

    @staticmethod
    def _example_input_value(question: Dict[str, Any]) -> Optional[Any]:
        """Return examples[0].input exactly as the user sees it."""
        examples = question.get("examples") or []
        if not examples or not isinstance(examples[0], dict):
            return None
        return examples[0].get("input")
