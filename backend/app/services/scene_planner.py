"""Scene Planner — semantic AlgorithmAnimation steps → cinematic SceneBeats.

Beats are generic AnimationScript steps (narration/shapes/motion) planned with
visual hierarchy: ARRAY APPEARS → MID ENTERS → RELATION → DISCARD → CAMERA
FOCUS → NEXT. Planner decides pacing; Design System decides look.

Now covers all 8 families (array/sorted-array/bars, stack, linked_list, tree,
graph, grid, intervals, backtrack) → all 103 canonical solutions. Each planner
is cinematic (highlight/dim/camera/badges) not literal debugger steps.
"""

import json
import math
from typing import Any, Dict, List, Optional

from app.models.animation_spec import (
    AlgorithmAnimation,
    AnimationStepSpec,
    Complexity,
)
from app.services import animation_design_tokens as tokens
from app.services.animation_pacing import apply_pacing


def _is_climax_narration(narration: Any) -> bool:
    """Climax = the Aha! reveal beat (#285): found / base case / final return.

    Matches the narrations planners actually emit for the reveal: bare or
    prefixed ``found`` (``Found 13 at [4]``), ``result`` reveals
    (``Result [2]=7``), the ``mark(state="match")`` close
    (``Mark [2]=7 match`` / bare ``match``), and trace labels carrying
    ``base case`` / ``return``. Compared lower-cased; every other middle
    beat defaults to the rhythmic loop role. The dedupe pass appends
    ``" (cont.)"`` to repeated narrations, so the base narration is
    matched — a second finalize pass must re-tag the same roles.
    """
    text = str(narration or "").strip().lower()
    text = text.split(" (cont.", 1)[0].strip()
    return (
        text.startswith("found")
        or text.startswith("result")
        or text == "match"
        or text.endswith(" match")
        or "base case" in text
        or "return" in text
    )


def _finalize_beats(
    beats: List[Dict[str, Any]], complexity: Complexity
) -> List[Dict[str, Any]]:
    """Shared post-pass so ALL families get A2 pedagogy guarantees.

    Dedupe consecutive narrations with a repeat counter (A2 precedent),
    ensure the intro beat carries camera.reset, and ensure the final beat
    carries the complexity badge. Then tag each beat with its transient
    pacing role (#285) — intro = first, outro = badge beat, climax = the
    reveal, loop = everything else — and run ``apply_pacing``, which
    rewrites motion durations by role (clamped to 0.1-5.0s) and strips
    ``role`` so it never leaves the planner. A pre-existing ``role`` is
    honored, never overwritten. Idempotent — safe to apply over beats
    that already went through a per-family post-pass.
    """
    if not beats:
        return beats
    prev_base = None
    repeat = 0
    for b in beats[1:-1]:
        base = b.get("narration", "")
        if base == prev_base:
            repeat += 1
            suffix = " (cont.)" if repeat == 1 else f" (cont. {repeat})"
            b["narration"] = (base + suffix)[:300]
        else:
            repeat = 0
        prev_base = base
    if "camera" not in beats[0]:
        beats[0]["camera"] = {
            "action": "reset",
            "zoom": tokens.CAMERA["zoom_full"],
        }
    if "badge" not in beats[-1]:
        beats[-1]["badge"] = {
            "time": complexity.time,
            "space": complexity.space,
        }
    beats[0].setdefault("role", "intro")
    beats[-1].setdefault("role", "outro")
    for b in beats[1:-1]:
        if "role" in b:
            continue
        b["role"] = "climax" if _is_climax_narration(b.get("narration")) else "loop"
    return apply_pacing(beats)


def _cell_x(index: int, n: int, cell: float = 88.0, gap: float = 12.0) -> float:
    total = n * cell + (n - 1) * gap
    start = -total / 2 + cell / 2
    return round(start + index * (cell + gap), 2)


def _label_text(value: Any) -> str:
    """Visible label for a cell value.

    Whitespace-only values (e.g. the space in a char array) render as ␣ so
    the text shape passes validation — blank text is rejected.
    """
    text = str(value)[: tokens.MAX_LABEL]
    return text if text.strip() else "␣"


def _root_shape(sid: str, w: float = 140.0, h: float = 48.0) -> Dict[str, Any]:
    """Container shape so the intro beat's appear target validates."""
    return {
        "id": sid,
        "type": "rect",
        "x": 0.0,
        "y": 220.0,
        "width": w,
        "height": h,
        "radius": 10,
        "fill": tokens.PALETTE["idle_fill"],
        "stroke": tokens.PALETTE["idle_stroke"],
        "lineWidth": 2,
    }


def _item_shape(sid: str, x: float = 0.0, y: float = 0.0) -> Dict[str, Any]:
    """Generic item shape for dynamically referenced ids (stack/tree/graph)."""
    return {
        "id": sid,
        "type": "rect",
        "x": round(x, 2),
        "y": round(y, 2),
        "width": 64.0,
        "height": 44.0,
        "radius": 8,
        "fill": tokens.PALETTE["idle_fill"],
        "stroke": tokens.PALETTE["idle_stroke"],
        "lineWidth": 2,
    }


def _ensure_graph_node(
    known: set,
    shapes: List[Dict[str, Any]],
    sid: str,
    idx: int,
    positions: List[Dict[str, float]],
) -> None:
    if sid not in known:
        pos = positions[max(0, min(int(idx), len(positions) - 1))]
        shapes.append(_item_shape(sid, x=pos["x"], y=pos["y"]))
        known.add(sid)


def _graph_edge_shape(
    sid: str,
    a_pos: Dict[str, float],
    b_pos: Dict[str, float],
) -> Dict[str, Any]:
    return {
        "id": sid,
        "type": "line",
        "points": [[a_pos["x"], a_pos["y"]], [b_pos["x"], b_pos["y"]]],
        "stroke": tokens.PALETTE["idle_stroke"],
        "lineWidth": 2,
    }


# ── searching (binary search hero template) ──────────────────────────────────


