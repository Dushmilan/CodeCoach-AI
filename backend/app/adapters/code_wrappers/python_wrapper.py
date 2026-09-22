"""Python student-code runner (wrap / wrap_with_tests).

INVARIANT — no ``typing.get_type_hints()`` on this path: string annotations
(quoted ``"List[int]"`` or PEP 563 ``from __future__ import annotations``)
are never evaluated at def-time, so student functions define and run without
their names being importable. That safety holds ONLY because nothing here —
runner templates, arity detection (``_function_arity`` is AST-based), or
output comparison — resolves annotations via ``typing.get_type_hints()``,
which would evaluate the strings and raise ``NameError``. Keep it that way:
introspection on this path stays syntactic (``ast``/``re``).
"""

import ast
import re
from typing import Any, Dict, List

from .base import CodeWrapper
from .output_comparator import PYTHON_OUTPUT_MATCH


def _function_arity(code: str, func_name: str) -> tuple[int, int]:
    """(total, required) positional params of the named function.

    Falls back to (1, 1) when the code does not parse — single-arg call
    behavior is then preserved exactly.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return (1, 1)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            total = len(node.args.posonlyargs) + len(node.args.args)
            required = total - len(node.args.defaults)
            return (total, required)
    return (1, 1)


# Typing names students commonly use bare in annotations (e.g. LeetCode
# signatures like ``def canJump(nums: List[int])``) without importing them.
# Lowercase builtins (``list[int]``) need nothing and are never injected.
_TYPING_NAMES = frozenset({"List", "Dict", "Set", "Tuple", "Optional", "Union", "Any"})


def _typing_import_block(code: str) -> str:
    """Import lines for typing names the code uses but never imports.

    Returns "" when nothing is missing, when the code already imports what
    it uses, or when the code does not parse (old behavior preserved).
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return ""
    imported: set[str] = set()
    imports_typing_module = False
    used: set[str] = set()
    uses_typing_attr = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in _TYPING_NAMES:
            used.add(node.id)
        elif (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "typing"
        ):
            uses_typing_attr = True
    # Only top-level imports bind names at module scope, where the runner
    # embeds student code. A typing import nested in a function body must
    # not suppress the injected header (worst case is a redundant import).
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "typing":
            if any(a.name == "*" for a in node.names):
                return ""
            imported.update(a.asname or a.name for a in node.names)
        elif isinstance(node, ast.Import):
            if any(
                a.name == "typing" or a.name.startswith("typing.") for a in node.names
            ):
                imports_typing_module = True
    lines: List[str] = []
    if uses_typing_attr and not imports_typing_module:
        lines.append("import typing")
    missing = sorted(used - imported)
    if missing:
        lines.append(f"from typing import {', '.join(missing)}")
    return "\n".join(lines)


def _split_future_imports(code: str) -> tuple[str, str]:
    """Split top-level ``from __future__`` imports out of student code.

    The runner prepends its own ``import sys/json`` header (plus injected
    typing imports), which would otherwise push a student's future import
    off the top of the module — a compile-time ``SyntaxError``, since
    future imports must lead the file. Returns ``(future_block, rest)``;
    ``future_block`` is "" when there is nothing to hoist or the code does
    not parse (old behavior preserved).
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return "", code
    future_nodes = [
        node
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "__future__"
    ]
    if not future_nodes:
        return "", code
    lines = code.splitlines(keepends=True)
    for node in future_nodes:
        # A future import sharing its line with another statement via
        # semicolon (``from __future__ import annotations; x = 1``) cannot
        # be hoisted by whole lines without silently dropping that code —
        # bail out and preserve old behavior instead.
        first = lines[node.lineno - 1]
        if first[: node.col_offset].strip():
            return "", code
        last = lines[(node.end_lineno or node.lineno) - 1]
        end_col = node.end_col_offset or len(last)
        trailing = last[end_col:].strip()
        if trailing and not trailing.startswith("#"):
            return "", code
    future_linenos: set[int] = set()
    for node in future_nodes:
        for lineno in range(node.lineno, (node.end_lineno or node.lineno) + 1):
            future_linenos.add(lineno)
    lines = code.splitlines(keepends=True)
    future_block = "".join(lines[i - 1] for i in sorted(future_linenos)).strip()
    rest = "".join(ln for i, ln in enumerate(lines, start=1) if i not in future_linenos)
    return future_block, rest


class PythonCodeWrapper(CodeWrapper):
    # Bracket/quote-aware splitter embedded in multi-arg single-run runners.
    # f-string literal: every brace below is doubled in the template itself.
    _SPLIT_HELPER = """
def __split_top_level(__text):
    __parts = []
    __current = []
    __depth = 0
    __quote = None
    __i = 0
    while __i < len(__text):
        __ch = __text[__i]
        if __quote is not None:
            __current.append(__ch)
            if __ch == "\\\\" and __i + 1 < len(__text):
                __current.append(__text[__i + 1])
                __i += 1
            elif __ch == __quote:
                __quote = None
        elif __ch in ("'", '"'):
            __quote = __ch
            __current.append(__ch)
        elif __ch in "[{(":
            __depth += 1
            __current.append(__ch)
        elif __ch in "]})":
            __depth = max(0, __depth - 1)
            __current.append(__ch)
        elif __ch == "," and __depth == 0:
            __parts.append("".join(__current))
            __current = []
        else:
            __current.append(__ch)
        __i += 1
    __parts.append("".join(__current))
    return __parts


