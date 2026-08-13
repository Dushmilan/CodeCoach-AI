"""Unit tests for the trace→scene compiler.

The compiler is the universal animation mechanism: it takes an ordered
execution trace (from the canonical solution) plus the array values and
deterministically produces the generic AnimationScript the viewer already
renders. The output must always pass AnimationValidator so no structurally
broken scene can reach the viewer.

Semantics exercised here:

- init   → intro step that appears the array cells, value labels and pointers.
- compare→ highlight the two cells (checking color) + narration.
- swap   → the two values' labels cross to the other cell (animated move).
- write  → the label at that index changes to the new value.
- pointer→ the named pointer arrow moves to the index.
- mark   → cell enters a state (sorted = green).
- return → closing narration.

Because a swap physically moves labels, later write/compare ops must keep
tracking which label currently sits at each index.
"""

import json

from app.services.trace_parser import parse_trace
from app.services.animation_compiler import (
    AnimationCompiler,
    compile_animation,
)
from app.services.animation_validator import AnimationValidator


def _trace(stdout):
    return parse_trace(stdout)


def _bubble_trace():
    lines = [
        '{"event":"init","values":[5,1,4,2,8]}',
        '{"event":"pointer","name":"j","index":0}',
        '{"event":"compare","i":0,"j":1}',
        '{"event":"swap","i":0,"j":1}',
        '{"event":"pointer","name":"j","index":1}',
        '{"event":"compare","i":1,"j":2}',
        '{"event":"swap","i":1,"j":2}',
        '{"event":"pointer","name":"j","index":2}',
        '{"event":"compare","i":2,"j":3}',
        '{"event":"pointer","name":"j","index":3}',
        '{"event":"compare","i":3,"j":4}',
        '{"event":"mark","i":4,"state":"sorted"}',
        '{"event":"return","result":[1,2,4,5,8]}',
    ]
    return parse_trace("\n".join(lines))


def _validated(animation):
    validated, reason = AnimationValidator().validate(animation)
    assert validated is not None, f"compiled scene must validate: {reason}"
    return validated


def _ids_in(step):
    ids = {shape["id"] for shape in step.get("shapes", [])}
    ids.update(op["target"] for op in step.get("motion", []))
    return ids


class TestCompileAnimation:
    def test_bubble_sort_trace_produces_valid_scene(self):
        animation = _validated(compile_animation(_bubble_trace(), title="Bubble Sort"))
        assert animation["title"] == "Bubble Sort"
        assert len(animation["steps"]) >= 3
        first = animation["steps"][0]
        # Intro step appears every cell + label + pointer.
        ids = _ids_in(first)
        for i in range(5):
            assert f"cell_{i}" in ids
            assert f"val_{i}" in ids
        assert "ptr_j" in ids

    def test_values_render_inside_labels(self):
        animation = _validated(compile_animation(_bubble_trace()))
        first = animation["steps"][0]
        texts = {
            shape["text"]: shape["id"]
            for shape in first["shapes"]
            if shape["type"] == "text" and shape["id"].startswith("val_")
        }
        assert texts.get("5") == "val_0"
        assert texts.get("8") == "val_4"

    def test_compare_step_highlights_both_cells(self):
        animation = _validated(compile_animation(_bubble_trace()))
        # Find the step after the first that is a compare (narration contains "Compare").
        compare_step = next(
            s
            for s in animation["steps"][1:]
            if s["narration"].startswith("Compare index 0")
        )
        targets = {op["target"] for op in compare_step["motion"]}
        assert "cell_0" in targets
        assert "cell_1" in targets
        fills = {op["to"] for op in compare_step["motion"] if op["op"] == "fill"}
        assert any("#" in f for f in fills)

    def test_swap_crosses_value_labels(self):
        animation = _validated(compile_animation(_bubble_trace()))
        swap_step = next(
            s
            for s in animation["steps"][1:]
            if "swap" in s["narration"].lower() and "index 0" in s["narration"].lower()
        )
        moves = {
            op["target"]: op["to"] for op in swap_step["motion"] if op["op"] == "move"
        }
        assert "val_0" in moves and "val_1" in moves
        # They cross: label 0 ends at cell 1, label 1 at cell 0.
        assert moves["val_0"] != moves["val_1"]
        assert moves["val_0"][0] == AnimationCompiler(n=5).cell_x(1)
        assert moves["val_1"][0] == AnimationCompiler(n=5).cell_x(0)

    def test_sorted_mark_greens_the_cell(self):
        animation = _validated(compile_animation(_bubble_trace()))
        mark_step = next(
            s for s in animation["steps"][1:] if "final position" in s["narration"]
        )
        fills = {op["to"] for op in mark_step["motion"] if op["op"] == "fill"}
        assert "#14532d" in fills

    def test_write_updates_label_at_tracked_index(self):
        trace = _trace(
            "\n".join(
                [
                    '{"event":"init","values":[1,2,3]}',
                    '{"event":"compare","i":0,"j":1}',
                    '{"event":"swap","i":0,"j":1}',
                    '{"event":"write","i":1,"value":99}',
                    '{"event":"return","result":[2,99,3]}',
                ]
            )
        )
        animation = _validated(compile_animation(trace))
        write_step = next(
            s for s in animation["steps"][1:] if "becomes 99" in s["narration"]
        )
        label_ops = [op for op in write_step["motion"] if op["op"] == "label"]
        assert label_ops, "write must relabel a value"
        assert label_ops[0]["to"] == "99"

    def test_pointer_event_moves_arrow(self):
        trace = _trace(
            "\n".join(
                [
                    '{"event":"init","values":[9,1,5]}',
                    '{"event":"pointer","name":"low","index":0}',
                    '{"event":"pointer","name":"high","index":2}',
                    '{"event":"compare","i":0,"j":2}',
                    '{"event":"return","result":[9,1,5]}',
                ]
            )
        )
        animation = _validated(compile_animation(trace))
        first = animation["steps"][0]
        ids = _ids_in(first)
        assert "ptr_low" in ids and "ptr_high" in ids
        # high pointer moves to index 2.
        moves = [
            o
            for s in animation["steps"]
            for o in s["motion"]
            if o["target"] == "ptr_high" and o["op"] == "move"
        ]
        assert moves
        assert abs(moves[0]["to"][0] - AnimationCompiler(n=3).cell_x(2)) < 1e-6

    def test_many_values_shrink_cells_within_bounds(self):
        values = list(range(1, 26))
        init = json.dumps({"event": "init", "values": values})
        ret = json.dumps({"event": "return", "result": values})
        trace = parse_trace(init + "\n" + ret)
        animation = _validated(compile_animation(trace))
        # Intro is split across steps so each stays under the per-step cap.
        rects = [
            shape
            for step in animation["steps"]
            for shape in step.get("shapes", [])
            if shape["type"] == "rect"
        ]
        assert len(rects) == len(values)
        for shape in rects:
            assert -960 <= shape["x"] <= 960

    def test_compile_requires_an_init_event(self):
        trace = parse_trace('{"event":"compare","i":0,"j":1}')
        assert compile_animation(trace, title="x") is None

    def test_compile_returns_none_for_empty_trace(self):
        assert compile_animation([], title="x") is None

    def test_default_compiler_instance(self):
        assert isinstance(AnimationCompiler(), AnimationCompiler)