def plan_searching(spec: AlgorithmAnimation) -> List[Dict[str, Any]]:
    """Binary-search beats with camera + typography hierarchy."""
    arr = list(spec.initialState.array or [])
    n = len(arr)
    if n == 0:
        return []
    target = spec.initialState.target
    title = spec.title or spec.algorithm.replace("-", " ").title()
    shapes: List[Dict[str, Any]] = []
    motion: List[Dict[str, Any]] = []
    for i, v in enumerate(arr):
        x = _cell_x(i, n)
        shapes.append(
            {
                "id": f"cell_{i}",
                "type": "rect",
                "x": x,
                "y": tokens.ROW_Y,
                "width": 88,
                "height": 88,
                "radius": 10,
                "fill": tokens.PALETTE["idle_fill"],
                "stroke": tokens.PALETTE["idle_stroke"],
                "lineWidth": 2,
            }
        )
        shapes.append(
            {
                "id": f"val_{i}",
                "type": "text",
                "x": x,
                "y": tokens.ROW_Y,
                "text": _label_text(v),
                "fontSize": tokens.CELL_LABEL_SIZE,
                "fill": tokens.PALETTE["text"],
            }
        )
        motion.append(
            {
                "target": f"cell_{i}",
                "op": "appear",
                "duration": tokens.DURATION["enter"],
            }
        )
        motion.append(
            {"target": f"val_{i}", "op": "appear", "duration": tokens.DURATION["enter"]}
        )
    beats: List[Dict[str, Any]] = [
        {
            "narration": f"{title} — Find {target} in {arr}"[:300],
            "shapes": shapes,
            "motion": motion,
            "camera": {"action": "reset", "zoom": tokens.CAMERA["zoom_full"]},
        }
    ]
    for step in spec.steps:
        m: List[Dict[str, Any]] = []
        camera: Dict[str, Any] | None = None
        narr = ""
        if step.action == "set_bounds":
            low, high = step.low or 0, step.high or (n - 1)
            camera = {
                "action": "focus",
                "region": [low, high],
                "zoom": tokens.CAMERA["zoom_focus"],
            }
            for idx in range(low, min(high + 1, n)):
                m.append(
                    {
                        "target": f"cell_{idx}",
                        "op": "stroke",
                        "to": tokens.PALETTE["accent"],
                        "duration": tokens.DURATION["highlight"],
                    }
                )
            narr = f"Search region [{low}..{high}]"
        elif step.action == "inspect_mid":
            idx = max(0, min(int(step.index or 0), n - 1))
            m.append(
                {
                    "target": f"cell_{idx}",
                    "op": "fill",
                    "to": tokens.PALETTE["highlight_fill"],
                    "duration": tokens.DURATION["highlight"],
                }
            )
            m.append(
                {
                    "target": f"cell_{idx}",
                    "op": "stroke",
                    "to": tokens.PALETTE["highlight_stroke"],
                    "duration": tokens.DURATION["highlight"],
                }
            )
            camera = {
                "action": "focus",
                "element": f"cell_{idx}",
                "zoom": tokens.CAMERA["zoom_focus"],
            }
            narr = f"Inspect mid [{idx}] = {arr[idx]}"
        elif step.action in ("discard_left", "discard_right"):
            until = int(step.until if step.until is not None else 0)
            if step.action == "discard_left":
                rng = range(0, min(until, n))
                narr = (
                    f"{target} > {arr[step.index]} — discard left, search right →"
                    if step.index is not None
                    else "Discard left →"
                )
            else:
                rng = range(max(until, 0), n)
                narr = (
                    f"{target} < {arr[step.index]} — discard right ←"
                    if step.index is not None
                    else "Discard right ←"
                )
            for idx in rng:
                m.append(
                    {
                        "target": f"cell_{idx}",
                        "op": "fill",
                        "to": tokens.PALETTE["dim_fill"],
                        "duration": tokens.DURATION["dim"],
                    }
                )
                m.append(
                    {
                        "target": f"cell_{idx}",
                        "op": "stroke",
                        "to": tokens.PALETTE["dim_stroke"],
                        "duration": tokens.DURATION["dim"],
                    }
                )
            camera = {
                "action": "panTo",
                "region": [until, n - 1]
                if step.action == "discard_left"
                else [0, until - 1],
            }
        elif step.action == "found":
            idx = max(0, min(int(step.index or 0), n - 1))
            m.append(
                {
                    "target": f"cell_{idx}",
                    "op": "fill",
                    "to": tokens.PALETTE["success_fill"],
                    "duration": tokens.DURATION["highlight"],
                }
            )
            m.append(
                {
                    "target": f"cell_{idx}",
                    "op": "stroke",
                    "to": tokens.PALETTE["success_stroke"],
                    "duration": tokens.DURATION["highlight"],
                }
            )
            narr = f"Found {target} at [{idx}]"
        elif step.action == "not_found":
            narr = f"{target} not in array"
            m.append({"target": "cell_0", "op": "scale", "to": 1.0, "duration": 0.25})
        else:
            m.append({"target": "cell_0", "op": "scale", "to": 1.0, "duration": 0.25})
            narr = step.label or step.action
        beat: Dict[str, Any] = {"narration": narr[:300], "shapes": [], "motion": m}
        if camera:
            beat["camera"] = camera
        beats.append(beat)
    beats.append(
        {
            "narration": f"Complexity {spec.complexity.time} time, {spec.complexity.space} space"[
                :300
            ],
            "shapes": [],
            "motion": [
                {"target": "cell_0", "op": "scale", "to": 1.0, "duration": 0.25}
            ],
            "badge": {"time": spec.complexity.time, "space": spec.complexity.space},
        }
    )
    return beats


# ── generic array / bars (sorting, DP, two-pointers, sliding window) ─────────


def _compare_indices(step: AnimationStepSpec) -> List[int]:
    """Indices a compare step inspects, mirroring the planner branch."""
    if step.indices:
        return list(step.indices)
    if step.index is not None:
        return [step.index]
    return []


def _chunk_decision_steps(
    steps: List[AnimationStepSpec],
) -> List[Any]:
    """Chunk pointer+compare pairs into single decision beats (#240).

    A pointer step immediately followed by a compare over an overlapping
    index is one decision, not two beats — the mechanical 'Pointer → [i]'
    beat disappears and the compare beat carries the pointer's stroke.
    Non-overlapping pairs stay separate: a distant pointer is independent
    information, never merged.
    """
    chunked: List[Any] = []
    i = 0
    while i < len(steps):
        step = steps[i]
        nxt = steps[i + 1] if i + 1 < len(steps) else None
        if (
            step.action == "pointer"
            and nxt is not None
            and nxt.action == "compare"
            and step.index is not None
            and step.index in _compare_indices(nxt)
        ):
            chunked.append((step, nxt))
            i += 2
        else:
            chunked.append(step)
            i += 1
    return chunked


def _compare_narration(idxs: List[int], display: List[Any]) -> str:
    """Value-bearing compare narration shared by compare and decision beats."""
    n = len(display)
    if len(idxs) >= 2:
        vals = [str(display[i])[:12] if 0 <= i < n else "?" for i in idxs[:2]]
        return (
            f"Compare [{idxs[0]}]={vals[0]} "
            f"vs [{idxs[1]}]={vals[1] if len(vals) > 1 else '?'}"
        )
    if len(idxs) == 1:
        i0 = idxs[0]
        v0 = str(display[i0])[:12] if 0 <= i0 < n else "?"
        return f"Compare [{i0}]={v0}"
    return f"Compare {idxs}"


