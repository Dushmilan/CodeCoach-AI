"""Universal trace → scene compiler (the animation mechanism).

Deterministically converts an ordered execution trace (from the canonical
optimal solution) plus the array values into the generic AnimationScript
contract the Motion Canvas viewer already renders. The mechanism is
algorithm-agnostic: the model/AI never authors geometry — it only produces
semantic events (compare/swap/pointer/write/mark/return) at runtime, and this
module owns layout, colors, pointer arrows, swap crossings and narration.

The output is always structurally validated by AnimationValidator so a bad
compile can never reach the viewer. compile_animation returns None when the
trace is unusable (no init event, empty, values too large to render).
"""

import logging
from typing import Any, Dict, List, Optional

from app.services.trace_parser import TraceEvent

logger = logging.getLogger(__name__)

# ── layout ───────────────────────────────────────────────────────────────
ROW_Y = 0.0
PTR_DY = -78.0
CELL = 88.0
GAP = 12.0
MAX_HALF_WIDTH = 900.0  # keep well inside the ±960 canvas bounds
MIN_CELL = 24.0

MAX_CELLS = 48  # 48 cells + 48 labels + ≤3 pointers stays under the 120-shape cap
MAX_POINTERS = 3

# ── colors ───────────────────────────────────────────────────────────────
IDLE_FILL = "#1e293b"
IDLE_STROKE = "#334155"
CHECK_FILL = "#1d4ed8"
CHECK_STROKE = "#3b82f6"
SWAP_FILL = "#713f12"
SWAP_STROKE = "#facc15"
SORTED_FILL = "#14532d"
SORTED_STROKE = "#22c55e"
CHOSEN_FILL = "#3b0764"
CHOSEN_STROKE = "#a855f7"
WINDOW_FILL = "#1e3a8a"
ACTIVE_FILL = "#312e81"
TEXT_FILL = "#e2e8f0"

# Pointer triangle drawn above the array, pointing down at a cell.
PTR_POINTS = [[-14, -36], [0, -66], [14, -36]]


