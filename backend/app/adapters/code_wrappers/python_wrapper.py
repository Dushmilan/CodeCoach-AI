import ast
import re
from typing import Any, Dict, List

from .base import CodeWrapper
from .output_comparator import PYTHON_OUTPUT_MATCH


def _split_top_level(text: str) -> List[str]:
    """Split on commas that sit outside brackets and string literals."""
    parts: List[str] = []
    current: List[str] = []
    depth = 0
    quote: str | None = None
    i = 0
    while i < len(text):
        ch = text[i]
        if quote is not None:
            current.append(ch)
            if ch == "\\" and i + 1 < len(text):
                current.append(text[i + 1])
                i += 1
            elif ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            current.append(ch)
        elif ch in "[{(":
            depth += 1
            current.append(ch)
        elif ch in "]})":
            depth = max(0, depth - 1)
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
        i += 1
    parts.append("".join(current))
    return parts


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


def _maybe_split_input(text: str, total: int, required: int) -> str:
    """Unpack a single-line multi-arg input into newline-separated args.

    The suite runner already unpacks multi-line inputs positionally; a
    one-line ``"[2,7,11,15], 9"`` for ``def two_sum(nums, target)`` would
    otherwise arrive as a single string and fail with a missing-argument
    error even for correct solutions. Only rewrites when the part count
    matches the function's arity, so ambiguous inputs keep old behavior.
    """
    if total <= 1 or "\n" in text:
        return text
    parts = [p.strip() for p in _split_top_level(text)]
    if len(parts) > 1 and len(parts) in (required, total):
        return "\n".join(parts)
    return text


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
            single_call = """if __raw and isinstance(parsed_line, str):
            __split = [__p.strip() for __p in __split_top_level(parsed_line)]
            if len(__split) > 1 and len(__split) in ({required}, {total}):
                result = {func_name}(*[__to_arg(__p) for __p in __split])
            else:
                result = {func_name}(parsed_line)
        else:
            result = {func_name}(parsed_line)"""
        typing_imports = _typing_import_block(code)
        header = "import sys\nimport json"
        if typing_imports:
            header += f"\n{typing_imports}"
        runner = f"""
{header}

{code}
"""
        if total > 1:
            runner += self._SPLIT_HELPER
        runner += f"""
try:
    line = sys.stdin.read().strip()
    if line:
        try:
            parsed_line = json.loads(line)
            __raw = False
        except:
            parsed_line = line
            __raw = True
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
                "input": _maybe_split_input(tc["input"], total, required),
                "expected": tc["expected_output"],
                "index": i + 1,
            }
            for i, tc in enumerate(test_cases)
        ]
        tc_repr = repr(tc_clean)

        typing_imports = _typing_import_block(code)
        header = "import sys, json"
        if typing_imports:
            header += f"\n{typing_imports}"
        return f"""{header}

{code}

{PYTHON_OUTPUT_MATCH}

def run_suite():
    __test_cases = {tc_repr}
    __results = []

    def __run_test(__tc):
        __inp = __tc["input"]
        try:
            __lines = __inp.split("\\n") if __inp else [""]
            if len(__lines) == 1:
                try:
                    __parsed = json.loads(__lines[0])
                except Exception:
                    __parsed = __lines[0]
                __result = {func_name}(__parsed)
                return __result, __parsed
            elif len(__lines) == 2:
                try:
                    __a = json.loads(__lines[0])
                    __b = json.loads(__lines[1]) if (__lines[1].strip().lstrip("-").isdigit() or __lines[1].strip().startswith("[")) else __lines[1]
                except Exception:
                    __a, __b = __lines[0], __lines[1]
                __result = {func_name}(__a, __b)
                return __result, __a
            else:
                __parsed_args = [json.loads(ln) if ln.strip() else ln for ln in __lines]
                __result = {func_name}(*__parsed_args)
                return __result, __parsed_args[0]
        except Exception as e:
            raise e

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