def _window_band_shape(low: int, high: int, n: int) -> Dict[str, Any]:
    """Persistent window-band shape for the array family (#240).

    A translucent band behind the active range. Ids are unique per range
    (the validator rejects duplicate shape ids script-wide); the
    cumulative renderer keeps every band visible as visited-region state.
    """
    x0 = _cell_x(low, n) - 54
    x1 = _cell_x(high, n) + 54
    return {
        "id": f"window_band_{low}_{high}",
        "type": "rect",
        "x": round((x0 + x1) / 2, 2),
        "y": tokens.ROW_Y,
        "width": round(x1 - x0, 2),
        "height": 112,
        "radius": 12,
        "fill": tokens.PALETTE["accent"],
        "stroke": tokens.PALETTE["accent"],
        "lineWidth": 1,
        "opacity": 0.16,
    }


def _result_text(result: Any) -> Optional[str]:
    """Short truthful rendering of a return.result for the outro beat."""
    if result is None or isinstance(result, bool):
        return None
    if isinstance(result, (int, float, str)):
        text = str(result)
    else:
        try:
            text = json.dumps(result, sort_keys=True, default=str)
        except (TypeError, ValueError):
            return None
    text = text.strip()
    return text[:120] if text else None


def plan_array(spec: AlgorithmAnimation) -> List[Dict[str, Any]]:
    """Cinematic array beats: compare→highlight, swap→move, write→label, window→focus."""
    arr = list(spec.initialState.array or [])
    n = len(arr) if arr else 8
    if spec.initialState.array is not None and len(arr) == 0:
        return []
    # Cap displayed cells so the 2-per-cell intro never busts validator caps
    # (40 shapes / 30 motions per step): 15 cells → 30 shapes + 30 motions.
    # Same pattern as MAX_PLAN_NODES; downstream clamps already use n.
    n = min(n, MAX_ARRAY_CELLS)
    display = (arr if arr else [0] * n)[:n]
    title = spec.title or spec.algorithm.replace("-", " ").title()
    # Intro: bars/cells stagger
    shapes: List[Dict[str, Any]] = []
    motion: List[Dict[str, Any]] = []
    for i, v in enumerate(display):
        x = _cell_x(i, n)
        shapes.append(
            {
                "id": f"cell_{i}",
                "type": "rect",
                "x": x,
                "y": tokens.ROW_Y,
                "width": 88,
                "height": 88,
                "radius": 10,
                "fill": tokens.PALETTE["idle_fill"],
                "stroke": tokens.PALETTE["idle_stroke"],
                "lineWidth": 2,
            }
        )
        shapes.append(
            {
                "id": f"val_{i}",
                "type": "text",
                "x": x,
                "y": tokens.ROW_Y,
                "text": _label_text(v),
                "fontSize": tokens.CELL_LABEL_SIZE,
                "fill": tokens.PALETTE["text"],
            }
        )
        motion.append(
            {
                "target": f"cell_{i}",
                "op": "appear",
                "duration": tokens.DURATION["enter"],
            }
        )
        motion.append(
            {"target": f"val_{i}", "op": "appear", "duration": tokens.DURATION["enter"]}
        )
    beats: List[Dict[str, Any]] = [
        {
            "narration": f"{title} — {display}"[:300],
            "shapes": shapes,
            "motion": motion,
            "camera": {"action": "reset", "zoom": tokens.CAMERA["zoom_full"]},
        }
    ]
    last_band: tuple[int, int] | None = None
    for item in _chunk_decision_steps(spec.steps):
        m: List[Dict[str, Any]] = []
        shapes_b: List[Dict[str, Any]] = []
        camera: Dict[str, Any] | None = None
        if isinstance(item, tuple):
            # Decision beat: pointer stroke folds into the compare it sets
            # up; the narration carries the compared values (#240).
            pointer_step, compare_step = item
            pidx = max(0, min(int(pointer_step.index or 0), n - 1))
            m.append(
                {
                    "target": f"cell_{pidx}",
                    "op": "stroke",
                    "to": tokens.PALETTE["accent"],
                    "duration": 0.25,
                }
            )
            idxs = _compare_indices(compare_step)
            for idx in idxs[:2]:
                idx = max(0, min(idx, n - 1))
                m.append(
                    {
                        "target": f"cell_{idx}",
                        "op": "fill",
                        "to": tokens.PALETTE["highlight_fill"],
                        "duration": tokens.DURATION["highlight"],
                    }
                )
                m.append(
                    {
                        "target": f"cell_{idx}",
                        "op": "stroke",
                        "to": tokens.PALETTE["highlight_stroke"],
                        "duration": tokens.DURATION["highlight"],
                    }
                )
            narr = _compare_narration(idxs, display)
            camera = {
                "action": "focus",
                "region": idxs[:2],
                "zoom": tokens.CAMERA["zoom_focus"],
            }
            beat = {
                "narration": narr[:300],
                "shapes": shapes_b,
                "motion": m,
            }
            if camera:
                beat["camera"] = camera
            beats.append(beat)
            continue
        step = item
        narr = step.label or ""
        if step.action == "compare":
            idxs = _compare_indices(step)
            for idx in idxs[:2]:
                idx = max(0, min(idx, n - 1))
                m.append(
                    {
                        "target": f"cell_{idx}",
                        "op": "fill",
                        "to": tokens.PALETTE["highlight_fill"],
                        "duration": tokens.DURATION["highlight"],
                    }
                )
                m.append(
                    {
                        "target": f"cell_{idx}",
                        "op": "stroke",
                        "to": tokens.PALETTE["highlight_stroke"],
                        "duration": tokens.DURATION["highlight"],
                    }
                )
            narr = _compare_narration(idxs, display)
            camera = {
                "action": "focus",
                "region": idxs[:2],
                "zoom": tokens.CAMERA["zoom_focus"],
            }
        elif step.action == "swap":
            if step.indices and len(step.indices) >= 2:
                a, b = step.indices[0], step.indices[1]
                m.append(
                    {
                        "target": f"val_{a}",
                        "op": "move",
                        "to": [_cell_x(b, n), tokens.ROW_Y],
                        "duration": 0.45,
                    }
                )
                m.append(
                    {
                        "target": f"val_{b}",
                        "op": "move",
                        "to": [_cell_x(a, n), tokens.ROW_Y],
                        "duration": 0.45,
                    }
                )
                m.append(
                    {
                        "target": f"cell_{a}",
                        "op": "fill",
                        "to": tokens.PALETTE["accent"],
                        "duration": 0.25,
                    }
                )
                m.append(
                    {
                        "target": f"cell_{b}",
                        "op": "fill",
                        "to": tokens.PALETTE["accent"],
                        "duration": 0.25,
                    }
                )
                if 0 <= a < n and 0 <= b < n:
                    narr = f"Swap [{a}]={display[a]} ↔ [{b}]={display[b]}"
                else:
                    narr = f"Swap [{a}] ↔ [{b}]"
                camera = {
                    "action": "focus",
                    "region": [a, b],
                    "zoom": tokens.CAMERA["zoom_focus"],
                }
            else:
                m.append(
                    {"target": "cell_0", "op": "scale", "to": 1.0, "duration": 0.25}
                )
                narr = "Swap"
        elif step.action == "write":
            idx = max(0, min(int(step.index or 0), n - 1))
            val = step.values[0] if step.values else step.label or "·"
            m.append(
                {
                    "target": f"val_{idx}",
                    "op": "label",
                    "to": str(val)[: tokens.MAX_LABEL],
                    "duration": 0.3,
                }
            )
            m.append(
                {
                    "target": f"cell_{idx}",
                    "op": "fill",
                    "to": tokens.PALETTE["highlight_fill"],
                    "duration": 0.25,
                }
            )
            narr = f"Write [{idx}] = {val}"
            camera = {
                "action": "focus",
                "element": f"cell_{idx}",
                "zoom": tokens.CAMERA["zoom_focus"],
            }
        elif step.action == "window":
            low, high = int(step.low or 0), int(step.high or 0)
            band_range = (max(0, low), min(high, n - 1))
            if band_range != last_band:
                last_band = band_range
                if band_range[0] <= band_range[1]:
                    shapes_b.append(_window_band_shape(*band_range, n))
            for idx in range(low, min(high + 1, n)):
                m.append(
                    {
                        "target": f"cell_{idx}",
                        "op": "fill",
                        "to": tokens.PALETTE["highlight_fill"],
                        "duration": 0.25,
                    }
                )
            narr = f"Window [{low}..{high}] (len {max(0, high - low + 1)})"
            camera = {
                "action": "focus",
                "region": [low, high],
                "zoom": tokens.CAMERA["zoom_focus"],
            }
        elif step.action == "partition":
            idx = max(0, min(int(step.index or 0), n - 1))
            m.append(
                {
                    "target": f"cell_{idx}",
                    "op": "stroke",
                    "to": tokens.PALETTE["accent"],
                    "duration": 0.3,
                }
            )
            m.append(
                {
                    "target": f"cell_{idx}",
                    "op": "fill",
                    "to": tokens.PALETTE["accent"],
                    "duration": 0.3,
                }
            )
            if 0 <= idx < n:
                narr = f"Partition at [{idx}]={display[idx]}"
            else:
                narr = f"Partition at [{idx}]"
            camera = {
                "action": "focus",
                "element": f"cell_{idx}",
                "zoom": tokens.CAMERA["zoom_focus"],
            }
        elif step.action == "mark":
            idx = max(0, min(int(step.index or 0), n - 1))
            m.append(
                {
                    "target": f"cell_{idx}",
                    "op": "fill",
                    "to": tokens.PALETTE["success_fill"],
                    "duration": 0.3,
                }
            )
            m.append(
                {
                    "target": f"cell_{idx}",
                    "op": "stroke",
                    "to": tokens.PALETTE["success_stroke"],
                    "duration": 0.3,
                }
            )
            # The state comes from the trace via _try_planner (label); only
            # sorting algorithms ever mark "sorted" (#235).
            state = step.label or "sorted"
            if 0 <= idx < n:
                narr = f"Mark [{idx}]={display[idx]} {state}"
            else:
                narr = f"Mark [{idx}] {state}"
            camera = {
                "action": "focus",
                "element": f"cell_{idx}",
                "zoom": tokens.CAMERA["zoom_focus"],
            }
        elif step.action == "pointer":
            idx = max(0, min(int(step.index or 0), n - 1))
            m.append(
                {
                    "target": f"cell_{idx}",
                    "op": "stroke",
                    "to": tokens.PALETTE["accent"],
                    "duration": 0.25,
                }
            )
            if step.label:
                narr = step.label
            elif 0 <= idx < n:
                narr = f"Pointer → [{idx}]={display[idx]}"
            else:
                narr = f"Pointer → [{idx}]"
            camera = {
                "action": "focus",
                "element": f"cell_{idx}",
                "zoom": tokens.CAMERA["zoom_focus"],
            }
        elif step.action in ("read", "visit"):
            # Array traces observe cells via read (greedy/DP) and visit
            # (cycle/consecutive scans) — highlight the observed cell like a
            # single compare, never a placeholder beat on cell_0 (#235).
            idx = max(0, min(int(step.index or 0), n - 1))
            m.append(
                {
                    "target": f"cell_{idx}",
                    "op": "fill",
                    "to": tokens.PALETTE["highlight_fill"],
                    "duration": 0.25,
                }
            )
            m.append(
                {
                    "target": f"cell_{idx}",
                    "op": "stroke",
                    "to": tokens.PALETTE["highlight_stroke"],
                    "duration": 0.25,
                }
            )
            verb = "Read" if step.action == "read" else "Visit"
            if 0 <= idx < n:
                narr = f"{verb} [{idx}]={display[idx]}"
            else:
                narr = f"{verb} [{idx}]"
            camera = {
                "action": "focus",
                "element": f"cell_{idx}",
                "zoom": tokens.CAMERA["zoom_focus"],
            }
        elif step.action == "found":
            # Climax beat: the returned index resolves to a real cell (#240).
            idx = max(0, min(int(step.index or 0), n - 1))
            m.append(
                {
                    "target": f"cell_{idx}",
                    "op": "fill",
                    "to": tokens.PALETTE["success_fill"],
                    "duration": tokens.DURATION["highlight"],
                }
            )
            m.append(
                {
                    "target": f"cell_{idx}",
                    "op": "stroke",
                    "to": tokens.PALETTE["success_stroke"],
                    "duration": tokens.DURATION["highlight"],
                }
            )
            m.append(
                {
                    "target": f"cell_{idx}",
                    "op": "scale",
                    "to": 1.15,
                    "duration": 0.3,
                }
            )
            target = spec.initialState.target
            if target is not None:
                narr = f"Found {target} at [{idx}]"
            elif 0 <= idx < n:
                narr = f"Result [{idx}]={display[idx]}"
            else:
                narr = f"Result [{idx}]"
            camera = {
                "action": "focus",
                "element": f"cell_{idx}",
                "zoom": tokens.CAMERA["zoom_focus"],
            }
        elif step.action == "not_found":
            target = spec.initialState.target
            narr = f"{target} not in array" if target is not None else "Not found"
            for idx in range(n):
                m.append(
                    {
                        "target": f"cell_{idx}",
                        "op": "fill",
                        "to": tokens.PALETTE["dim_fill"],
                        "duration": tokens.DURATION["dim"],
                    }
                )
        beat = {
            "narration": narr[:300],
            "shapes": shapes_b,
            "motion": m,
        }
        if camera:
            beat["camera"] = camera
        beats.append(beat)
    result_text = _result_text((spec.initialState.extra or {}).get("result"))
    outro_narration = f"{spec.complexity.time} · {spec.complexity.space}"
    if result_text is not None:
        outro_narration = f"Result {result_text} · {outro_narration}"
    beats.append(
        {
            "narration": outro_narration[:300],
            "shapes": [],
            "motion": [
                {"target": "cell_0", "op": "scale", "to": 1.0, "duration": 0.25}
            ],
            "badge": {"time": spec.complexity.time, "space": spec.complexity.space},
        }
    )
    return _finalize_beats(beats, spec.complexity)


