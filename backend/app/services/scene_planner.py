"""Scene Planner — semantic AlgorithmAnimation steps → cinematic SceneBeats.

Beats are generic AnimationScript steps (narration/shapes/motion) planned with
visual hierarchy: ARRAY APPEARS → MID ENTERS → RELATION → DISCARD → CAMERA
FOCUS → NEXT. Planner decides pacing; Design System decides look.

Now covers all 8 families (array/sorted-array/bars, stack, linked_list, tree,
graph, grid, intervals, backtrack) → all 103 canonical solutions. Each planner
is cinematic (highlight/dim/camera/badges) not literal debugger steps.
"""

from typing import Any, Dict, List

from app.models.animation_spec import AlgorithmAnimation
from app.services import animation_design_tokens as tokens


def _cell_x(index: int, n: int, cell: float = 88.0, gap: float = 12.0) -> float:
    total = n * cell + (n - 1) * gap
    start = -total / 2 + cell / 2
    return round(start + index * (cell + gap), 2)


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
                "text": str(v)[: tokens.MAX_LABEL],
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


def plan_array(spec: AlgorithmAnimation) -> List[Dict[str, Any]]:
    """Cinematic array beats: compare→highlight, swap→move, write→label, window→focus."""
    arr = list(spec.initialState.array or [])
    n = len(arr) if arr else 8
    if spec.initialState.array is not None and len(arr) == 0:
        return []
    title = spec.title or spec.algorithm.replace("-", " ").title()
    # Intro: bars/cells stagger
    shapes: List[Dict[str, Any]] = []
    motion: List[Dict[str, Any]] = []
    display = arr if arr else [0] * n
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
                "text": str(v)[: tokens.MAX_LABEL],
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
    for step in spec.steps:
        m: List[Dict[str, Any]] = []
        camera: Dict[str, Any] | None = None
        narr = step.label or ""
        if step.action == "compare":
            idxs = step.indices or ([step.index] if step.index is not None else [])
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
            narr = f"Compare {idxs}"
            camera = {"action": "focus", "region": idxs[:2]}
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
                narr = f"Swap [{a}] ↔ [{b}]"
                camera = {"action": "focus", "region": [a, b]}
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
            camera = {"action": "focus", "element": f"cell_{idx}"}
        elif step.action == "window":
            low, high = int(step.low or 0), int(step.high or 0)
            for idx in range(low, min(high + 1, n)):
                m.append(
                    {
                        "target": f"cell_{idx}",
                        "op": "fill",
                        "to": tokens.PALETTE["highlight_fill"],
                        "duration": 0.25,
                    }
                )
            narr = f"Window [{low}..{high}]"
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
            narr = f"Partition at [{idx}]"
            camera = {"action": "focus", "element": f"cell_{idx}"}
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
            narr = f"Mark [{idx}] sorted"
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
            narr = step.label or f"Pointer → [{idx}]"
            camera = {"action": "focus", "element": f"cell_{idx}"}
        else:
            m.append({"target": "cell_0", "op": "scale", "to": 1.0, "duration": 0.25})
            narr = step.label or step.action
        beat: Dict[str, Any] = {"narration": narr[:300], "shapes": [], "motion": m}
        if camera:
            beat["camera"] = camera
        beats.append(beat)
    beats.append(
        {
            "narration": f"{spec.complexity.time} · {spec.complexity.space}"[:300],
            "shapes": [],
            "motion": [
                {"target": "cell_0", "op": "scale", "to": 1.0, "duration": 0.25}
            ],
            "badge": {"time": spec.complexity.time, "space": spec.complexity.space},
        }
    )
    return beats


# ── stack ────────────────────────────────────────────────────────────────────