def __to_arg(__s):
    try:
        return json.loads(__s)
    except Exception:
        return __s
"""

    # Shared argument-unpacking rule embedded in BOTH runners (Run via
    # ``wrap`` and Submit via ``wrap_with_tests``) so the two paths cannot
    # diverge on how one raw input maps to positional arguments: one arg per
    # line, or single-line top-level-comma separated, split only when the
    # part count matches the function's arity.
    _ARG_UNPACK_HELPER = """
def __unpack_args(__text, __required, __total):
    if not isinstance(__text, str):
        return [__text]
    if __total <= 1:
        return [__to_arg(__text)]
    if "\\n" in __text:
        __parts = __text.split("\\n")
    else:
        __parts = [__p.strip() for __p in __split_top_level(__text)]
    if len(__parts) > 1 and len(__parts) in (__required, __total):
        return [__to_arg(__p) for __p in __parts]
    return [__to_arg(__text)]
"""

    def wrap(self, code: str) -> str:
        if "input(" in code or "sys.stdin" in code or "print(" in code:
            return code
        code = re.sub(r"(\(\s*)self\s*,?\s*", r"\1", code)

        func_match = re.search(r"def\s+(\w+)\s*\(", code)
        if not func_match:
            return code
        func_name = func_match.group(1)
        total, required = _function_arity(code, func_name)
        if total <= 1:
            single_call = "result = {func_name}(parsed_line)"
        else:
            single_call = (
                "result = {func_name}(*__unpack_args(parsed_line, {required}, {total}))"
            )
        typing_imports = _typing_import_block(code)
        future_block, body = _split_future_imports(code)
        header = "import sys\nimport json"
        if typing_imports:
            header += f"\n{typing_imports}"
        if future_block:
            header = f"{future_block}\n{header}"
        runner = f"""
{header}

{body}
"""
        if total > 1:
            runner += self._SPLIT_HELPER
            runner += self._ARG_UNPACK_HELPER
        runner += f"""
try:
    line = sys.stdin.read().strip()
    if line:
        try:
            parsed_line = json.loads(line)
        except:
            parsed_line = line
        {single_call.format(func_name=func_name, required=required, total=total)}
    else:
        result = {func_name}("")
    if result is None and isinstance(parsed_line, (list, dict)):
        print(json.dumps(parsed_line, separators=(",", ":")))
    elif isinstance(result, list):
        print(json.dumps(result, separators=(",", ":")))
    elif isinstance(result, bool):
        print(str(result).lower())
    elif isinstance(result, str):
        print(result)
    else:
        print(result)
except Exception as e:
    print(str(e), file=sys.stderr)
    sys.exit(1)
"""
        return runner.strip()

    def wrap_with_tests(self, code: str, test_cases: List[Dict[str, Any]]) -> str:
        code = re.sub(r"(\(\s*)self\s*,?\s*", r"\1", code)
        func_match = re.search(r"def\s+(\w+)\s*\(", code)
        func_name = func_match.group(1) if func_match else "solve"
        total, required = _function_arity(code, func_name)
        tc_clean = [
            {
                "input": tc["input"],
                "expected": tc["expected_output"],
                "index": i + 1,
            }
            for i, tc in enumerate(test_cases)
        ]
        tc_repr = repr(tc_clean)

        typing_imports = _typing_import_block(code)
        future_block, body = _split_future_imports(code)
        header = "import sys, json"
        if typing_imports:
            header += f"\n{typing_imports}"
        if future_block:
            header = f"{future_block}\n{header}"
        return f"""{header}

{body}

{self._SPLIT_HELPER}
{self._ARG_UNPACK_HELPER}

{PYTHON_OUTPUT_MATCH}

def run_suite():
    __test_cases = {tc_repr}
    __results = []

    def __run_test(__tc):
        __inp = __tc["input"]
        __args = __unpack_args(__inp, {required}, {total})
        __result = {func_name}(*__args)
        return __result, __args[0]

    for __tc in __test_cases:
        __idx = __tc["index"]
        __exp = __tc["expected"]
        try:
            __out, __in_val = __run_test(__tc)
            if __out is None:
                __actual = json.dumps(__in_val, separators=(",", ":")) if isinstance(__in_val, (list, dict)) else str(__in_val)
            elif isinstance(__out, list):
                __actual = json.dumps(__out, separators=(",", ":"))
            elif isinstance(__out, bool):
                __actual = str(__out).lower()
            else:
                __actual = str(__out)
            __passed = __outputs_match(__actual, __exp)
        except Exception as __e:
            __actual = str(__e)
            __passed = False
        __results.append({{"index": __idx, "passed": __passed, "actual": __actual}})

    print("@@SUITE_RESULT@@" + json.dumps(__results, separators=(",", ":")) + "@@SUITE_RESULT@@")
    sys.stdout.flush()

if __name__ == "__main__":
    run_suite()
"""
