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
from app.services.trace_instrumenter import (
    display_code_and_map,
    wrap_traced_solution,
)
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
from app.services import animation_design_tokens as tokens
from app.services import scene_planner
from app.services.animation_pacing import apply_pacing
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
    "merge_sort": ("O(n log n)", "O(n)"),
    "quick_sort": ("O(n log n)", "O(log n)"),
    "two_sum": ("O(n)", "O(n)"),
    "clone_graph": ("O(V+E)", "O(V)"),
    "course_schedule": ("O(V+E)", "O(V)"),
    "number_of_islands": ("O(m*n)", "O(m*n)"),
    "coin_change": ("O(n*amount)", "O(amount)"),
    "climbing_stairs": ("O(n)", "O(1)"),
}

_COMPLEXITY_BY_FAMILY = {
    "array": ("O(n)", "O(1)"),
    "backtrack": ("O(2^n)", "O(n)"),
    "stack": ("O(n)", "O(n)"),
    "linked_list": ("O(n)", "O(1)"),
    "tree": ("O(n)", "O(h)"),
    "graph": ("O(V+E)", "O(V)"),
    "grid": ("O(m*n)", "O(m*n)"),
    "intervals": ("O(n log n)", "O(n)"),
}

# Compressible trace actions are sampled; everything else is always kept.
_DOWNSAMPLE_KEEP = frozenset(
    {
        "swap",
        "write",
        "mark",
        "found",
        "not_found",
        "dp_update",
        "partition",
        "edge",
        "choose",
        "backtrack",
        "push",
        "pop",
    }
)


def resolve_complexity(entry: Dict[str, Any], algorithm: str) -> tuple:
    """Resolve (time, space) preferring catalog entry, then algo, then family."""
    complexity = (entry or {}).get("complexity")
    if isinstance(complexity, (list, tuple)) and len(complexity) == 2:
        return (str(complexity[0]), str(complexity[1]))
    if algorithm in _COMPLEXITY_BY_ALGO:
        return _COMPLEXITY_BY_ALGO[algorithm]
    family = (entry or {}).get("family", "")
    return _COMPLEXITY_BY_FAMILY.get(family, ("O(n)", "O(1)"))


def downsample_steps(steps: list, limit: int = 96) -> list:
    """Cap semantic steps preserving key events and original order.

    The story skeleton is always kept: the first intro beat and the last
    outro beat survive even when key events alone exceed the limit.
    """
    if limit <= 0:
        return []
    if len(steps) <= limit:
        return list(steps)
    key = [s for s in steps if getattr(s, "action", None) in _DOWNSAMPLE_KEEP]
    if len(key) >= limit:
        keep = key[:limit]
    else:
        others = [
            s for s in steps if getattr(s, "action", None) not in _DOWNSAMPLE_KEEP
        ]
        budget = limit - len(key)
        stride = max(1.0, len(others) / max(budget, 1))
        sampled_ids = {
            id(s)
            for s in (
                others[round(i * stride)]
                for i in range(budget)
                if round(i * stride) < len(others)
            )
        }
        key_ids = {id(s) for s in key}
        keep = [s for s in steps if id(s) in key_ids or id(s) in sampled_ids]
    keep_ids = {id(s) for s in keep} | {id(steps[0]), id(steps[-1])}
    ordered = [s for s in steps if id(s) in keep_ids]
    if len(ordered) <= limit:
        return ordered
    return ordered[: limit - 1] + [steps[-1]]


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