def plan_stack(spec: AlgorithmAnimation) -> List[Dict[str, Any]]:
    beats: List[Dict[str, Any]] = [
        {
            "narration": f"{spec.title or spec.algorithm} — Stack"[:300],
            "shapes": [],
            "motion": [{"target": "stack_base", "op": "appear", "duration": 0.4}],
            "camera": {"action": "reset"},
        }
    ]
    depth = 0
    for step in spec.steps:
        m: List[Dict[str, Any]] = []
        narr = step.label or step.action
        if step.action == "push":
            val = step.values[0] if step.values else "·"
            m.append({"target": f"stack_{depth}", "op": "appear", "duration": 0.35})
            m.append(
                {
                    "target": f"stack_{depth}",
                    "op": "move",
                    "to": [0, -depth * 60],
                    "duration": 0.35,
                }
            )
            narr = f"Push {val}"
            depth += 1
        elif step.action == "pop":
            depth = max(0, depth - 1)
            m.append({"target": f"stack_{depth}", "op": "disappear", "duration": 0.3})
            narr = f"Pop {step.values[0] if step.values else ''}".strip()
        elif step.action == "visit":
            idx = step.index or 0
            m.append(
                {
                    "target": f"cell_{idx}",
                    "op": "fill",
                    "to": tokens.PALETTE["highlight_fill"],
                    "duration": 0.3,
                }
            )
            narr = f"Visit [{idx}]"
        else:
            m.append(
                {"target": "stack_base", "op": "scale", "to": 1.0, "duration": 0.25}
            )
        beats.append({"narration": narr[:300], "shapes": [], "motion": m})
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
    beats: List[Dict[str, Any]] = [
        {
            "narration": f"{spec.title or spec.algorithm} — Linked List"[:300],
            "shapes": [
                {
                    "id": f"node_{i}",
                    "type": "ellipse",
                    "x": -200 + i * 100,
                    "y": 0,
                    "width": 60,
                    "height": 60,
                    "fill": tokens.PALETTE["idle_fill"],
                    "stroke": tokens.PALETTE["idle_stroke"],
                }
                for i in range(n)
            ],
            "motion": [
                {"target": f"node_{i}", "op": "appear", "duration": 0.3}
                for i in range(n)
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


def plan_tree(spec: AlgorithmAnimation) -> List[Dict[str, Any]]:
    beats: List[Dict[str, Any]] = [
        {
            "narration": f"{spec.title or spec.algorithm} — Tree"[:300],
            "shapes": [],
            "motion": [{"target": "tree_root", "op": "appear", "duration": 0.4}],
            "camera": {"action": "reset"},
        }
    ]
    for step in spec.steps:
        m: List[Dict[str, Any]] = []
        narr = step.label or step.action
        idx = int(step.index or 0)
        if step.action == "visit":
            m.append(
                {
                    "target": f"tree_{idx}",
                    "op": "fill",
                    "to": tokens.PALETTE["highlight_fill"],
                    "duration": 0.3,
                }
            )
            narr = f"Visit {idx}"
        elif step.action == "choose":
            m.append(
                {
                    "target": f"tree_{idx}",
                    "op": "stroke",
                    "to": tokens.PALETTE["accent"],
                    "duration": 0.3,
                }
            )
            narr = f"Choose {idx}"
        elif step.action == "backtrack":
            m.append(
                {
                    "target": f"tree_{idx}",
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
        beats.append({"narration": narr[:300], "shapes": [], "motion": m})
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
    beats: List[Dict[str, Any]] = [
        {
            "narration": f"{spec.title or spec.algorithm} — {kind.title()}"[:300],
            "shapes": [],
            "motion": [{"target": f"{kind}_root", "op": "appear", "duration": 0.4}],
            "camera": {"action": "reset"},
        }
    ]
    for step in spec.steps:
        m: List[Dict[str, Any]] = []
        narr = step.label or step.action
        if step.action == "visit":
            idx = int(step.index or 0)
            m.append(
                {
                    "target": f"node_{idx}",
                    "op": "fill",
                    "to": tokens.PALETTE["highlight_fill"],
                    "duration": 0.3,
                }
            )
            narr = f"Visit {idx}"
        elif step.action == "edge":
            a = step.indices[0] if step.indices and len(step.indices) >= 1 else 0
            b = step.indices[1] if step.indices and len(step.indices) >= 2 else 1
            m.append(
                {
                    "target": f"edge_{a}_{b}",
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
            narr = f"Relax {step.indices}"
            m.append(
                {
                    "target": f"node_{step.indices[0] if step.indices else 0}",
                    "op": "scale",
                    "to": 1.05,
                    "duration": 0.25,
                }
            )
        else:
            m.append(
                {"target": f"{kind}_root", "op": "scale", "to": 1.0, "duration": 0.25}
            )
        beats.append({"narration": narr[:300], "shapes": [], "motion": m})
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


def plan_intervals(spec: AlgorithmAnimation) -> List[Dict[str, Any]]:
    beats: List[Dict[str, Any]] = [
        {
            "narration": f"{spec.title or spec.algorithm} — Intervals"[:300],
            "shapes": [],
            "motion": [{"target": "interval_0", "op": "appear", "duration": 0.4}],
            "camera": {"action": "reset"},
        }
    ]
    for step in spec.steps:
        m: List[Dict[str, Any]] = []
        narr = step.label or step.action
        if step.action in ("partition", "window"):
            m.append(
                {
                    "target": "interval_0",
                    "op": "stroke",
                    "to": tokens.PALETTE["accent"],
                    "duration": 0.3,
                }
            )
            narr = f"{step.action} {step.indices or [step.low, step.high]}"
        elif step.action == "visit":
            idx = int(step.index or 0)
            m.append(
                {
                    "target": f"interval_{idx}",
                    "op": "fill",
                    "to": tokens.PALETTE["highlight_fill"],
                    "duration": 0.3,
                }
            )
            narr = f"Visit interval {idx}"
        else:
            m.append(
                {"target": "interval_0", "op": "scale", "to": 1.0, "duration": 0.25}
            )
        beats.append({"narration": narr[:300], "shapes": [], "motion": m})
    beats.append(
        {
            "narration": f"{spec.complexity.time}"[:300],
            "shapes": [],
            "motion": [
                {"target": "interval_0", "op": "scale", "to": 1.0, "duration": 0.25}
            ],
            "badge": {"time": spec.complexity.time, "space": spec.complexity.space},
        }
    )
    return beats


# ── backtrack ────────────────────────────────────────────────────────────────


def plan_backtrack(spec: AlgorithmAnimation) -> List[Dict[str, Any]]:
    beats: List[Dict[str, Any]] = [
        {
            "narration": f"{spec.title or spec.algorithm} — Backtracking"[:300],
            "shapes": [],
            "motion": [{"target": "bt_root", "op": "appear", "duration": 0.4}],
            "camera": {"action": "reset"},
        }
    ]
    depth = 0
    for step in spec.steps:
        m: List[Dict[str, Any]] = []
        narr = step.label or step.action
        if step.action == "choose":
            idx = int(step.index or depth)
            m.append(
                {
                    "target": f"bt_{idx}",
                    "op": "fill",
                    "to": tokens.PALETTE["highlight_fill"],
                    "duration": 0.3,
                }
            )
            m.append(
                {
                    "target": f"bt_{idx}",
                    "op": "stroke",
                    "to": tokens.PALETTE["highlight_stroke"],
                    "duration": 0.3,
                }
            )
            narr = f"Choose [{idx}]"
            depth += 1
        elif step.action == "backtrack":
            idx = int(step.index or max(0, depth - 1))
            m.append(
                {
                    "target": f"bt_{idx}",
                    "op": "fill",
                    "to": tokens.PALETTE["dim_fill"],
                    "duration": 0.3,
                }
            )
            narr = f"Backtrack [{idx}]"
            depth = max(0, depth - 1)
        elif step.action == "visit":
            idx = int(step.index or 0)
            m.append(
                {
                    "target": f"bt_{idx}",
                    "op": "fill",
                    "to": tokens.PALETTE["highlight_fill"],
                    "duration": 0.3,
                }
            )
            narr = f"Visit {idx}"
        else:
            m.append({"target": "bt_root", "op": "scale", "to": 1.0, "duration": 0.25})
        beats.append({"narration": narr[:300], "shapes": [], "motion": m})
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
        return plan_searching(spec)
    if viz in ("bars", "array"):
        return plan_array(spec)
    if viz == "stack":
        return plan_stack(spec)
    if viz == "queue":
        return plan_stack(spec)  # queue reuses stack beats with shifted layout
    if viz == "linked_list":
        return plan_linked_list(spec)
    if viz == "tree":
        return plan_tree(spec)
    if viz == "graph":
        return plan_graph(spec, "graph")
    if viz == "grid":
        return plan_graph(spec, "grid")
    if viz == "intervals":
        return plan_intervals(spec)
    if viz == "backtrack":
        return plan_backtrack(spec)
    # Fallback: generic array beats so no algo renders empty
    return plan_array(spec)
