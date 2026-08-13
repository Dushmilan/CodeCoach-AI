"""Family compilers — turn a semantic trace into a validated generic scene.

One compiler per visualization family, each deterministically producing the
generic AnimationScript contract the Motion Canvas viewer already renders.
The canonical traced solution only emits semantic events at runtime
(push/pop, visit, edge, dp_update, choose/backtrack, compare/swap/...); this
module owns every visual: layout, colors, arrows, containers and narration.

All output is structurally validated by AnimationValidator before returning,
so a bad compile can never reach the viewer. ``compile_family`` returns None
when the trace is unusable (no init event, empty, structure too large).
"""

import logging
import math
from typing import Any, Dict, List, Optional

from app.services.trace_parser import TraceEvent
from app.services.animation_compiler import AnimationCompiler

logger = logging.getLogger(__name__)

# ── shared palette ──────────────────────────────────────────────────────────
IDLE_FILL = "#1e293b"
IDLE_STROKE = "#334155"
CHECK_FILL = "#1d4ed8"
CHECK_STROKE = "#3b82f6"
SWAP_FILL = "#713f12"
SWAP_STROKE = "#facc15"
DONE_FILL = "#14532d"
DONE_STROKE = "#22c55e"
ACTIVE_FILL = "#3b0764"
ACTIVE_STROKE = "#a855f7"
TEXT_FILL = "#e2e8f0"
MUTED_FILL = "#0f172a"

MAX_SHAPES_TOTAL = 60
MAX_STEP_SHAPES = 40
MAX_STEP_MOTIONS = 30

PTR_POINTS = [[-14, -36], [0, -66], [14, -36]]


def _rect(sid: str, x: float, y: float, w: float, h: float, **kw) -> dict:
    shape = {
        "id": sid,
        "type": "rect",
        "x": round(x, 2),
        "y": round(y, 2),
        "width": round(w, 2),
        "height": round(h, 2),
        "radius": kw.get("radius", 8),
        "fill": kw.get("fill", IDLE_FILL),
        "stroke": kw.get("stroke", IDLE_STROKE),
        "lineWidth": kw.get("lineWidth", 2),
    }
    if kw.get("opacity") is not None:
        shape["opacity"] = kw["opacity"]
    return shape


def _ellipse(sid: str, x: float, y: float, w: float, h: float, **kw) -> dict:
    shape = {
        "id": sid,
        "type": "ellipse",
        "x": round(x, 2),
        "y": round(y, 2),
        "width": round(w, 2),
        "height": round(h, 2),
        "fill": kw.get("fill", IDLE_FILL),
        "stroke": kw.get("stroke", IDLE_STROKE),
        "lineWidth": kw.get("lineWidth", 2),
    }
    return shape


def _text(sid: str, x: float, y: float, content: str, size: float, **kw) -> dict:
    return {
        "id": sid,
        "type": "text",
        "x": round(x, 2),
        "y": round(y, 2),
        "text": str(content)[:200],
        "fontSize": round(size, 2),
        "fill": kw.get("fill", TEXT_FILL),
    }


def _line(sid: str, points: List[List[float]], **kw) -> dict:
    return {
        "id": sid,
        "type": "line",
        "points": [[round(p[0], 2), round(p[1], 2)] for p in points],
        "stroke": kw.get("stroke", IDLE_STROKE),
        "lineWidth": kw.get("lineWidth", 2),
    }


def _polygon(sid: str, x: float, y: float, points: List[List[float]], **kw) -> dict:
    return {
        "id": sid,
        "type": "polygon",
        "x": round(x, 2),
        "y": round(y, 2),
        "points": points,
        "fill": kw.get("fill", "#facc15"),
    }


def _step(
    narration: str, motion: List[dict], shapes: Optional[List[dict]] = None
) -> dict:
    return {"narration": narration[:300], "shapes": shapes or [], "motion": motion}


def _split_intro(shapes: List[dict], first_narration: str) -> List[dict]:
    """Chunked appear intro; later chunks carry a scale transform (validator).

    Chunked at 15 shapes so each intro step stays under the 30-motion cap even
    for grids that create two shapes per cell.
    """
    steps = []
    for idx in range(0, len(shapes), 15):
        chunk = shapes[idx : idx + 15]
        motion = [
            {"target": shape["id"], "op": "appear", "duration": 0.25} for shape in chunk
        ]
        if idx > 0:
            motion.append(
                {"target": chunk[0]["id"], "op": "scale", "to": 1.0, "duration": 0.25}
            )
        steps.append(
            _step(
                first_narration
                if idx == 0
                else "Setting up the rest of the structure.",
                motion,
                chunk,
            )
        )
    return steps


