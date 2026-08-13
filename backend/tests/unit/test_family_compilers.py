"""Unit tests for the family compilers (stack/list/tree/grid/graph/intervals/
backtrack).

Every family compiler deterministically turns an ordered semantic trace into a
generic AnimationScript that must always pass AnimationValidator — the same
structural gate the array compiler's output passes. Each family renders its
structure with rect/ellipse/line/polygon/text primitives and animates
semantic events (push/pop, visit, edge, dp_update, choose/backtrack ...) by
moving/filling/relabeling existing shapes.
"""

import json

from app.services.trace_parser import parse_trace
from app.services.family_compilers import compile_family
from app.services.animation_validator import AnimationValidator


def _validated(animation):
    assert animation is not None, "family scene must compile"
    validated, reason = AnimationValidator().validate(animation)
    assert validated is not None, f"family scene must validate: {reason}"
    return validated


def _ids_in(step):
    ids = {shape["id"] for shape in step.get("shapes", [])}
    ids.update(op["target"] for op in step.get("motion", []))
    return ids


def _all_ids(animation):
    ids = set()
    for step in animation["steps"]:
        ids.update(_ids_in(step))
    return ids


class TestStackFamily:
    def test_push_pop_trace_produces_valid_scene(self):
        trace = parse_trace(
            "\n".join(
                [
                    '{"event":"init","data":["(","(",")","]"],"family":"stack"}',
                    '{"event":"push","value":"("}',
                    '{"event":"push","value":"("}',
                    '{"event":"pop","value":"("}',
                    '{"event":"return","result":false}',
                ]
            )
        )
        animation = _validated(compile_family("stack", trace, title="Valid Parens"))
        ids = _all_ids(animation)
        assert "stack_box" in ids
        assert any(sid.startswith("stack_item_") for sid in ids)
        first = animation["steps"][0]
        assert any(s["id"] == "stack_box" for s in first["shapes"])

    def test_stack_push_appends_item_and_moves(self):
        trace = parse_trace(
            "\n".join(
                [
                    '{"event":"init","data":["(",")"],"family":"stack"}',
                    '{"event":"push","value":"("}',
                    '{"event":"return","result":true}',
                ]
            )
        )
        animation = _validated(compile_family("stack", trace))
        push_step = next(
            s
            for s in animation["steps"]
            if any(op["op"] == "move" for op in s["motion"])
        )
        targets = {op["target"] for op in push_step["motion"]}
        assert any(sid.startswith("stack_item_") for sid in targets)


class TestLinkedListFamily:
    def test_reverse_trace_produces_valid_scene(self):
        trace = parse_trace(
            "\n".join(
                [
                    '{"event":"init","data":[1,2,3,4,5],"family":"linked_list"}',
                    '{"event":"pointer","name":"prev","index":0}',
                    '{"event":"visit","i":0}',
                    '{"event":"pointer","name":"prev","index":1}',
                    '{"event":"visit","i":1}',
                    '{"event":"return","result":[5,4,3,2,1]}',
                ]
            )
        )
        animation = _validated(compile_family("linked_list", trace, title="Reverse"))
        ids = _all_ids(animation)
        for i in range(5):
            assert f"node_{i}" in ids
            assert f"val_{i}" in ids
        assert "null_node" in ids
        assert "ptr_prev" in ids
        # Visit highlights a node.
        visit_step = next(
            s for s in animation["steps"][1:] if "Visiting" in s["narration"]
        )
        assert any(op["op"] == "fill" for op in visit_step["motion"])

    def test_swap_crosses_node_labels(self):
        trace = parse_trace(
            "\n".join(
                [
                    '{"event":"init","data":[1,2],"family":"linked_list"}',
                    '{"event":"swap","i":0,"j":1}',
                    '{"event":"return","result":[2,1]}',
                ]
            )
        )
        animation = _validated(compile_family("linked_list", trace))
        swap_step = next(
            s for s in animation["steps"][1:] if "swap" in s["narration"].lower()
        )
        moves = {
            op["target"]: op["to"] for op in swap_step["motion"] if op["op"] == "move"
        }
        assert "val_0" in moves and "val_1" in moves


class TestTreeFamily:
    def test_visit_trace_produces_valid_scene(self):
        trace = parse_trace(
            "\n".join(
                [
                    '{"event":"init","data":[3,9,20,null,null,15,7],"family":"tree"}',
                    '{"event":"pointer","name":"current","index":0}',
                    '{"event":"visit","i":0}',
                    '{"event":"visit","i":2}',
                    '{"event":"return","result":3}',
                ]
            )
        )
        animation = _validated(compile_family("tree", trace, title="Max Depth"))
        ids = _all_ids(animation)
        assert "node_0" in ids and "node_2" in ids
        assert any(sid.startswith("tree_edge_") for sid in ids)
        visit_step = next(
            s for s in animation["steps"][1:] if "Visiting" in s["narration"]
        )
        assert any(op["op"] == "fill" for op in visit_step["motion"])


