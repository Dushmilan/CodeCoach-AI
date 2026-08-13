"""Unit tests for the traced-solution wrapper (trace_instrumenter).

The wrapper injects the __trace emitter and a stdin-driven main that parses
the example input (a JSON kwargs dict) and invokes the canonical solution,
producing the JSON-array trace the parser + compiler consume. The canonical
solution emits its own ``init`` event.

These tests exec the wrapped code for real so the full
solution→trace→parse chain is validated without Piston.
"""

import io
import sys
import json

from app.services.trace_instrumenter import wrap_traced_solution
from app.services.trace_parser import parse_trace

BUBBLE_SORT = """\
def bubble_sort(values):
    __trace("init", values=list(values), family="array")
    n = len(values)
    for i in range(n - 1):
        for j in range(n - i - 1):
            __trace("pointer", name="j", index=j)
            __trace("compare", i=j, j=j + 1)
            if values[j] > values[j + 1]:
                values[j], values[j + 1] = values[j + 1], values[j]
                __trace("swap", i=j, j=j + 1)
        __trace("mark", i=n - i - 1, state="sorted")
    return values
"""

LINEAR_SEARCH = """\
def linear_search(values, target):
    __trace("init", values=list(values), family="array")
    for i, v in enumerate(values):
        __trace("pointer", name="i", index=i)
        __trace("compare", i=i)
        if v == target:
            __trace("mark", i=i, state="match")
            return i
    return -1
"""

TREE_DEPTH = """\
def max_depth(root):
    __trace("init", data=list(root), family="tree")
    best = 0
    for i, v in enumerate(root):
        if v is not None:
            __trace("visit", i=i)
            best = max(best, i.bit_length())
    return best
"""

GRAPH_TRAVERSAL = """\
def count_nodes(adj, n):
    __trace("init", data=adj, family="graph", n=n)
    total = 0
    for i in range(n):
        __trace("visit", i=i)
        for b in adj[i]:
            __trace("edge", a=i, b=b)
        total += 1
    return total
"""


def _run(code: str, stdin: str) -> str:
    old_stdin, old_stdout = sys.stdin, sys.stdout
    buf = io.StringIO()
    try:
        sys.stdin = io.StringIO(stdin)
        sys.stdout = buf
        exec(compile(code, "<wrapped>", "exec"), {})
    finally:
        sys.stdin, sys.stdout = old_stdin, old_stdout
    return buf.getvalue()


class TestWrapTracedSolution:
    def test_array_style_bubble_sort_trace(self):
        code = wrap_traced_solution(BUBBLE_SORT, "bubble_sort")
        events = parse_trace(_run(code, json.dumps({"values": [5, 1, 4, 2, 8]})))
        kinds = [e.kind for e in events]
        assert kinds[0] == "init"
        assert kinds[-1] == "return"
        assert "compare" in kinds
        assert "swap" in kinds
        assert "mark" in kinds
        init = events[0]
        assert init.fields["values"] == [5, 1, 4, 2, 8]
        assert init.fields["family"] == "array"
        result = events[-1].fields["result"]
        assert result == [1, 2, 4, 5, 8]

    def test_kwargs_style_linear_search_trace(self):
        code = wrap_traced_solution(LINEAR_SEARCH, "linear_search")
        stdin = json.dumps({"values": [4, 2, 7, 1], "target": 7})
        events = parse_trace(_run(code, stdin))
        kinds = [e.kind for e in events]
        assert kinds[0] == "init"
        assert events[0].fields["values"] == [4, 2, 7, 1]
        assert "compare" in kinds
        match = next(e for e in events if e.kind == "mark")
        assert match.state == "match"
        assert events[-1].kind == "return"

    def test_non_dict_stdin_is_wrapped_as_value(self):
        echo = 'def echo(value):\n    __trace("init", values=list(value), family="array")\n    return value\n'
        code = wrap_traced_solution(echo, "echo")
        events = parse_trace(_run(code, "[5,1,4,2,8]"))
        assert events[0].kind == "init"
        assert events[0].fields["values"] == [5, 1, 4, 2, 8]
        assert events[-1].fields["result"] == [5, 1, 4, 2, 8]

    def test_tree_family_init_carries_data(self):
        code = wrap_traced_solution(TREE_DEPTH, "max_depth")
        events = parse_trace(
            _run(
                code,
                json.dumps({"root": [3, 9, 20, None, None, 15, 7]}),
            )
        )
        assert events[0].fields["family"] == "tree"
        assert events[0].fields["data"] == [3, 9, 20, None, None, 15, 7]

    def test_graph_family_init_carries_vertex_count(self):
        code = wrap_traced_solution(GRAPH_TRAVERSAL, "count_nodes")
        events = parse_trace(
            _run(
                code,
                json.dumps({"adj": [[1], [0], [1]], "n": 3}),
            )
        )
        assert events[0].fields["family"] == "graph"
        assert events[0].fields["n"] == 3

    def test_wrapper_contains_helper_and_function(self):
        code = wrap_traced_solution(BUBBLE_SORT, "bubble_sort")
        assert "def __trace" in code
        assert "def bubble_sort" in code
        assert "__TRACE" in code