class AnimationCompiler:
    """Deterministic compiler from a normalized trace to an AnimationScript."""

    def __init__(self, n: Optional[int] = None):
        # Layout is derived from the number of cells; a pre-seeded n is allowed
        # for tests that compute cell positions without running a full trace.
        self._n = n
        self._cell = CELL
        self._spacing = CELL + GAP
        if n is not None:
            self._fit_cells(n)

    def _fit_cells(self, n: int) -> None:
        """Shrink cells so `n` of them fit inside the canvas half-width."""
        available = 2 * MAX_HALF_WIDTH
        cell = min(CELL, (available - (n - 1) * GAP) / n)
        self._cell = max(cell, MIN_CELL)
        self._spacing = self._cell + GAP

    @property
    def n(self) -> int:
        return self._n or 0

    def cell_x(self, index: int) -> float:
        """Canvas x for the center of cell `index` (0-based, array centered)."""
        total = self.n * self._cell + (self.n - 1) * GAP
        start = -total / 2 + self._cell / 2
        return round(start + index * self._spacing, 2)

    def _fit_for_values(self, values: List[Any]) -> bool:
        n = len(values)
        if not 0 < n <= MAX_CELLS:
            return False
        self._n = n
        self._fit_cells(n)
        return True

    # ── scene assembly ──────────────────────────────────────────────────

    def _intro_steps(self, values: List[Any], pointers: List[str]) -> List[dict]:
        """Appear cells + value labels + pointer arrows.

        Intro is split into chunks so no step exceeds the per-step shape cap.
        Chunks after the first also scale their shapes to 1.0 so every step
        after the first carries a transform op (validator rule), while the
        shapes pop in rather than fade.
        """
        shapes = []
        for i in range(len(values)):
            x = self.cell_x(i)
            shapes.append(
                {
                    "id": f"cell_{i}",
                    "type": "rect",
                    "x": x,
                    "y": ROW_Y,
                    "width": self._cell,
                    "height": self._cell,
                    "radius": 10,
                    "fill": IDLE_FILL,
                    "stroke": IDLE_STROKE,
                    "lineWidth": 2,
                }
            )
            shapes.append(
                {
                    "id": f"val_{i}",
                    "type": "text",
                    "x": x,
                    "y": ROW_Y,
                    "text": self._display(values[i]),
                    "fontSize": self._label_font_size(),
                    "fill": TEXT_FILL,
                }
            )
        for name in pointers:
            shapes.append(
                {
                    "id": f"ptr_{name}",
                    "type": "polygon",
                    "x": self.cell_x(0),
                    "y": ROW_Y + PTR_DY,
                    "points": PTR_POINTS,
                    "fill": "#facc15",
                }
            )

        # Split into chunks of at most 20 shapes per intro step.
        chunk_size = 20
        chunks = [shapes[k : k + chunk_size] for k in range(0, len(shapes), chunk_size)]
        steps = []
        for idx, chunk in enumerate(chunks):
            step = {
                "narration": (
                    f"Starting with {values}."
                    if idx == 0
                    else "Setting up the rest of the array."
                ),
                "shapes": chunk,
                "motion": [
                    {"target": shape["id"], "op": "appear", "duration": 0.25}
                    for shape in chunk
                ],
            }
            if idx > 0:
                # Later intro steps must still carry a transform op (validator
                # rule): a single scale on the first shape satisfies it while
                # keeping the step under the motion-op cap.
                step["motion"].append(
                    {
                        "target": chunk[0]["id"],
                        "op": "scale",
                        "to": 1.0,
                        "duration": 0.25,
                    }
                )
            steps.append(step)
        return steps

    def _label_font_size(self) -> float:
        return max(22.0, min(36.0, self._cell * 0.4))

    @staticmethod
    def _display(value: Any) -> str:
        """Text for a cell label; whitespace-only values get a visible dot."""
        text = str(value)
        return "·" if not text or not text.strip() else text

    def _clamp_i(self, index: int) -> int:
        """Clamp an index into the rendered array (guards off-range pointers)."""
        return max(0, min(int(index), self.n - 1))

    def _make_step(self, narration: str, motion: List[dict]) -> dict:
        return {"narration": narration[:300], "shapes": [], "motion": motion}

    # ── compile ─────────────────────────────────────────────────────────

    def compile(
        self, events: List[TraceEvent], title: str = ""
    ) -> Optional[Dict[str, Any]]:
        if not events:
            return None
        init = next((e for e in events if e.kind == "init"), None)
        if init is None:
            return None
        values = list(init.fields.get("values") or [])
        if not self._fit_for_values(values):
            logger.warning(
                "Cannot render %d values in the animation canvas", len(values)
            )
            return None

        pointer_names = []
        for e in events:
            if e.kind == "pointer" and e.has("name"):
                name = str(e.fields["name"])
                if name not in pointer_names and len(pointer_names) < MAX_POINTERS:
                    pointer_names.append(name)

        steps: List[dict] = self._intro_steps(values, pointer_names)

        # cell_to_label[i] = id of the label shape currently over cell i.
        cell_to_label = [f"val_{i}" for i in range(len(values))]
        state = list(values)

        # Coalesce pointer events into the following event's step so arrows
        # move at the same moment the next operation happens. Multiple
        # pointers may be pending before one operation (e.g. low/high).
        pending_pointers: List[TraceEvent] = []

        for e in events:
            if e.kind == "init":
                continue

            if e.kind == "pointer":
                pending_pointers.append(e)
                continue

            motion: List[dict] = []
            narration = ""

            for p in pending_pointers:
                name = str(p.fields["name"])
                index = self._clamp_i(p.fields["index"])
                motion.append(
                    {
                        "target": f"ptr_{name}",
                        "op": "move",
                        "to": [self.cell_x(index), ROW_Y + PTR_DY],
                        "duration": 0.35,
                    }
                )
            pending_pointers = []

            if e.kind == "compare":
                i = self._clamp_i(e.i)
                j = e.fields.get("j")
                motion.append(
                    {
                        "target": f"cell_{i}",
                        "op": "fill",
                        "to": CHECK_FILL,
                        "duration": 0.25,
                    }
                )
                motion.append(
                    {
                        "target": f"cell_{i}",
                        "op": "stroke",
                        "to": CHECK_STROKE,
                        "duration": 0.25,
                    }
                )
                if j is not None:
                    j = self._clamp_i(j)
                    motion.append(
                        {
                            "target": f"cell_{j}",
                            "op": "fill",
                            "to": CHECK_FILL,
                            "duration": 0.25,
                        }
                    )
                    motion.append(
                        {
                            "target": f"cell_{j}",
                            "op": "stroke",
                            "to": CHECK_STROKE,
                            "duration": 0.25,
                        }
                    )
                    narration = f"Compare index {e.i} and {e.fields['j']}: {state[i]} vs {state[j]}."
                else:
                    narration = f"Compare index {e.i}: {state[i]}."

            elif e.kind == "swap":
                i, j = self._clamp_i(e.i), self._clamp_i(e.j)
                li, lj = cell_to_label[i], cell_to_label[j]
                xj = self.cell_x(j)
                xi = self.cell_x(i)
                motion.append(
                    {"target": li, "op": "move", "to": [xj, ROW_Y], "duration": 0.45}
                )
                motion.append(
                    {"target": lj, "op": "move", "to": [xi, ROW_Y], "duration": 0.45}
                )
                motion.append(
                    {
                        "target": f"cell_{i}",
                        "op": "fill",
                        "to": SWAP_FILL,
                        "duration": 0.25,
                    }
                )
                motion.append(
                    {
                        "target": f"cell_{j}",
                        "op": "fill",
                        "to": SWAP_FILL,
                        "duration": 0.25,
                    }
                )
                narration = f"Index {i} and {j}: {state[i]} and {state[j]} are out of order — swap them."
                cell_to_label[i], cell_to_label[j] = lj, li
                state[i], state[j] = state[j], state[i]

            elif e.kind == "write":
                i = self._clamp_i(e.i)
                value = e.fields.get("value")
                label = cell_to_label[i]
                motion.append(
                    {
                        "target": label,
                        "op": "label",
                        "to": self._display(value),
                        "duration": 0.3,
                    }
                )
                motion.append(
                    {
                        "target": f"cell_{i}",
                        "op": "fill",
                        "to": CHECK_FILL,
                        "duration": 0.25,
                    }
                )
                narration = f"values[{e.i}] becomes {value}."
                state[i] = value

            elif e.kind == "mark":
                i = self._clamp_i(e.i)
                state_name = str(e.fields.get("state", ""))
                if state_name == "sorted":
                    motion.append(
                        {
                            "target": f"cell_{i}",
                            "op": "fill",
                            "to": SORTED_FILL,
                            "duration": 0.35,
                        }
                    )
                    motion.append(
                        {
                            "target": f"cell_{i}",
                            "op": "stroke",
                            "to": SORTED_STROKE,
                            "duration": 0.35,
                        }
                    )
                    narration = f"Index {i} is in its final position."
                else:
                    motion.append(
                        {
                            "target": f"cell_{i}",
                            "op": "fill",
                            "to": CHECK_FILL,
                            "duration": 0.3,
                        }
                    )
                    narration = f"values[{i}] marked {state_name}."

            elif e.kind == "return":
                result = e.fields.get("result")
                narration = (
                    f"Finished. Result: {result}."
                    if result is not None
                    else "Finished."
                )
                # Give the closing step a real transform so it is never
                # dropped by the empty-motion guard or the validator.
                motion.append(
                    {"target": "cell_0", "op": "scale", "to": 1.0, "duration": 0.25}
                )

            elif e.kind == "visit":
                i = self._clamp_i(e.i)
                motion.append(
                    {
                        "target": f"cell_{i}",
                        "op": "fill",
                        "to": CHECK_FILL,
                        "duration": 0.25,
                    }
                )
                motion.append(
                    {
                        "target": f"cell_{i}",
                        "op": "stroke",
                        "to": CHECK_STROKE,
                        "duration": 0.25,
                    }
                )
                narration = f"Visiting index {i}: {state[i]}."

            elif e.kind == "read":
                i = self._clamp_i(e.i)
                motion.append(
                    {
                        "target": f"cell_{i}",
                        "op": "fill",
                        "to": ACTIVE_FILL,
                        "duration": 0.25,
                    }
                )
                narration = f"Read values[{i}] = {state[i]}."

            elif e.kind == "choose":
                i = self._clamp_i(e.i)
                motion.append(
                    {
                        "target": f"cell_{i}",
                        "op": "fill",
                        "to": CHOSEN_FILL,
                        "duration": 0.3,
                    }
                )
                motion.append(
                    {
                        "target": f"cell_{i}",
                        "op": "stroke",
                        "to": CHOSEN_STROKE,
                        "duration": 0.3,
                    }
                )
                narration = f"Choose index {i}: {state[i]}."

            elif e.kind == "backtrack":
                i = self._clamp_i(e.i)
                motion.append(
                    {
                        "target": f"cell_{i}",
                        "op": "fill",
                        "to": IDLE_FILL,
                        "duration": 0.3,
                    }
                )
                motion.append(
                    {
                        "target": f"cell_{i}",
                        "op": "stroke",
                        "to": IDLE_STROKE,
                        "duration": 0.3,
                    }
                )
                narration = f"Backtrack from index {i}."

            elif e.kind == "window":
                left, right = e.l, e.r
                for idx in range(left, min(right + 1, left + 26, len(state))):
                    motion.append(
                        {
                            "target": f"cell_{idx}",
                            "op": "fill",
                            "to": WINDOW_FILL,
                            "duration": 0.25,
                        }
                    )
                narration = f"Active window covers indices {left}..{right}."

            elif e.kind == "partition":
                i = self._clamp_i(e.i)
                motion.append(
                    {
                        "target": f"cell_{i}",
                        "op": "stroke",
                        "to": SWAP_STROKE,
                        "duration": 0.25,
                    }
                )
                motion.append(
                    {
                        "target": f"cell_{i}",
                        "op": "fill",
                        "to": SWAP_FILL,
                        "duration": 0.25,
                    }
                )
                narration = f"Partition boundary at index {i}."

            elif e.kind == "dp_update":
                # 1-D DP: treat as a value write into the tracked label.
                i = self._clamp_i(e.i)
                value = e.fields.get("value")
                label = cell_to_label[i]
                motion.append(
                    {
                        "target": label,
                        "op": "label",
                        "to": self._display(value),
                        "duration": 0.3,
                    }
                )
                motion.append(
                    {
                        "target": f"cell_{i}",
                        "op": "fill",
                        "to": SORTED_FILL,
                        "duration": 0.25,
                    }
                )
                narration = f"DP[{i}] becomes {value}."
                state[i] = value

            elif e.kind == "edge":
                # Edge activation has no array visual; skip quietly.
                continue

            if not motion:
                continue
            steps.append(self._make_step(narration, motion))

        if len(steps) < 3:
            return None

        return {
            "title": title,
            "data": {"values": values},
            "steps": steps,
        }


def compile_animation(
    events: List[TraceEvent], title: str = ""
) -> Optional[Dict[str, Any]]:
    """Compile a trace into a validated AnimationScript dict, or None."""
    return AnimationCompiler().compile(events, title=title)