def _clamp(total: int, max_total: int) -> int:
    return max(0, min(total, max_total))


def _init_events(events: List[TraceEvent]) -> List[TraceEvent]:
    return [e for e in events if e.kind == "init"]


# ── array / backtrack (delegates to the array compiler) ─────────────────────
def _compile_array(events: List[TraceEvent], title: str) -> Optional[Dict[str, Any]]:
    return AnimationCompiler().compile(events, title=title)


# ── stack ───────────────────────────────────────────────────────────────────
STACK_BOX_W = 110.0
STACK_BOX_H = 240.0
STACK_ITEM_H = 34.0
STACK_MAX_ITEMS = 10
STACK_MAX_OPS = 14


def _compile_stack(events: List[TraceEvent], title: str) -> Optional[Dict[str, Any]]:
    init = _init_events(events)
    if not init:
        return None
    data = init[0].fields.get("data")
    ops = list(data) if isinstance(data, (list, str)) else []
    if not ops:
        return None
    ops = [str(v) for v in ops][:STACK_MAX_OPS]

    n_ops = len(ops)
    cell_w = min(64.0, 2 * 380.0 / max(n_ops, 1))
    total_w = n_ops * cell_w + (n_ops - 1) * 8
    start_x = -total_w / 2 + cell_w / 2
    ops_y = -180.0
    box_x = 250.0
    box_y = 40.0

    shapes: List[dict] = []
    for i, op in enumerate(ops):
        x = round(start_x + i * (cell_w + 8), 2)
        shapes.append(_rect(f"op_{i}", x, ops_y, cell_w, 40, radius=6))
        shapes.append(_text(f"op_val_{i}", x, ops_y, op, 20))
    shapes.append(_rect("stack_box", box_x, box_y, STACK_BOX_W, STACK_BOX_H, radius=10))

    steps: List[dict] = _split_intro(shapes, f"Starting with operations {ops}.")

    stack_count = 0
    item_seq = 0
    stack_ids: List[int] = []
    for e in events:
        if e.kind in ("init", "pointer"):
            continue
        motion: List[dict] = []
        narration = ""
        if e.kind == "visit":
            i = int(e.i)
            if 0 <= i < n_ops:
                motion.append(
                    {
                        "target": f"op_{i}",
                        "op": "fill",
                        "to": CHECK_FILL,
                        "duration": 0.25,
                    }
                )
                motion.append(
                    {
                        "target": f"op_{i}",
                        "op": "stroke",
                        "to": CHECK_STROKE,
                        "duration": 0.25,
                    }
                )
            narration = f"Process operation {i}: {ops[i] if 0 <= i < n_ops else ''}."
        elif e.kind == "push":
            value = e.fields.get("value")
            new_shapes: List[dict] = []
            if stack_count < STACK_MAX_ITEMS:
                item_y = box_y + STACK_BOX_H - STACK_ITEM_H * (stack_count + 1)
                item_w = STACK_BOX_W - 20
                seq = item_seq
                item_seq += 1
                sid = f"stack_cell_{seq}"
                vid = f"stack_item_{seq}"
                stack_ids.append(seq)
                new_shapes.append(
                    _rect(
                        sid,
                        box_x,
                        box_y + STACK_BOX_H + 40,
                        item_w,
                        STACK_ITEM_H - 8,
                        radius=6,
                        fill=ACTIVE_FILL,
                        stroke=ACTIVE_STROKE,
                    )
                )
                new_shapes.append(
                    _text(vid, box_x, box_y + STACK_BOX_H + 40, str(value), 20)
                )
                motion.append({"target": sid, "op": "appear", "duration": 0.2})
                motion.append({"target": vid, "op": "appear", "duration": 0.2})
                motion.append(
                    {
                        "target": sid,
                        "op": "move",
                        "to": [box_x, item_y + (STACK_ITEM_H - 8) / 2],
                        "duration": 0.4,
                    }
                )
                motion.append(
                    {
                        "target": vid,
                        "op": "move",
                        "to": [box_x, item_y + (STACK_ITEM_H - 8) / 2],
                        "duration": 0.4,
                    }
                )
                stack_count += 1
            narration = f"Push {value} onto the stack."
            if not motion:
                continue
            steps.append(_step(narration, motion, new_shapes))
            continue
        elif e.kind == "pop":
            value = e.fields.get("value")
            if stack_count > 0 and stack_ids:
                stack_count -= 1
                seq = stack_ids.pop()
                sid = f"stack_cell_{seq}"
                vid = f"stack_item_{seq}"
                motion.append(
                    {
                        "target": sid,
                        "op": "move",
                        "to": [box_x, box_y + STACK_BOX_H + 70],
                        "duration": 0.4,
                    }
                )
                motion.append(
                    {
                        "target": vid,
                        "op": "move",
                        "to": [box_x, box_y + STACK_BOX_H + 70],
                        "duration": 0.4,
                    }
                )
                motion.append({"target": sid, "op": "disappear", "duration": 0.2})
                motion.append({"target": vid, "op": "disappear", "duration": 0.2})
                for k, bottom_seq in enumerate(stack_ids):
                    item_y = box_y + STACK_BOX_H - STACK_ITEM_H * (k + 1)
                    motion.append(
                        {
                            "target": f"stack_cell_{bottom_seq}",
                            "op": "move",
                            "to": [box_x, item_y + (STACK_ITEM_H - 8) / 2],
                            "duration": 0.3,
                        }
                    )
                    motion.append(
                        {
                            "target": f"stack_item_{bottom_seq}",
                            "op": "move",
                            "to": [box_x, item_y + (STACK_ITEM_H - 8) / 2],
                            "duration": 0.3,
                        }
                    )
            narration = f"Pop {value} off the stack."
        elif e.kind == "mark":
            i = int(e.i)
            state = str(e.fields.get("state", ""))
            if 0 <= i < n_ops:
                motion.append(
                    {
                        "target": f"op_{i}",
                        "op": "fill",
                        "to": DONE_FILL,
                        "duration": 0.3,
                    }
                )
                motion.append(
                    {
                        "target": f"op_{i}",
                        "op": "stroke",
                        "to": DONE_STROKE,
                        "duration": 0.3,
                    }
                )
            narration = f"Operation {i} marked {state}."
        elif e.kind == "return":
            result = e.fields.get("result")
            narration = (
                f"Finished. Result: {result}." if result is not None else "Finished."
            )
            motion.append(
                {"target": "stack_box", "op": "scale", "to": 1.0, "duration": 0.25}
            )
        if not motion:
            continue
        steps.append(_step(narration, motion))

    if len(steps) < 3:
        return None
    return {"title": title, "data": {"ops": ops, "family": "stack"}, "steps": steps}