# ── stack ────────────────────────────────────────────────────────────────────


def plan_stack(spec: AlgorithmAnimation) -> List[Dict[str, Any]]:
    beats: List[Dict[str, Any]] = [
        {
            "narration": f"{spec.title or spec.algorithm} — Stack"[:300],
            "shapes": [_root_shape("stack_base")],
            "motion": [{"target": "stack_base", "op": "appear", "duration": 0.4}],
            "camera": {"action": "reset"},
        }
    ]
    known = {"stack_base"}
    depth = 0
    created: List[str] = []
    for step in spec.steps:
        m: List[Dict[str, Any]] = []
        shapes: List[Dict[str, Any]] = []
        narr = step.label or step.action
        if step.action == "push":
            val = step.values[0] if step.values else "·"
            sid = f"stack_{depth}"
            if sid not in known:
                shapes.append(_item_shape(sid, x=0.0, y=-depth * 60.0))
                known.add(sid)
            m.append({"target": sid, "op": "appear", "duration": 0.35})
            m.append(
                {
                    "target": sid,
                    "op": "move",
                    "to": [0, -depth * 60],
                    "duration": 0.35,
                }
            )
            narr = f"Push {val}"
            created.append(sid)
            depth += 1
        elif step.action == "pop":
            depth = max(0, depth - 1)
            sid = created.pop() if created else f"stack_{depth}"
            if sid not in known:
                m.append(
                    {"target": "stack_base", "op": "scale", "to": 1.0, "duration": 0.25}
                )
            else:
                m.append(
                    {
                        "target": sid,
                        "op": "move",
                        "to": [0, 220.0],
                        "duration": 0.3,
                    }
                )
                m.append({"target": sid, "op": "disappear", "duration": 0.2})
            narr = f"Pop {step.values[0] if step.values else ''}".strip()
        elif step.action == "visit":
            idx = step.index or 0
            m.append(
                {
                    "target": "stack_base",
                    "op": "stroke",
                    "to": tokens.PALETTE["accent"],
                    "duration": 0.3,
                }
            )
            narr = f"Visit [{idx}]"
        else:
            m.append(
                {"target": "stack_base", "op": "scale", "to": 1.0, "duration": 0.25}
            )
        beats.append({"narration": narr[:300], "shapes": shapes, "motion": m})
    beats.append(
        {
            "narration": f"{spec.complexity.time}"[:300],
            "shapes": [],
            "motion": [
                {"target": "stack_base", "op": "scale", "to": 1.0, "duration": 0.25}
            ],
            "badge": {"time": spec.complexity.time, "space": spec.complexity.space},
        }
    )
    return beats