def _translate_search_events(
    events, values=None, target=None
) -> List[AnimationStepSpec]:
    """Translate a binary-search trace into search-region semantics.

    The reference solution traces ``pointer`` (low/high/mid) + ``compare``
    + ``mark`` (match) events, which ``plan_searching`` does not understand
    (#243). Every emitted step is derived from observed trace state only:

    - ``set_bounds`` when the [low..high] region changes (seen at compare),
    - ``inspect_mid`` for each compared mid index,
    - ``discard_left``/``discard_right`` when the next iteration's bound
      moves past mid (``until`` matches the planner's dim ranges),
    - ``found`` on a match mark, ``not_found`` when the stream ends
      without one (honoring an explicit ``return`` result when present).

    The loop's final bound change is never traced (pointers emit at loop
    top only), so on a miss the closing discard is derived from the data
    itself (``values[mid]`` vs ``target`` — the same comparison the
    algorithm performed). It is skipped whenever the data is unavailable
    or incomparable, never invented.
    """
    steps: List[AnimationStepSpec] = []
    low: Optional[int] = None
    high: Optional[int] = None
    emitted_bounds: Optional[tuple] = None
    compared_bounds: Optional[tuple] = None
    pending_mid: Optional[int] = None
    found = False
    return_result = None

    def _bounds() -> Optional[tuple]:
        if low is None or high is None:
            return None
        return (low, high)

    for e in events:
        if e.kind == "init":
            continue
        if e.kind == "pointer" and e.fields.get("name") in ("low", "high", "mid"):
            if e.fields["name"] == "low":
                low = int(e.fields["index"])
            elif e.fields["name"] == "high":
                high = int(e.fields["index"])
            bounds = _bounds()
            if (
                pending_mid is not None
                and bounds is not None
                and compared_bounds is not None
                and bounds != compared_bounds
            ):
                prev_low, prev_high = compared_bounds
                if low is not None and low > prev_low:
                    steps.append(
                        AnimationStepSpec(
                            action="discard_left", index=pending_mid, until=low
                        )
                    )
                if high is not None and high < prev_high:
                    steps.append(
                        AnimationStepSpec(
                            action="discard_right",
                            index=pending_mid,
                            until=high + 1,
                        )
                    )
                compared_bounds = bounds
                pending_mid = None
            continue
        if e.kind == "compare" and e.has("i"):
            mid = int(e.fields["i"])
            bounds = _bounds()
            if bounds is not None and bounds != emitted_bounds:
                steps.append(
                    AnimationStepSpec(
                        action="set_bounds", low=bounds[0], high=bounds[1]
                    )
                )
                emitted_bounds = bounds
            steps.append(
                AnimationStepSpec(action="inspect_mid", index=mid, annotation=e.intent)
            )
            pending_mid = mid
            compared_bounds = bounds
            continue
        if e.kind == "mark" and e.has("i"):
            if e.fields.get("state") == "match":
                steps.append(
                    AnimationStepSpec(action="found", index=int(e.fields["i"]))
                )
                found = True
            continue
        if e.kind == "return":
            return_result = e.fields.get("result")
            continue
        # Any other event kind keeps the generic 1:1 mapping.
        action = _EVENT_TO_ACTION.get(e.kind, "custom")
        kwargs: Dict[str, Any] = {"action": action}
        if e.has("i"):
            kwargs["index"] = int(e.fields["i"])
        steps.append(AnimationStepSpec(**kwargs))

    if not found:
        if isinstance(return_result, int) and return_result >= 0:
            steps.append(AnimationStepSpec(action="found", index=return_result))
            return steps
        _append_terminal_discard(steps, values, target, pending_mid)
        steps.append(AnimationStepSpec(action="not_found"))
    return steps


def _append_terminal_discard(steps, values, target, pending_mid) -> None:
    """Emit the untraced closing discard of a missed binary search.

    Derived from the data (values[mid] vs target), never invented: when
    the loop exits, the side the algorithm discarded last is exactly the
    side the comparison ruled out. Skips silently without usable data.
    """
    if pending_mid is None or not isinstance(values, list) or target is None:
        return
    if not 0 <= pending_mid < len(values):
        return
    try:
        mid_value = values[pending_mid]
        if mid_value is None:
            return
        if mid_value < target:
            steps.append(
                AnimationStepSpec(
                    action="discard_left", index=pending_mid, until=pending_mid + 1
                )
            )
        elif mid_value > target:
            steps.append(
                AnimationStepSpec(
                    action="discard_right", index=pending_mid, until=pending_mid
                )
            )
    except TypeError:
        return