# ── linked list ─────────────────────────────────────────────────────────────
LIST_MAX_NODES = 14
LIST_PTR_DY = -70.0


def _compile_linked_list(
    events: List[TraceEvent], title: str
) -> Optional[Dict[str, Any]]:
    init = _init_events(events)
    if not init:
        return None
    data = init[0].fields.get("data")
    values = list(data) if isinstance(data, (list, str)) else []
    values = values[:LIST_MAX_NODES]
    if not 0 < len(values) <= LIST_MAX_NODES:
        return None

    n = len(values)
    cell = min(88.0, (2 * 820.0 - (n - 1) * 12) / n)
    spacing = cell + 12.0
    total = n * cell + (n - 1) * 12
    start = -total / 2 + cell / 2

    def node_x(i: int) -> float:
        return round(start + i * spacing, 2)

    shapes: List[dict] = []
    for i, v in enumerate(values):
        x = node_x(i)
        shapes.append(_rect(f"node_{i}", x, 0, cell, cell, radius=10))
        shapes.append(_text(f"val_{i}", x, 0, str(v), max(20, min(30, cell * 0.38))))
    for i in range(n - 1):
        x1 = node_x(i) + cell / 2
        x2 = node_x(i + 1) - cell / 2
        shapes.append(
            _line(
                f"arrow_{i}",
                [[x1, 0], [x1 + 10, 0], [x2, 0], [x2 - 8, -6], [x2 - 8, 6], [x2, 0]],
                stroke="#64748b",
                lineWidth=2,
            )
        )
    null_x = node_x(n - 1) + spacing
    shapes.append(
        _rect(
            "null_node",
            null_x,
            0,
            cell,
            cell,
            radius=10,
            fill=MUTED_FILL,
            stroke="#475569",
        )
    )
    shapes.append(_text("null_val", null_x, 0, "null", 22))

    pointer_names: List[str] = []
    for e in events:
        if e.kind == "pointer" and e.has("name"):
            name = str(e.fields["name"])
            if name not in pointer_names and len(pointer_names) < 3:
                pointer_names.append(name)
    for name in pointer_names:
        shapes.append(_polygon(f"ptr_{name}", node_x(0), LIST_PTR_DY, PTR_POINTS))

    steps: List[dict] = _split_intro(shapes, f"Starting with the linked list {values}.")

    cell_to_label = [f"val_{i}" for i in range(n)]
    state = list(values)
    pending: List[TraceEvent] = []
    for e in events:
        if e.kind == "init":
            continue
        if e.kind == "pointer":
            pending.append(e)
            continue
        motion: List[dict] = []
        narration = ""
        for p in pending:
            name = str(p.fields["name"])
            idx = p.fields["index"]
            tx = node_x(idx) if isinstance(idx, int) and 0 <= idx < n else null_x
            motion.append(
                {
                    "target": f"ptr_{name}",
                    "op": "move",
                    "to": [tx, LIST_PTR_DY],
                    "duration": 0.35,
                }
            )
        pending = []
        if e.kind == "visit":
            i = int(e.i)
            motion.append(
                {
                    "target": f"node_{i}",
                    "op": "fill",
                    "to": CHECK_FILL,
                    "duration": 0.25,
                }
            )
            motion.append(
                {
                    "target": f"node_{i}",
                    "op": "stroke",
                    "to": CHECK_STROKE,
                    "duration": 0.25,
                }
            )
            narration = f"Visiting node {i}: {state[i]}."
        elif e.kind == "swap":
            i, j = int(e.i), int(e.j)
            li, lj = cell_to_label[i], cell_to_label[j]
            motion.append(
                {"target": li, "op": "move", "to": [node_x(j), 0], "duration": 0.45}
            )
            motion.append(
                {"target": lj, "op": "move", "to": [node_x(i), 0], "duration": 0.45}
            )
            motion.append(
                {"target": f"node_{i}", "op": "fill", "to": SWAP_FILL, "duration": 0.25}
            )
            motion.append(
                {"target": f"node_{j}", "op": "fill", "to": SWAP_FILL, "duration": 0.25}
            )
            narration = f"Swap values at positions {i} and {j}."
            cell_to_label[i], cell_to_label[j] = lj, li
            state[i], state[j] = state[j], state[i]
        elif e.kind == "write":
            i = int(e.i)
            value = e.fields.get("value")
            motion.append(
                {
                    "target": cell_to_label[i],
                    "op": "label",
                    "to": str(value),
                    "duration": 0.3,
                }
            )
            motion.append(
                {
                    "target": f"node_{i}",
                    "op": "fill",
                    "to": CHECK_FILL,
                    "duration": 0.25,
                }
            )
            narration = f"Position {i} becomes {value}."
            state[i] = value
        elif e.kind == "mark":
            i = int(e.i)
            motion.append(
                {"target": f"node_{i}", "op": "fill", "to": DONE_FILL, "duration": 0.35}
            )
            motion.append(
                {
                    "target": f"node_{i}",
                    "op": "stroke",
                    "to": DONE_STROKE,
                    "duration": 0.35,
                }
            )
            narration = f"Node {i} marked {e.fields.get('state', '')}."
        elif e.kind == "return":
            result = e.fields.get("result")
            narration = (
                f"Finished. Result: {result}." if result is not None else "Finished."
            )
            motion.append(
                {"target": "node_0", "op": "scale", "to": 1.0, "duration": 0.25}
            )
        if not motion:
            continue
        steps.append(_step(narration, motion))

    if len(steps) < 3:
        return None
    return {
        "title": title,
        "data": {"values": values, "family": "linked_list"},
        "steps": steps,
    }


