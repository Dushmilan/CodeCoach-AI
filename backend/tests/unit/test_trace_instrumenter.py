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

from app.services.trace_instrumenter import (
    display_code_and_map,
    wrap_traced_solution,
)
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


class TestLineCapture:
    def test_events_carry_solution_relative_line(self):
        code = wrap_traced_solution(BUBBLE_SORT, "bubble_sort")
        events = parse_trace(_run(code, json.dumps({"values": [5, 1, 4, 2, 8]})))
        # BUBBLE_SORT's `__trace("pointer", ...)` is on line 6 of the solution.
        pointer = next(e for e in events if e.kind == "pointer")
        assert pointer.line == 6
        # `__trace("init", ...)` is on line 2.
        assert events[0].line == 2

    def test_offset_is_stable_across_functions(self):
        code = wrap_traced_solution(LINEAR_SEARCH, "linear_search")
        events = parse_trace(
            _run(code, json.dumps({"values": [4, 2, 7, 1], "target": 7}))
        )
        compare = next(e for e in events if e.kind == "compare")
        assert compare.line == 5


INTENT_SOLUTION = """\
def pick(values, target):
    __trace("init", values=list(values), family="array")
    for i, v in enumerate(values):
        __trace("pointer", name="i", index=i)
        __trace("compare", i=i, intent=f"{v} = {target} -> found" if v == target else f"{v} != {target} -> keep scanning")
        if v == target:
            return i
    return -1
"""


class TestIntentAndLineCapture:
    """#287: string intent fields ride the event without disturbing the
    __CODE_OFFSET line math — only ``line`` enters the offset path."""

    def test_intent_rides_events_and_lines_stay_solution_relative(self):
        code = wrap_traced_solution(INTENT_SOLUTION, "pick")
        events = parse_trace(_run(code, json.dumps({"values": [4, 2], "target": 2})))
        intents = [e.intent for e in events if e.kind == "compare"]
        assert intents == ["4 != 2 -> keep scanning", "2 = 2 -> found"]
        # The pointer __trace sits on line 4 of the solution — identical to
        # a run where the intent kwarg never existed.
        pointer = next(e for e in events if e.kind == "pointer")
        assert pointer.line == 4


TRACE_DISPLAY_SAMPLE = """\
def total(values):
    __trace("init", values=values, family="array")
    acc = 0
    for i, v in enumerate(values):
        __trace("pointer", name="i", index=i)
        acc += v
        __trace("mark", i=i, state="seen")
    return acc
"""


class TestDisplayCodeAndMap:
    def test_strips_standalone_trace_calls(self):
        display, _ = display_code_and_map(TRACE_DISPLAY_SAMPLE)
        assert "__trace" not in display
        assert "acc += v" in display
        assert "return acc" in display

    def test_maps_trace_lines_to_preceding_statement(self):
        _, mapping = display_code_and_map(TRACE_DISPLAY_SAMPLE)
        # pointer's __trace is line 5 -> the `for` header (display line 3)
        assert mapping[5] == 3
        # mark's __trace is line 7 -> `acc += v` (display line 4)
        assert mapping[7] == 4

    def test_init_with_no_preceding_statement_maps_forward(self):
        display, mapping = display_code_and_map(
            'def f(x):\n    __trace("init", x=x)\n    return x\n'
        )
        assert mapping[2] == 1  # def f(x):
        assert "return x" in display

    def test_non_statement_trace_call_is_kept(self):
        code = 'def f(x):\n    y = __trace("init", x=x)\n    return y\n'
        display, mapping = display_code_and_map(code)
        assert "__trace" in display
        assert mapping[2] == 2

    def test_syntax_error_returns_identity_map(self):
        bad = "def f(:\n    pass\n"
        display, mapping = display_code_and_map(bad)
        assert display == bad
        assert mapping == {1: 1, 2: 2}

    def test_multiline_trace_call_is_fully_stripped(self):
        code = (
            "def f(x):\n"
            "    __trace(\n"
            '        "init",\n'
            "        x=x,\n"
            "    )\n"
            "    return x\n"
        )
        display, mapping = display_code_and_map(code)
        assert "__trace" not in display
        assert display == "def f(x):\n    return x"
        # Every original line of the call maps to the def line (display 1).
        assert mapping[2] == mapping[3] == mapping[4] == mapping[5] == 1

    def test_code_with_only_trace_calls_returns_identity_map(self):
        code = '__trace("init")\n__trace("mark")\n'
        display, mapping = display_code_and_map(code)
        assert display == code
        assert mapping == {1: 1, 2: 2}