class TestGridFamily:
    def test_dp_update_trace_produces_valid_scene(self):
        trace = parse_trace(
            "\n".join(
                [
                    '{"event":"init","data":[[0,0],[0,0]],"family":"grid"}',
                    '{"event":"dp_update","i":1,"j":1,"value":5}',
                    '{"event":"return","result":5}',
                ]
            )
        )
        animation = _validated(compile_family("grid", trace, title="DP"))
        ids = _all_ids(animation)
        assert "cell_0_0" in ids and "cell_1_1" in ids
        update_step = next(
            s for s in animation["steps"][1:] if "becomes 5" in s["narration"]
        )
        assert any(op["op"] == "label" for op in update_step["motion"])

    def test_visit_uses_row_col(self):
        trace = parse_trace(
            "\n".join(
                [
                    '{"event":"init","data":[["A","B"],["C","D"]],"family":"grid"}',
                    '{"event":"visit","i":1,"j":0}',
                    '{"event":"return","result":true}',
                ]
            )
        )
        animation = _validated(compile_family("grid", trace))
        visit_step = next(
            s for s in animation["steps"][1:] if "Visiting" in s["narration"]
        )
        targets = {op["target"] for op in visit_step["motion"]}
        assert "cell_1_0" in targets


class TestGraphFamily:
    def test_visit_edge_trace_produces_valid_scene(self):
        trace = parse_trace(
            "\n".join(
                [
                    '{"event":"init","data":[[2,4],[1,3],[2,4],[1,3]],"family":"graph"}',
                    '{"event":"visit","i":0}',
                    '{"event":"edge","a":0,"b":1}',
                    '{"event":"visit","i":1}',
                    '{"event":"return","result":4}',
                ]
            )
        )
        animation = _validated(compile_family("graph", trace, title="Clone"))
        ids = _all_ids(animation)
        for i in range(4):
            assert f"g_node_{i}" in ids
        assert "ge_0_1" in ids
        edge_step = next(
            s for s in animation["steps"][1:] if "edge" in s["narration"].lower()
        )
        assert any(op["op"] == "stroke" for op in edge_step["motion"])

    def test_edge_list_with_explicit_n_is_not_misread_as_adjacency(self):
        # course_schedule emits data=prerequisites (edge list) + n=numCourses.
        # When len(edges) == numCourses the old len(data) == n heuristic fell
        # into the adjacency branch, dropping real edges (here 0-2).
        trace = parse_trace(
            "\n".join(
                [
                    '{"event":"init","data":[[0,1],[0,2],[2,1]],"family":"graph","n":3}',
                    '{"event":"edge","a":0,"b":1}',
                    '{"event":"edge","a":0,"b":2}',
                    '{"event":"return","result":true}',
                ]
            )
        )
        animation = _validated(compile_family("graph", trace, title="Courses"))
        ids = _all_ids(animation)
        for pair in ("0_1", "0_2", "1_2"):
            assert f"ge_{pair}" in ids, f"missing edge ge_{pair}"
        edge_ids = [sid for sid in ids if sid.startswith("ge_")]
        assert len(edge_ids) == 3


class TestIntervalsFamily:
    def test_merge_trace_produces_valid_scene(self):
        trace = parse_trace(
            "\n".join(
                [
                    '{"event":"init","data":[[1,3],[2,6],[8,10]],"family":"intervals"}',
                    '{"event":"pointer","name":"i","index":0}',
                    '{"event":"visit","i":0}',
                    '{"event":"mark","i":0,"state":"merged"}',
                    '{"event":"return","result":[[1,6],[8,10]]}',
                ]
            )
        )
        animation = _validated(
            compile_family("intervals", trace, title="Merge Intervals")
        )
        ids = _all_ids(animation)
        assert "bar_0" in ids and "bar_2" in ids
        merged_step = next(
            s for s in animation["steps"][1:] if "merged" in s["narration"]
        )
        assert any(op["op"] == "fill" for op in merged_step["motion"])


class TestBacktrackFamily:
    def test_choose_backtrack_trace_produces_valid_scene(self):
        trace = parse_trace(
            "\n".join(
                [
                    '{"event":"init","values":[1,2,3],"family":"backtrack"}',
                    '{"event":"choose","i":0}',
                    '{"event":"choose","i":1}',
                    '{"event":"backtrack","i":1}',
                    '{"event":"choose","i":2}',
                    '{"event":"return","result":[[1,2],[1,3]]}',
                ]
            )
        )
        animation = _validated(compile_family("backtrack", trace, title="Subsets"))
        ids = _all_ids(animation)
        assert "cell_0" in ids and "cell_2" in ids
        choose_step = next(
            s for s in animation["steps"][1:] if "Choose" in s["narration"]
        )
        assert any(op["op"] == "fill" for op in choose_step["motion"])

    def test_backtrack_resets_highlight(self):
        trace = parse_trace(
            "\n".join(
                [
                    '{"event":"init","values":[1,2],"family":"backtrack"}',
                    '{"event":"choose","i":0}',
                    '{"event":"backtrack","i":0}',
                    '{"event":"return","result":[]}',
                ]
            )
        )
        animation = _validated(compile_family("backtrack", trace))
        back_step = next(
            s for s in animation["steps"][1:] if "Backtrack" in s["narration"]
        )
        fills = {op["to"] for op in back_step["motion"] if op["op"] == "fill"}
        assert "#1e293b" in fills  # reset to idle


class TestDispatch:
    def test_unknown_family_returns_none(self):
        assert compile_family("nope", [], title="x") is None

    def test_missing_init_returns_none(self):
        trace = parse_trace('{"event":"visit","i":0}')
        assert compile_family("tree", trace, title="x") is None

    def test_array_family_roundtrips_through_compile_family(self):
        trace = parse_trace(
            json.dumps(
                [
                    {"event": "init", "values": [5, 1]},
                    {"event": "compare", "i": 0, "j": 1},
                    {"event": "return", "result": [1, 5]},
                ],
                separators=(",", ":"),
            )
        )
        animation = _validated(compile_family("array", trace, title="Bubble"))
        assert animation["title"] == "Bubble"