# ── tree ────────────────────────────────────────────────────────────────────
TREE_MAX_NODES = 14
TREE_LEVEL_H = 96.0
TREE_WIDTH = 620.0
TREE_TOP = -240.0
TREE_PTR_DY = 30.0


def _tree_layout(n: int) -> List[Dict[str, float]]:
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


def _compile_tree(events: List[TraceEvent], title: str) -> Optional[Dict[str, Any]]:
    init = _init_events(events)
    if not init:
        return None
    data = init[0].fields.get("data")
    raw = list(data) if isinstance(data, (list, str)) else []
    raw = raw[:TREE_MAX_NODES]
    present = [i for i, v in enumerate(raw) if v is not None]
    if not present:
        return None
    positions = _tree_layout(max(present) + 1)
    cell = 44.0

    shapes: List[dict] = []
    for i in present:
        pos = positions[i]
        parent = (i - 1) // 2
        if parent >= 0 and parent in present:
            pp = positions[parent]
            shapes.append(
                _line(
                    f"tree_edge_{i}",
                    [[pp["x"], pp["y"] + cell / 2], [pos["x"], pos["y"] - cell / 2]],
                    stroke="#475569",
                    lineWidth=2,
                )
            )
    for i in present:
        pos = positions[i]
        shapes.append(_rect(f"node_{i}", pos["x"], pos["y"], cell, cell, radius=10))
        shapes.append(_text(f"val_{i}", pos["x"], pos["y"], str(raw[i]), 18))

    pointer_names: List[str] = []
    for e in events:
        if e.kind == "pointer" and e.has("name"):
            name = str(e.fields["name"])
            if name not in pointer_names and len(pointer_names) < 3:
                pointer_names.append(name)
    first_pos = positions[present[0]]
    for name in pointer_names:
        shapes.append(
            _polygon(
                f"ptr_{name}",
                first_pos["x"],
                first_pos["y"] + TREE_PTR_DY,
                [[-10, -18], [0, 6], [10, -18]],
                fill="#facc15",
            )
        )

    steps: List[dict] = _split_intro(shapes, f"Starting with the tree {raw}.")

    pending: List[TraceEvent] = []
    for e in events:
        if e.kind == "init":
            continue
        if e.kind == "pointer":
            pending.append(e)
            continue
        motion: List[dict] = []
        narration = ""
        for p in pending:
            name = str(p.fields["name"])
            idx = p.fields["index"]
            if isinstance(idx, int) and 0 <= idx <= max(present):
                pos = positions[idx]
                motion.append(
                    {
                        "target": f"ptr_{name}",
                        "op": "move",
                        "to": [pos["x"], pos["y"] + TREE_PTR_DY],
                        "duration": 0.35,
                    }
                )
        pending = []
        if e.kind == "visit":
            i = int(e.i)
            if i in present:
                motion.append(
                    {
                        "target": f"node_{i}",
                        "op": "fill",
                        "to": CHECK_FILL,
                        "duration": 0.25,
                    }
                )
                motion.append(
                    {
                        "target": f"node_{i}",
                        "op": "stroke",
                        "to": CHECK_STROKE,
                        "duration": 0.25,
                    }
                )
            narration = f"Visiting node {i}: {raw[i] if i < len(raw) else ''}."
        elif e.kind == "mark":
            i = int(e.i)
            if i in present:
                motion.append(
                    {
                        "target": f"node_{i}",
                        "op": "fill",
                        "to": DONE_FILL,
                        "duration": 0.35,
                    }
                )
                motion.append(
                    {
                        "target": f"node_{i}",
                        "op": "stroke",
                        "to": DONE_STROKE,
                        "duration": 0.35,
                    }
                )
            narration = f"Node {i} marked {e.fields.get('state', '')}."
        elif e.kind == "return":
            result = e.fields.get("result")
            narration = (
                f"Finished. Result: {result}." if result is not None else "Finished."
            )
            motion.append(
                {
                    "target": f"node_{present[0]}",
                    "op": "scale",
                    "to": 1.0,
                    "duration": 0.25,
                }
            )
        if not motion:
            continue
        steps.append(_step(narration, motion))

    if len(steps) < 3:
        return None
    return {"title": title, "data": {"values": raw, "family": "tree"}, "steps": steps}


