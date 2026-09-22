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