# ── linked_list ──────────────────────────────────────────────────────────────


def plan_linked_list(spec: AlgorithmAnimation) -> List[Dict[str, Any]]:
    arr = list(spec.initialState.array or [])
    n = len(arr) if arr else 5
    # Cap like tree/graph (MAX_PLAN_NODES) so the 2n+1-shape intro can never
    # bust the validator caps (40 shapes / 30 motions per step).
    n = max(1, min(n, MAX_PLAN_NODES))
    # Compress horizontal spacing for large n so nodes stay in ±960 bounds;
    # identical to the old -200+i*100 layout for n <= 5.
    gap = min(100.0, 1500.0 / n)
    node_x = [round((i - (n - 1) / 2) * gap, 2) for i in range(n)]
    intro_shapes: List[Dict[str, Any]] = [
        {
            "id": f"node_{i}",
            "type": "ellipse",
            "x": node_x[i],
            "y": 0,
            "width": 60,
            "height": 60,
            "fill": tokens.PALETTE["idle_fill"],
            "stroke": tokens.PALETTE["idle_stroke"],
        }
        for i in range(n)
    ]
    for i in range(n - 1):
        intro_shapes.append(
            {
                "id": f"link_{i}",
                "type": "line",
                "points": [[node_x[i] + 30.0, 0.0], [node_x[i + 1] - 30.0, 0.0]],
                "stroke": tokens.PALETTE["muted"],
                "lineWidth": 2,
            }
        )
    null_x = round(((n + 1) / 2) * gap, 2)
    intro_shapes.append(
        {
            "id": "node_null",
            "type": "ellipse",
            "x": null_x,
            "y": 0,
            "width": 60,
            "height": 60,
            "fill": tokens.PALETTE["idle_fill"],
            "stroke": tokens.PALETTE["idle_stroke"],
        }
    )
    intro_shapes.append(
        {
            "id": "val_null",
            "type": "text",
            "x": null_x,
            "y": 0,
            "text": "null",
            "fontSize": 22,
            "fill": tokens.PALETTE["muted"],
        }
    )
    beats: List[Dict[str, Any]] = [
        {
            "narration": f"{spec.title or spec.algorithm} — Linked List"[:300],
            "shapes": intro_shapes,
            # Appear motions cover nodes only (n + 2 ops): link lines render
            # statically so the intro stays under the 30-motions-per-step cap.
            "motion": [
                {"target": s["id"], "op": "appear", "duration": 0.3}
                for s in intro_shapes
                if s["id"].startswith("node_") or s["id"] == "val_null"
            ],
            "camera": {"action": "reset"},
        }
    ]
    for step in spec.steps:
        m: List[Dict[str, Any]] = []
        narr = step.label or step.action
        if step.action == "visit":
            idx = max(0, min(int(step.index or 0), n - 1))
            m.append(
                {
                    "target": f"node_{idx}",
                    "op": "fill",
                    "to": tokens.PALETTE["highlight_fill"],
                    "duration": 0.3,
                }
            )
            m.append(
                {
                    "target": f"node_{idx}",
                    "op": "stroke",
                    "to": tokens.PALETTE["highlight_stroke"],
                    "duration": 0.3,
                }
            )
            narr = f"Visit node {idx}"
        elif step.action == "pointer":
            idx = max(0, min(int(step.index or 0), n - 1))
            m.append(
                {
                    "target": f"node_{idx}",
                    "op": "stroke",
                    "to": tokens.PALETTE["accent"],
                    "duration": 0.3,
                }
            )
            narr = f"Pointer → node {idx}"
        else:
            m.append({"target": "node_0", "op": "scale", "to": 1.0, "duration": 0.25})
        beats.append({"narration": narr[:300], "shapes": [], "motion": m})
    beats.append(
        {
            "narration": f"{spec.complexity.time}"[:300],
            "shapes": [],
            "motion": [
                {"target": "node_0", "op": "scale", "to": 1.0, "duration": 0.25}
            ],
            "badge": {"time": spec.complexity.time, "space": spec.complexity.space},
        }
    )
    return beats