# ── grid (matrix / DP table) ────────────────────────────────────────────────
GRID_MAX_CELLS = 20
GRID_CELL = 60.0
GRID_GAP = 8.0
GRID_Y = -80.0


def _compile_grid(events: List[TraceEvent], title: str) -> Optional[Dict[str, Any]]:
    init = _init_events(events)
    if not init:
        return None
    data = init[0].fields.get("data")
    if not isinstance(data, list) or not data or not isinstance(data[0], list):
        return None
    rows = len(data)
    cols = max(len(r) for r in data)
    while rows * cols > GRID_MAX_CELLS and cols > 1:
        cols -= 1
    while rows * cols > GRID_MAX_CELLS and rows > 1:
        rows -= 1
    if rows * cols == 0:
        return None

    cell_w = min(GRID_CELL, 2 * 420.0 / max(cols, 1))
    cell_h = min(GRID_CELL, 2 * 300.0 / max(rows, 1))
    total_w = cols * cell_w + (cols - 1) * GRID_GAP
    total_h = rows * cell_h + (rows - 1) * GRID_GAP
    x0 = -total_w / 2 + cell_w / 2
    y0 = GRID_Y - total_h / 2 + cell_h / 2

    def cell_x(c: int) -> float:
        return round(x0 + c * (cell_w + GRID_GAP), 2)

    def cell_y(r: int) -> float:
        return round(y0 + r * (cell_h + GRID_GAP), 2)

    shapes: List[dict] = []
    for r in range(rows):
        for c in range(cols):
            value = data[r][c] if r < len(data) and c < len(data[r]) else None
            x, y = cell_x(c), cell_y(r)
            shapes.append(_rect(f"cell_{r}_{c}", x, y, cell_w, cell_h, radius=6))
            shapes.append(
                _text(
                    f"val_{r}_{c}",
                    x,
                    y,
                    str(value) if value is not None else "",
                    max(14, min(22, cell_w * 0.35)),
                )
            )

    steps: List[dict] = _split_intro(shapes, f"Starting with the grid {rows}x{cols}.")

    for e in events:
        if e.kind == "init":
            continue
        motion: List[dict] = []
        narration = ""
        if e.kind == "return":
            result = e.fields.get("result")
            narration = (
                f"Finished. Result: {result}." if result is not None else "Finished."
            )
            motion.append(
                {"target": "cell_0_0", "op": "scale", "to": 1.0, "duration": 0.25}
            )
            steps.append(_step(narration, motion))
            continue
        r = getattr(e, "i", None)
        c = getattr(e, "j", None)
        if r is None:
            continue
        r = int(r)
        if c is None:
            c = 0
        else:
            c = int(c)
        if e.kind == "visit":
            if 0 <= r < rows and 0 <= c < cols:
                motion.append(
                    {
                        "target": f"cell_{r}_{c}",
                        "op": "fill",
                        "to": CHECK_FILL,
                        "duration": 0.25,
                    }
                )
                motion.append(
                    {
                        "target": f"cell_{r}_{c}",
                        "op": "stroke",
                        "to": CHECK_STROKE,
                        "duration": 0.25,
                    }
                )
            narration = f"Visiting cell ({r}, {c})."
        elif e.kind == "read":
            if 0 <= r < rows and 0 <= c < cols:
                motion.append(
                    {
                        "target": f"cell_{r}_{c}",
                        "op": "fill",
                        "to": ACTIVE_FILL,
                        "duration": 0.25,
                    }
                )
            narration = f"Read cell ({r}, {c})."
        elif e.kind == "backtrack":
            if 0 <= r < rows and 0 <= c < cols:
                motion.append(
                    {
                        "target": f"cell_{r}_{c}",
                        "op": "fill",
                        "to": IDLE_FILL,
                        "duration": 0.25,
                    }
                )
                motion.append(
                    {
                        "target": f"cell_{r}_{c}",
                        "op": "stroke",
                        "to": IDLE_STROKE,
                        "duration": 0.25,
                    }
                )
            narration = f"Backtrack from cell ({r}, {c})."
        elif e.kind in ("write", "dp_update"):
            value = e.fields.get("value")
            if 0 <= r < rows and 0 <= c < cols:
                motion.append(
                    {
                        "target": f"val_{r}_{c}",
                        "op": "label",
                        "to": str(value),
                        "duration": 0.3,
                    }
                )
                motion.append(
                    {
                        "target": f"cell_{r}_{c}",
                        "op": "fill",
                        "to": DONE_FILL,
                        "duration": 0.3,
                    }
                )
            narration = f"Cell ({r}, {c}) becomes {value}."
        elif e.kind == "mark":
            if 0 <= r < rows and 0 <= c < cols:
                motion.append(
                    {
                        "target": f"cell_{r}_{c}",
                        "op": "fill",
                        "to": DONE_FILL,
                        "duration": 0.3,
                    }
                )
                motion.append(
                    {
                        "target": f"cell_{r}_{c}",
                        "op": "stroke",
                        "to": DONE_STROKE,
                        "duration": 0.3,
                    }
                )
            narration = f"Cell ({r}, {c}) marked {e.fields.get('state', '')}."
        if not motion:
            continue
        steps.append(_step(narration, motion))

    if len(steps) < 3:
        return None
    return {
        "title": title,
        "data": {"rows": rows, "cols": cols, "family": "grid"},
        "steps": steps,
    }


