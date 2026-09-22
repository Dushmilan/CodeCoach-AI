"""Wrapping of a traced canonical solution for sandbox execution.

A curated reference solution is written against a tiny __trace API — each
semantic step (compare/swap/pointer/mark/write/visit/push/pop/dp_update/...)
appends one event object to an in-memory list. The canonical solution emits
its own ``init`` event (it knows its real structure — a DP array, a character
list, a tree, ...), and this module injects the __trace helper plus a
stdin-driven main that parses the example input (a JSON kwargs dict produced
by the input normalizer) and invokes the canonical solution, then prints the
whole trace as a single compact JSON array.

Buffering (instead of one line per event) keeps stdout far under the sandbox
output cap — Piston SIGKILLs runners whose stdout exceeds the limit.
"""

import ast

_TRACE_HELPER_TEMPLATE = """\
import json as __json
import sys as __sys

__TRACE = []
__CODE_OFFSET = 0


def __trace(event, **fields):
    __frame = __sys._getframe(1) if hasattr(__sys, "_getframe") else None
    if __frame is not None and "line" not in fields:
        fields["line"] = __frame.f_lineno - __CODE_OFFSET
    __TRACE.append({"event": event, **fields})
"""


def _build_helper() -> str:
    """Finalize the helper, injecting the wrapped-file line offset.

    The placeholder line keeps the template's line count stable, so the offset
    computed here stays correct after substitution.
    """
    offset = _TRACE_HELPER_TEMPLATE.count("\n") + 1
    return _TRACE_HELPER_TEMPLATE.replace(
        "__CODE_OFFSET = 0", f"__CODE_OFFSET = {offset}"
    )


def _dump_trace() -> str:
    return (
        '__TRACE.append({"event": "return", "result": __result})\n'
        'print(__json.dumps(__TRACE, separators=(",", ":")))'
    )


def wrap_traced_solution(code: str, function: str) -> str:
    """Wrap canonical solution code so it emits the JSON-array execution trace."""
    helper = _build_helper()
    wrapper = f"""\
__inp = __sys.stdin.read().strip()
if not __inp:
    __inp = "{{}}"
__arg = __json.loads(__inp)
if not isinstance(__arg, dict):
    __arg = {{"value": __arg}}
__result = {function}(**__arg)
{_dump_trace()}
"""
    return f"{helper}\n{code}\n\n{wrapper}".strip()


def _is_trace_statement(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "__trace"
    )


def display_code_and_map(code: str) -> tuple[str, dict[int, int]]:
    """Strip standalone ``__trace(...)`` statements; map original→display line.

    Each stripped line maps to the nearest preceding kept line, falling back to
    the nearest following kept line when there is none. Syntactically invalid
    code, and code with nothing left to display, is returned unchanged with an
    identity map.
    """
    lines = code.splitlines()
    identity = {i: i for i in range(1, len(lines) + 1)}
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code, identity

    removed: set[int] = set()
    for node in ast.walk(tree):
        if _is_trace_statement(node):
            end = getattr(node, "end_lineno", None) or node.lineno
            removed.update(range(node.lineno, end + 1))

    kept = [i for i in range(1, len(lines) + 1) if i not in removed]
    if not kept:
        # Nothing survives (e.g. a trace-only snippet): keep the code intact so
        # the map stays total and callers never hit a KeyError.
        return code, identity
    display_pos = {orig: idx + 1 for idx, orig in enumerate(kept)}
    mapping: dict[int, int] = {}
    for orig in range(1, len(lines) + 1):
        if orig in display_pos:
            mapping[orig] = display_pos[orig]
            continue
        prev = max((k for k in kept if k < orig), default=None)
        if prev is not None:
            mapping[orig] = display_pos[prev]
        else:
            nxt = min((k for k in kept if k > orig), default=None)
            if nxt is not None:
                mapping[orig] = display_pos[nxt]

    display_code = "\n".join(lines[i - 1] for i in kept)
    return display_code, mapping