# ── tree ─────────────────────────────────────────────────────────────────────


TREE_WIDTH = 620.0
TREE_TOP = -240.0
TREE_LEVEL_H = 96.0


def tree_layout(n: int) -> List[Dict[str, float]]:
    """Return [{x, y}] positions for level-order indices 0..n-1."""
    positions = []
    for i in range(n):
        level = int(math.floor(math.log2(i + 1)))
        pos_in_level = i - (2**level - 1)
        slots = 2**level
        x = -TREE_WIDTH / 2 + (pos_in_level + 0.5) * (TREE_WIDTH / slots)
        y = TREE_TOP + level * TREE_LEVEL_H
        positions.append({"x": round(x, 2), "y": round(y, 2)})
    return positions


GRAPH_RADIUS = 230.0
GRID_CELL = 60.0
GRID_GAP = 8.0
GRID_Y = -80.0

# Validator caps (animation_validator MAX_SHAPES_PER_STEP 40 /
# MAX_MOTIONS_PER_STEP 30) bound full-layout intros; canonical inputs are far
# smaller, but a stray large index must never hang the planner or bust caps.
MAX_PLAN_NODES = 16
# Array intros emit 2 shapes + 2 motions per cell, so the display cap is 15
# (30 shapes + 30 motions — both exactly within caps).
MAX_ARRAY_CELLS = 15


def _plan_node_count(array_len: int, refs: List[int]) -> int:
    want = max([int(array_len)] + [i + 1 for i in refs if i >= 0] + [1])
    return max(1, min(want, MAX_PLAN_NODES))


def _tree_edge_shape(
    sid: str, pos: Dict[str, float], parent_pos: Dict[str, float]
) -> Dict[str, Any]:
    return {
        "id": sid,
        "type": "line",
        "points": [
            [parent_pos["x"], round(parent_pos["y"] + 22.0, 2)],
            [pos["x"], round(pos["y"] - 22.0, 2)],
        ],
        "stroke": tokens.PALETTE["idle_stroke"],
        "lineWidth": 2,
    }


def _tree_pos(idx: int) -> Dict[str, float]:
    """Level-order position for one tree index (index-pure math)."""
    safe = max(0, min(int(idx), MAX_PLAN_NODES - 1))
    return tree_layout(safe + 1)[safe]


def _graph_positions(n: int) -> List[Dict[str, float]]:
    """Circular layout radius GRAPH_RADIUS (parity with family_compilers)."""
    total = max(int(n), 1)
    positions = []
    for i in range(total):
        angle = 2 * math.pi * i / total - math.pi / 2
        positions.append(
            {
                "x": round(GRAPH_RADIUS * math.cos(angle), 2),
                "y": round(GRAPH_RADIUS * math.sin(angle), 2),
            }
        )
    return positions


def _grid_position(idx: int, n: int) -> Dict[str, float]:
    """Grid cell position from GRID_CELL/GAP centered on GRID_Y."""
    total = max(int(n), 1)
    cols = max(1, int(math.ceil(math.sqrt(total))))
    rows = max(1, int(math.ceil(total / cols)))
    safe = max(0, min(int(idx), total - 1))
    c, r = safe % cols, safe // cols
    return {
        "x": round((c - (cols - 1) / 2) * (GRID_CELL + GRID_GAP), 2),
        "y": round(GRID_Y + (r - (rows - 1) / 2) * (GRID_CELL + GRID_GAP), 2),
    }