# ── graph ───────────────────────────────────────────────────────────────────
GRAPH_MAX_VERTICES = 8
GRAPH_MAX_EDGES = 16
GRAPH_RADIUS = 230.0


def _compile_graph(events: List[TraceEvent], title: str) -> Optional[Dict[str, Any]]:
    init = _init_events(events)
    if not init:
        return None
    data = init[0].fields.get("data")
    if not isinstance(data, list) or not data:
        return None
    n = init[0].fields.get("n")
    explicit_n = n is not None
    if n is not None:
        n = int(n)

    flat = []
    for entry in data:
        if isinstance(entry, (list, tuple)):
            for v in entry:
                try:
                    flat.append(int(v))
                except (TypeError, ValueError):
                    continue
        else:
            try:
                flat.append(int(entry))
            except (TypeError, ValueError):
                continue
    mx = max(flat, default=0)

    if n is None:
        # Without an explicit vertex count, treat the data as an adjacency
        # list whose length is the vertex count (clone-graph style).
        n = len(data)

    adjacency: List[List[int]] = [[] for _ in range(n)]
    # 1-indexed inputs (clone-graph node labels) shift down by one when any
    # referenced id equals or exceeds the vertex count.
    shift = 1 if mx >= n else 0
    if not explicit_n and n > 0:
        # Adjacency list (clone-graph style, no explicit vertex count): row r
        # lists r's neighbors.
        for r in range(n):
            row = data[r] if r < len(data) and isinstance(data[r], list) else []
            for b in row:
                try:
                    b = int(b) - shift
                except (TypeError, ValueError):
                    continue
                if 0 <= b < n and b != r and b not in adjacency[r]:
                    adjacency[r].append(b)
    else:
        # Edge list (course-schedule style, explicit vertex count): each entry
        # is an [a, b] pair. The old len(data) == n heuristic was ambiguous —
        # an edge list with as many edges as vertices was misread as an
        # adjacency list, silently dropping edges.
        for entry in data:
            if not isinstance(entry, (list, tuple)) or len(entry) < 2:
                continue
            try:
                a, b = int(entry[0]) - shift, int(entry[1]) - shift
            except (TypeError, ValueError):
                continue
            if 0 <= a < n and 0 <= b < n and a != b and b not in adjacency[a]:
                adjacency[a].append(b)

    n = min(len(adjacency), GRAPH_MAX_VERTICES)
    positions = []
    for i in range(n):
        angle = 2 * math.pi * i / n - math.pi / 2
        positions.append(
            (
                round(GRAPH_RADIUS * math.cos(angle), 2),
                round(GRAPH_RADIUS * math.sin(angle), 2),
            )
        )

    edge_pairs = set()
    for a in range(n):
        for b in adjacency[a]:
            edge_pairs.add(tuple(sorted((a, b))))
    edge_pairs = sorted(edge_pairs)[:GRAPH_MAX_EDGES]

    shapes: List[dict] = []
    for a, b in edge_pairs:
        xa, ya = positions[a]
        xb, yb = positions[b]
        shapes.append(
            _line(f"ge_{a}_{b}", [[xa, ya], [xb, yb]], stroke="#475569", lineWidth=2)
        )
    for i in range(n):
        x, y = positions[i]
        shapes.append(_ellipse(f"g_node_{i}", x, y, 64, 64))
        shapes.append(_text(f"g_val_{i}", x, y, str(i), 22))

    steps: List[dict] = _split_intro(shapes, f"Starting with {n} vertices.")

    for e in events:
        if e.kind == "init":
            continue
        motion: List[dict] = []
        narration = ""
        if e.kind == "visit":
            i = int(e.i)
            if 0 <= i < n:
                motion.append(
                    {
                        "target": f"g_node_{i}",
                        "op": "fill",
                        "to": CHECK_FILL,
                        "duration": 0.25,
                    }
                )
                motion.append(
                    {
                        "target": f"g_node_{i}",
                        "op": "stroke",
                        "to": CHECK_STROKE,
                        "duration": 0.25,
                    }
                )
            narration = f"Visiting vertex {i}."
        elif e.kind == "edge":
            a, b = int(e.a), int(e.b)
            key = tuple(sorted((a, b)))
            if key in edge_pairs:
                motion.append(
                    {
                        "target": f"ge_{key[0]}_{key[1]}",
                        "op": "stroke",
                        "to": SWAP_STROKE,
                        "duration": 0.3,
                    }
                )
            narration = f"Traversing the edge between {a} and {b}."
        elif e.kind == "mark":
            i = int(e.i)
            if 0 <= i < n:
                motion.append(
                    {
                        "target": f"g_node_{i}",
                        "op": "fill",
                        "to": DONE_FILL,
                        "duration": 0.3,
                    }
                )
                motion.append(
                    {
                        "target": f"g_node_{i}",
                        "op": "stroke",
                        "to": DONE_STROKE,
                        "duration": 0.3,
                    }
                )
            narration = f"Vertex {i} marked {e.fields.get('state', '')}."
        elif e.kind == "return":
            result = e.fields.get("result")
            narration = (
                f"Finished. Result: {result}." if result is not None else "Finished."
            )
            motion.append(
                {"target": "g_node_0", "op": "scale", "to": 1.0, "duration": 0.25}
            )
        if not motion:
            continue
        steps.append(_step(narration, motion))

    if len(steps) < 3:
        return None
    return {"title": title, "data": {"vertices": n, "family": "graph"}, "steps": steps}