class SolutionAnimationService:
    """Generate algorithm animations from the canonical solution trace."""

    resolve_complexity = staticmethod(resolve_complexity)

    def __init__(self, executor: CodeExecutor):
        self.executor = executor
        self._validator = AnimationValidator()

    def _log_quality(self, algorithm: str, animation: Dict[str, Any]) -> None:
        for warning in self._validator.lint_quality(animation):
            logger.warning("Animation quality (%s): %s", algorithm, warning)

    @staticmethod
    def _attach_display_code(animation: Dict[str, Any], code: str) -> None:
        """Ship the stripped display code and remap beats onto it (#284).

        Trace lines address the canonical solution with ``__trace(...)``
        statements interleaved; the pane shows ``display_code_and_map``'s
        stripped copy, so each beat's ``code_line`` is rewritten through
        the original→display map. Lines outside the map (wrapper-level,
        never displayable) are dropped — honest absence over a wrong
        highlight. Beats without ``code_line`` are untouched. The beat's
        ``annotation`` (#287) is text, not a line: it passes through
        unchanged.
        """
        display_code, line_map = display_code_and_map(code)
        animation["animated_code"] = display_code
        for beat in animation.get("steps") or []:
            if not isinstance(beat, dict):
                continue
            line = beat.get("code_line")
            if not isinstance(line, int) or isinstance(line, bool):
                continue
            mapped = line_map.get(line)
            if mapped is None:
                beat.pop("code_line", None)
            else:
                beat["code_line"] = mapped

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

        planner_animation = self._try_planner(
            events, entry, algorithm, fallback_title, target=kwargs.get("target")
        )
        if planner_animation is not None:
            # #284: ship the instrument-free display code and remap every
            # beat's line onto it before validation, so the validated
            # payload is exactly what the viewer receives.
            self._attach_display_code(planner_animation, entry["code"])
            # #285 boundary: consume transient pacing roles where beats are
            # finalized so an unfinalized planner path can never leak
            # `role` past validation into the renderer output. No-op when
            # the planner already ran apply_pacing (roles stripped there).
            # A payload without a steps list is left untouched so the
            # validator rejects it and the pipeline degrades to fallback.
            steps = planner_animation.get("steps")
            if isinstance(steps, list):
                planner_animation["steps"] = apply_pacing(steps)
            validated, reason = self._validator.validate(planner_animation)
            if validated is not None:
                self._log_quality(algorithm, validated)
                return validated
            logger.warning(
                "Planner animation for %s failed validation: %s", algorithm, reason
            )

        animation = compile_family(entry["family"], events, title=fallback_title)
        if animation is None:
            logger.warning("Animation for %s could not be compiled", algorithm)
            return None

        animation = self._enrich_fallback_animation(animation, entry, algorithm)
        # #284: the family-compiler fallback is still build_animation's
        # output — ship the same instrument-free display code the dual-pane
        # viewer renders. Fallback beats carry no traced line, so their
        # code_line stays absent (null in the payload).
        self._attach_display_code(animation, entry["code"])
        validated, reason = self._validator.validate(animation)
        if validated is None:
            logger.warning(
                "Compiled animation for %s failed validation: %s", algorithm, reason
            )
            return None
        self._log_quality(algorithm, validated)
        return validated

    def _enrich_fallback_animation(
        self,
        animation: Dict[str, Any],
        entry: Dict[str, Any],
        algorithm: str,
    ) -> Dict[str, Any]:
        """Give compiler-fallback beats the planner path's camera guarantees.

        Family compilers emit shapes + motion only — no camera, no badge —
        so the viewer holds a dead static frame with no complexity badge.
        Attach beat-0 reset, per-action-beat focus on the beat's own first
        motion target, and the final-beat complexity badge. The focus target
        is always one of the beat's motion targets, which the validator
        resolves against cumulative shape ids — so the camera can never
        point at nothing. Idempotent: never overwrites an existing camera
        or badge. No motion/shapes are added, so validator caps are
        unaffected.
        """
        steps = animation.get("steps")
        if not isinstance(steps, list) or not steps:
            return animation
        if isinstance(steps[0], dict) and "camera" not in steps[0]:
            steps[0]["camera"] = {
                "action": "reset",
                "zoom": tokens.CAMERA["zoom_full"],
            }
        for step in steps[1:]:
            if not isinstance(step, dict) or "camera" in step:
                continue
            target = next(
                (
                    m.get("target")
                    for m in (step.get("motion") or [])
                    if isinstance(m, dict)
                    and isinstance(m.get("target"), str)
                    and m.get("target")
                ),
                None,
            )
            if target is not None:
                step["camera"] = {
                    "action": "focus",
                    "element": target,
                    "zoom": tokens.CAMERA["zoom_focus"],
                }
        last = steps[-1]
        if isinstance(last, dict) and "badge" not in last:
            time_c, space_c = resolve_complexity(entry, algorithm)
            last["badge"] = {"time": time_c, "space": space_c}
        return animation

    def _try_planner(
        self,
        events,
        entry: Dict[str, Any],
        algorithm: str,
        title: str,
        target: Any = None,
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
            time_c, space_c = resolve_complexity(entry, algorithm)
            steps: List[AnimationStepSpec] = []
            return_result: Any = None
            last_match_index: Optional[int] = None
            for e in events:
                if e.kind == "init":
                    continue
                if e.kind == "return":
                    # #240: the return value closes the story — an index
                    # result becomes a found climax beat (replacing a
                    # trailing mark(match) on the same cell), -1 with a
                    # known target becomes not_found, and anything else
                    # rides the outro beat via extra. Binary search owns
                    # its return via _translate_search_events.
                    return_result = e.fields.get("result")
                    if algorithm != "binary_search":
                        if (
                            isinstance(return_result, int)
                            and not isinstance(return_result, bool)
                            and 0 <= return_result < len(values)
                        ):
                            if (
                                steps
                                and steps[-1].action == "mark"
                                and last_match_index == return_result
                            ):
                                # The climax replaces the mark beat on the
                                # same cell — inherit its line so the
                                # highlight never drops at the peak (#284),
                                # and its annotation so the "why" never
                                # drops either (#287).
                                replaced = steps.pop()
                                steps.append(
                                    AnimationStepSpec(
                                        action="found",
                                        index=return_result,
                                        line=replaced.line,
                                        annotation=replaced.annotation,
                                    )
                                )
                            else:
                                steps.append(
                                    AnimationStepSpec(
                                        action="found", index=return_result
                                    )
                                )
                        elif return_result == -1 and target is not None:
                            steps.append(AnimationStepSpec(action="not_found"))
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
                    elif e.has("index"):
                        # Pointer events carry the scan position in `index`
                        # (trace schema), not `i` — without this every
                        # pointer beat clamps to cell 0 (#153).
                        kwargs["index"] = int(e.fields["index"])
                    if e.has("value"):
                        kwargs["values"] = [e.fields["value"]]
                    if e.kind == "mark" and e.has("state"):
                        # The mark state ("active", "match", ...) is the
                        # semantic — without it the planner can only guess
                        # (it hardcoded "sorted", #235).
                        kwargs["label"] = str(e.fields["state"])[:120]
                        if e.fields["state"] == "match" and e.has("i"):
                            last_match_index = int(e.fields["i"])
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
                if e.line is not None:
                    # #284: the beat this step becomes highlights the trace
                    # call's own line in the dual-pane viewer.
                    kwargs["line"] = e.line
                if e.intent is not None:
                    # #287: the beat this step becomes shows the real causal
                    # intent ("why") as its annotation — parsed intent is
                    # already a non-empty string capped at 200 chars.
                    kwargs["annotation"] = e.intent
                steps.append(AnimationStepSpec(**kwargs))
            if algorithm == "binary_search":
                # #243: generic pointer/compare/mark actions render as
                # placeholder beats in plan_searching — translate the trace
                # into search-region semantics instead. Falls back to the
                # generic steps if translation yields nothing.
                steps = (
                    _translate_search_events(events, values=values, target=target)
                    or steps
                )
            if not steps:
                return None
            steps = downsample_steps(steps, limit=96)
            spec = AlgorithmAnimation(
                algorithm=algorithm,
                visualization=viz,  # type: ignore[arg-type]
                initialState=InitialState(
                    array=values,
                    target=target,
                    extra={"result": return_result}
                    if return_result is not None
                    else {},
                ),
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