def plan_tree(spec: AlgorithmAnimation) -> List[Dict[str, Any]]:
    ref = [int(s.index or 0) for s in spec.steps]
    node_count = _plan_node_count(len(spec.initialState.array or []), ref)
    positions = tree_layout(node_count)
    intro_shapes: List[Dict[str, Any]] = [_root_shape("tree_root")]
    intro_motion: List[Dict[str, Any]] = [
        {
            "target": "tree_root",
            "op": "appear",
            "duration": tokens.DURATION["enter"],
        }
    ]
    for i, pos in enumerate(positions):
        intro_shapes.append(_item_shape(f"tree_{i}", x=pos["x"], y=pos["y"]))
        intro_motion.append({"target": f"tree_{i}", "op": "appear", "duration": 0.3})
        if i > 0:
            intro_shapes.append(
                _tree_edge_shape(f"tree_edge_{i}", pos, positions[(i - 1) // 2])
            )
    known = {"tree_root"}
    known.update(s["id"] for s in intro_shapes)
    beats: List[Dict[str, Any]] = [
        {
            "narration": f"{spec.title or spec.algorithm} — Tree"[:300],
            "shapes": intro_shapes,
            "motion": intro_motion,
            "camera": {"action": "reset"},
        }
    ]
    for step in spec.steps:
        m: List[Dict[str, Any]] = []
        shapes: List[Dict[str, Any]] = []
        narr = step.label or step.action
        idx = int(step.index or 0)
        sid = f"tree_{idx}"
        if step.action in ("visit", "choose", "backtrack") and sid not in known:
            pos = _tree_pos(idx)
            shapes.append(_item_shape(sid, x=pos["x"], y=pos["y"]))
            known.add(sid)
            if idx > 0:
                eid = f"tree_edge_{idx}"
                if eid not in known:
                    shapes.append(_tree_edge_shape(eid, pos, _tree_pos((idx - 1) // 2)))
                    known.add(eid)
        if step.action == "visit":
            m.append(
                {
                    "target": sid,
                    "op": "fill",
                    "to": tokens.PALETTE["highlight_fill"],
                    "duration": 0.3,
                }
            )
            narr = f"Visit {idx}"
        elif step.action == "choose":
            m.append(
                {
                    "target": sid,
                    "op": "stroke",
                    "to": tokens.PALETTE["accent"],
                    "duration": 0.3,
                }
            )
            narr = f"Choose {idx}"
        elif step.action == "backtrack":
            m.append(
                {
                    "target": sid,
                    "op": "fill",
                    "to": tokens.PALETTE["dim_fill"],
                    "duration": 0.3,
                }
            )
            narr = f"Backtrack {idx}"
        else:
            m.append(
                {"target": "tree_root", "op": "scale", "to": 1.0, "duration": 0.25}
            )
        beats.append({"narration": narr[:300], "shapes": shapes, "motion": m})
    beats.append(
        {
            "narration": f"{spec.complexity.time}"[:300],
            "shapes": [],
            "motion": [
                {"target": "tree_root", "op": "scale", "to": 1.0, "duration": 0.25}
            ],
            "badge": {"time": spec.complexity.time, "space": spec.complexity.space},
        }
    )
    return beats


# ── graph / grid ─────────────────────────────────────────────────────────────


def plan_graph(spec: AlgorithmAnimation, kind: str = "graph") -> List[Dict[str, Any]]:
    root = f"{kind}_root"
    ref_idxs: List[int] = []
    for _s in spec.steps:
        if _s.action == "visit" and _s.index is not None:
            ref_idxs.append(int(_s.index))
        elif _s.action == "edge" and _s.indices:
            ref_idxs.extend(int(v) for v in _s.indices[:2])
        elif _s.action == "relax_edge" and _s.indices:
            ref_idxs.append(int(_s.indices[0]))
    node_count = _plan_node_count(len(spec.initialState.array or []), ref_idxs)
    if kind == "grid":
        positions = [_grid_position(i, node_count) for i in range(node_count)]
    else:
        positions = _graph_positions(node_count)

    def _pos(idx: int) -> Dict[str, float]:
        return positions[max(0, min(int(idx), len(positions) - 1))]

    intro_shapes: List[Dict[str, Any]] = [_root_shape(root)]
    intro_motion: List[Dict[str, Any]] = [
        {"target": root, "op": "appear", "duration": 0.4}
    ]
    for i, pos in enumerate(positions):
        intro_shapes.append(_item_shape(f"node_{i}", x=pos["x"], y=pos["y"]))
        intro_motion.append({"target": f"node_{i}", "op": "appear", "duration": 0.3})
    known = {root}
    known.update(s["id"] for s in intro_shapes)
    beats: List[Dict[str, Any]] = [
        {
            "narration": f"{spec.title or spec.algorithm} — {kind.title()}"[:300],
            "shapes": intro_shapes,
            "motion": intro_motion,
            "camera": {"action": "reset"},
        }
    ]
    for step in spec.steps:
        m: List[Dict[str, Any]] = []
        shapes: List[Dict[str, Any]] = []
        narr = step.label or step.action
        if step.action == "visit":
            idx = int(step.index or 0)
            sid = f"node_{idx}"
            _ensure_graph_node(known, shapes, sid, idx, positions)
            m.append(
                {
                    "target": sid,
                    "op": "fill",
                    "to": tokens.PALETTE["highlight_fill"],
                    "duration": 0.3,
                }
            )
            narr = f"Visit {idx}"
        elif step.action == "edge":
            a = step.indices[0] if step.indices and len(step.indices) >= 1 else 0
            b = step.indices[1] if step.indices and len(step.indices) >= 2 else 1
            eid = f"edge_{a}_{b}"
            if eid not in known:
                shapes.append(_graph_edge_shape(eid, _pos(a), _pos(b)))
                known.add(eid)
            _ensure_graph_node(known, shapes, f"node_{b}", b, positions)
            m.append(
                {
                    "target": eid,
                    "op": "stroke",
                    "to": tokens.PALETTE["accent"],
                    "duration": 0.3,
                }
            )
            m.append(
                {
                    "target": f"node_{b}",
                    "op": "fill",
                    "to": tokens.PALETTE["success_fill"],
                    "duration": 0.3,
                }
            )
            narr = f"Edge {a} → {b}"
        elif step.action == "relax_edge":
            idx = int(step.indices[0]) if step.indices else 0
            sid = f"node_{idx}"
            _ensure_graph_node(known, shapes, sid, idx, positions)
            narr = f"Relax {step.indices}"
            m.append({"target": sid, "op": "scale", "to": 1.05, "duration": 0.25})
        else:
            m.append({"target": root, "op": "scale", "to": 1.0, "duration": 0.25})
        beats.append({"narration": narr[:300], "shapes": shapes, "motion": m})
    beats.append(
        {
            "narration": f"{spec.complexity.time}"[:300],
            "shapes": [],
            "motion": [
                {"target": f"{kind}_root", "op": "scale", "to": 1.0, "duration": 0.25}
            ],
            "badge": {"time": spec.complexity.time, "space": spec.complexity.space},
        }
    )
    return beats


# ── intervals ────────────────────────────────────────────────────────────────


# Token-scaled interval bars (mirrors family_compilers._compile_intervals math:
# lo/hi span, IV_WIDTH 700, bar_x/bar_w). Kept local so the planner owns its
# layout while the compiler remains the fallback path's source of truth.
IV_WIDTH = 700.0
IV_Y0 = -160.0
IV_H = 40.0
IV_GAP = 18.0
IV_MAX = 10


def _interval_pairs(array: Any) -> List[Any]:
    """Extract [lo, hi] pairs from the initial state, ignoring junk."""
    pairs: List[Any] = []
    for item in array or []:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            try:
                pairs.append((int(item[0]), int(item[1])))
            except (TypeError, ValueError):
                continue
    return pairs


def plan_intervals(spec: AlgorithmAnimation) -> List[Dict[str, Any]]:
    pairs = _interval_pairs(spec.initialState.array)
    if not pairs:
        # Traces carry init `data`, which _try_planner does not forward — fall
        # back to one unit bar per distinct referenced index so visit/mark
        # beats still render instead of a placeholder rect.
        seen: List[int] = []
        for s in spec.steps:
            refs = ([s.index] if s.index is not None else []) + list(s.indices or [])
            for v in refs:
                try:
                    idx = int(v)
                except (TypeError, ValueError):
                    continue
                if idx not in seen:
                    seen.append(idx)
        pairs = [(i, i + 1) for i in seen[:IV_MAX]] or [(0, 1)]
    else:
        pairs = pairs[:IV_MAX]

    lo = min(s for s, _ in pairs)
    hi = max(e for _, e in pairs)
    span = max(hi - lo, 1)

    def bar_x(start: int) -> float:
        return round(-IV_WIDTH / 2 + (start - lo) * IV_WIDTH / span, 2)

    def bar_w(start: int, end: int) -> float:
        return max(20.0, round((end - start) * IV_WIDTH / span, 2))

    intro_shapes: List[Dict[str, Any]] = []
    intro_motion: List[Dict[str, Any]] = []
    for i, (s, e) in enumerate(pairs):
        y = round(IV_Y0 + i * (IV_H + IV_GAP), 2)
        w = bar_w(s, e)
        cx = round(bar_x(s) + w / 2, 2)
        intro_shapes.append(
            {
                "id": f"bar_{i}",
                "type": "rect",
                "x": cx,
                "y": y,
                "width": w,
                "height": IV_H,
                "radius": 6,
                "fill": tokens.PALETTE["idle_fill"],
                "stroke": tokens.PALETTE["idle_stroke"],
                "lineWidth": 2,
            }
        )
        intro_shapes.append(
            {
                "id": f"bar_val_{i}",
                "type": "text",
                "x": cx,
                "y": y,
                "text": f"[{s},{e}]"[: tokens.MAX_LABEL],
                "fontSize": 16,
                "fill": tokens.PALETTE["text"],
            }
        )
        intro_motion.append(
            {"target": f"bar_{i}", "op": "appear", "duration": tokens.DURATION["enter"]}
        )
    beats: List[Dict[str, Any]] = [
        {
            "narration": f"{spec.title or spec.algorithm} — Intervals {pairs}"[:300],
            "shapes": intro_shapes,
            "motion": intro_motion,
            "camera": {"action": "reset"},
        }
    ]

    def _clamp(idx: int) -> int:
        return max(0, min(int(idx), len(pairs) - 1))

    for step in spec.steps:
        m: List[Dict[str, Any]] = []
        narr = step.label or step.action
        raw = step.index
        if raw is None and step.indices:
            raw = step.indices[0]
        idx = _clamp(raw if raw is not None else 0)
        sid = f"bar_{idx}"
        s, e = pairs[idx]
        camera: Dict[str, Any] | None = {
            "action": "focus",
            "element": sid,
            "zoom": tokens.CAMERA["zoom_focus"],
        }
        if step.action == "visit":
            m.append(
                {
                    "target": sid,
                    "op": "fill",
                    "to": tokens.PALETTE["highlight_fill"],
                    "duration": tokens.DURATION["highlight"],
                }
            )
            m.append(
                {
                    "target": sid,
                    "op": "stroke",
                    "to": tokens.PALETTE["highlight_stroke"],
                    "duration": tokens.DURATION["highlight"],
                }
            )
            narr = step.label or f"Visit [{s},{e}] (interval {idx})"
        elif step.action == "mark":
            m.append(
                {
                    "target": sid,
                    "op": "fill",
                    "to": tokens.PALETTE["success_fill"],
                    "duration": 0.3,
                }
            )
            m.append(
                {
                    "target": sid,
                    "op": "stroke",
                    "to": tokens.PALETTE["success_stroke"],
                    "duration": 0.3,
                }
            )
            narr = step.label or f"Mark [{s},{e}] (interval {idx})"
        elif step.action == "pointer":
            m.append(
                {
                    "target": sid,
                    "op": "stroke",
                    "to": tokens.PALETTE["accent"],
                    "duration": 0.25,
                }
            )
            narr = step.label or f"Pointer → [{s},{e}]"
        elif step.action in ("partition", "window"):
            m.append(
                {
                    "target": sid,
                    "op": "stroke",
                    "to": tokens.PALETTE["accent"],
                    "duration": 0.3,
                }
            )
            narr = step.label or f"{step.action.title()} [{s},{e}] (interval {idx})"
        else:
            camera = None
            m.append({"target": "bar_0", "op": "scale", "to": 1.0, "duration": 0.25})
        beat: Dict[str, Any] = {"narration": narr[:300], "shapes": [], "motion": m}
        if camera:
            beat["camera"] = camera
        beats.append(beat)
    beats.append(
        {
            "narration": f"{spec.complexity.time}"[:300],
            "shapes": [],
            "motion": [{"target": "bar_0", "op": "scale", "to": 1.0, "duration": 0.25}],
            "badge": {"time": spec.complexity.time, "space": spec.complexity.space},
        }
    )
    return beats


# ── backtrack ────────────────────────────────────────────────────────────────


def plan_backtrack(spec: AlgorithmAnimation) -> List[Dict[str, Any]]:
    beats: List[Dict[str, Any]] = [
        {
            "narration": f"{spec.title or spec.algorithm} — Backtracking"[:300],
            "shapes": [_root_shape("bt_root")],
            "motion": [{"target": "bt_root", "op": "appear", "duration": 0.4}],
            "camera": {"action": "reset"},
        }
    ]
    known = {"bt_root"}
    depth = 0

    def _ensure(sid: str, shapes: List[Dict[str, Any]], pos: int) -> None:
        if sid not in known:
            p = _tree_pos(pos)
            shapes.append(_item_shape(sid, x=p["x"], y=p["y"]))
            known.add(sid)

    for step in spec.steps:
        m: List[Dict[str, Any]] = []
        shapes: List[Dict[str, Any]] = []
        narr = step.label or step.action
        if step.action == "choose":
            idx = int(step.index or depth)
            sid = f"bt_{idx}"
            _ensure(sid, shapes, idx)
            m.append(
                {
                    "target": sid,
                    "op": "fill",
                    "to": tokens.PALETTE["highlight_fill"],
                    "duration": 0.3,
                }
            )
            m.append(
                {
                    "target": sid,
                    "op": "stroke",
                    "to": tokens.PALETTE["highlight_stroke"],
                    "duration": 0.3,
                }
            )
            narr = f"Choose [{idx}]"
            depth += 1
        elif step.action == "backtrack":
            idx = int(step.index or max(0, depth - 1))
            sid = f"bt_{idx}"
            _ensure(sid, shapes, idx)
            m.append(
                {
                    "target": sid,
                    "op": "fill",
                    "to": tokens.PALETTE["dim_fill"],
                    "duration": 0.3,
                }
            )
            narr = f"Backtrack [{idx}]"
            depth = max(0, depth - 1)
        elif step.action == "visit":
            idx = int(step.index or 0)
            sid = f"bt_{idx}"
            _ensure(sid, shapes, idx)
            m.append(
                {
                    "target": sid,
                    "op": "fill",
                    "to": tokens.PALETTE["highlight_fill"],
                    "duration": 0.3,
                }
            )
            narr = f"Visit {idx}"
        else:
            m.append({"target": "bt_root", "op": "scale", "to": 1.0, "duration": 0.25})
        beats.append({"narration": narr[:300], "shapes": shapes, "motion": m})
    beats.append(
        {
            "narration": f"{spec.complexity.time}"[:300],
            "shapes": [],
            "motion": [
                {"target": "bt_root", "op": "scale", "to": 1.0, "duration": 0.25}
            ],
            "badge": {"time": spec.complexity.time, "space": spec.complexity.space},
        }
    )
    return beats


# ── dispatcher ───────────────────────────────────────────────────────────────


def plan(spec: AlgorithmAnimation) -> List[Dict[str, Any]]:
    """Dispatch to template planner — covers all 103 canonical algos."""
    viz = spec.visualization
    if viz == "sorted-array":
        return _finalize_beats(plan_searching(spec), spec.complexity)
    if viz in ("bars", "array"):
        return _finalize_beats(plan_array(spec), spec.complexity)
    if viz == "stack":
        return _finalize_beats(plan_stack(spec), spec.complexity)
    if viz == "queue":
        # queue reuses stack beats with shifted layout
        return _finalize_beats(plan_stack(spec), spec.complexity)
    if viz == "linked_list":
        return _finalize_beats(plan_linked_list(spec), spec.complexity)
    if viz == "tree":
        return _finalize_beats(plan_tree(spec), spec.complexity)
    if viz == "graph":
        return _finalize_beats(plan_graph(spec, "graph"), spec.complexity)
    if viz == "grid":
        return _finalize_beats(plan_graph(spec, "grid"), spec.complexity)
    if viz == "intervals":
        return _finalize_beats(plan_intervals(spec), spec.complexity)
    if viz == "backtrack":
        return _finalize_beats(plan_backtrack(spec), spec.complexity)
    # Fallback: generic array beats so no algo renders empty
    return _finalize_beats(plan_array(spec), spec.complexity)