# ── intervals ───────────────────────────────────────────────────────────────
IV_MAX = 10
IV_WIDTH = 700.0
IV_Y0 = -160.0
IV_H = 40.0
IV_GAP = 18.0


def _compile_intervals(
    events: List[TraceEvent], title: str
) -> Optional[Dict[str, Any]]:
    init = _init_events(events)
    if not init:
        return None
    data = init[0].fields.get("data")
    if not isinstance(data, list):
        return None
    intervals = []
    for item in data:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            intervals.append((int(item[0]), int(item[1])))
    intervals = intervals[:IV_MAX]
    if not intervals:
        return None

    lo = min(s for s, _ in intervals)
    hi = max(e for _, e in intervals)
    span = max(hi - lo, 1)

    def bar_x(start: int) -> float:
        return round(-IV_WIDTH / 2 + (start - lo) * IV_WIDTH / span, 2)

    def bar_w(start: int, end: int) -> float:
        return max(20.0, round((end - start) * IV_WIDTH / span, 2))

    shapes: List[dict] = []
    for i, (s, e) in enumerate(intervals):
        y = IV_Y0 + i * (IV_H + IV_GAP)
        x = bar_x(s)
        shapes.append(_rect(f"bar_{i}", x, y, bar_w(s, e), IV_H, radius=6))
        shapes.append(_text(f"bar_val_{i}", x + bar_w(s, e) / 2, y, f"[{s},{e}]", 16))
    shapes.append(
        _polygon(
            "ptr_i",
            bar_x(lo),
            IV_Y0 + IV_H + IV_GAP,
            [[-12, -22], [0, 0], [12, -22]],
            fill="#facc15",
        )
    )

    steps: List[dict] = _split_intro(shapes, f"Starting with intervals {intervals}.")

    for e in events:
        if e.kind in ("init", "pointer"):
            continue
        motion: List[dict] = []
        narration = ""
        if e.kind == "visit":
            i = int(e.i)
            if 0 <= i < len(intervals):
                motion.append(
                    {
                        "target": f"bar_{i}",
                        "op": "fill",
                        "to": CHECK_FILL,
                        "duration": 0.25,
                    }
                )
            narration = f"Considering interval {intervals[i] if 0 <= i < len(intervals) else ''}."
        elif e.kind == "mark":
            i = int(e.i)
            state = str(e.fields.get("state", ""))
            if 0 <= i < len(intervals):
                motion.append(
                    {
                        "target": f"bar_{i}",
                        "op": "fill",
                        "to": DONE_FILL,
                        "duration": 0.3,
                    }
                )
            narration = f"Interval {i} marked {state}."
        elif e.kind == "return":
            result = e.fields.get("result")
            narration = (
                f"Finished. Result: {result}." if result is not None else "Finished."
            )
            motion.append(
                {"target": "bar_0", "op": "scale", "to": 1.0, "duration": 0.25}
            )
        if not motion:
            continue
        steps.append(_step(narration, motion))

    if len(steps) < 3:
        return None
    return {
        "title": title,
        "data": {"intervals": intervals, "family": "intervals"},
        "steps": steps,
    }


FAMILY_COMPILERS: Dict[str, Any] = {
    "array": _compile_array,
    "backtrack": _compile_array,
    "stack": _compile_stack,
    "linked_list": _compile_linked_list,
    "tree": _compile_tree,
    "grid": _compile_grid,
    "graph": _compile_graph,
    "intervals": _compile_intervals,
}


def family_of(events: List[TraceEvent]) -> Optional[str]:
    init = _init_events(events)
    if not init:
        return None
    return init[0].fields.get("family")


def compile_family(
    family: str,
    events: List[TraceEvent],
    title: str = "",
) -> Optional[Dict[str, Any]]:
    """Compile a trace for a visualization family into a validated scene, or None."""
    if not events:
        return None
    resolved = family or family_of(events) or ""
    compiler = FAMILY_COMPILERS.get(resolved)
    if compiler is None:
        logger.warning("No family compiler for %r", resolved)
        return None
    try:
        return compiler(events, title=title)
    except Exception as exc:  # noqa: BLE001 - a bad trace must never 500
        logger.warning("Family compile failed (%s): %s", resolved, exc)
        return None
