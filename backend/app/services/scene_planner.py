"""Scene Planner — semantic AlgorithmAnimation steps → cinematic SceneBeats.

Beats are still generic AnimationScript steps (narration/shapes/motion) but
planned with visual hierarchy: ARRAY APPEARS → MID ENTERS → RELATION →
DISCARD → CAMERA FOCUS → NEXT. The planner decides pacing; the Design System
decides how each primitive looks.

Searching template (binary search) is the first polished template.
Sorting / Graphs are placeholders for Phase 2.
"""

from typing import Any, Dict, List

from app.models.animation_spec import AlgorithmAnimation
from app.services import animation_design_tokens as tokens


def _cell_x(index: int, n: int, cell: float = 88.0, gap: float = 12.0) -> float:
    total = n * cell + (n - 1) * gap
    start = -total / 2 + cell / 2
    return round(start + index * (cell + gap), 2)


def plan_searching(spec: AlgorithmAnimation) -> List[Dict[str, Any]]:
    """Plan binary-search beats with camera + typography hierarchy.

    Input example:
      initialState: {array: [2,4,7,9,13,18,21], target: 13}
      steps: [set_bounds low=0 high=6, inspect_mid index=3, discard_left until=4, ...]

    Output: List[AnimationStep] dicts consumable by viewer.tsx renderSearchingScene
    (shapes/motion) and validated by AnimationValidator.
    """
    arr = list(spec.initialState.array or [])
    n = len(arr)
    if n == 0:
        return []

    target = spec.initialState.target
    title = spec.title or spec.algorithm.replace("-", " ").title()

    # Beat 0: ARRAY APPEARS — staggered enter
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

    # Follow semantic steps — each becomes a cinematic beat
    for step in spec.steps:
        narr = ""
        m: List[Dict[str, Any]] = []
        camera: Dict[str, Any] | None = None

        if step.action == "set_bounds":
            low, high = step.low or 0, step.high or (n - 1)
            # Focus search region — camera + highlight region
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
            # Dim discarded half — visual hierarchy
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
            # Camera pans to remaining region
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
            # Generic fallback — keep beat valid with a transform op
            m.append({"target": "cell_0", "op": "scale", "to": 1.0, "duration": 0.25})
            narr = step.label or step.action

        beat: Dict[str, Any] = {"narration": narr[:300], "shapes": [], "motion": m}
        if camera:
            beat["camera"] = camera
        beats.append(beat)

    # Final complexity badge beat
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


def plan(spec: AlgorithmAnimation) -> List[Dict[str, Any]]:
    """Dispatch to template planner."""
    if spec.visualization == "sorted-array":
        return plan_searching(spec)
    # Sorting / Graphs placeholders — return empty to force fallback to generic
    # compiler until Phase 2 implements them.
    return []
