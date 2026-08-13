"""Normalization of question example inputs into canonical solution kwargs.

DB questions store example inputs in many shapes: `nums = [2,7,11,15], target =
9`, bare arrays, bare strings, matrices, level-order tree arrays, and multiline
test inputs. The animation pipeline feeds the canonical traced solution the same
real example the user sees, so this module turns any of those shapes into the
kwargs dict the canonical function expects.

Parsing is safe (JSON/literal evaluation only — never exec) and graded:

1. Already-structured values (dicts) pass through.
2. Whole-string JSON/literal parse (arrays, objects, strings, numbers).
3. `key = value, key = value` assignment form, split at top-level commas.
4. Multiline inputs map each line to the signature in order.
5. A raw-string fallback for values that are not evaluable (e.g. bit strings
   like `00000000000000000000000000001011` for a binary-number argument).
"""

import ast
import json
from typing import Any, Dict, List, Optional


def _eval_value(raw: str) -> Any:
    """Parse a single value with JSON first (null/true) then literal eval."""
    stripped = raw.strip()
    try:
        return json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        pass
    try:
        return ast.literal_eval(stripped)
    except (ValueError, SyntaxError):
        return stripped


def _split_top_level(raw: str) -> List[str]:
    """Split on commas at bracket/brace/quote depth 0."""
    parts: List[str] = []
    depth = 0
    quote: Optional[str] = None
    current = ""
    i = 0
    while i < len(raw):
        ch = raw[i]
        if quote is not None:
            current += ch
            if ch == quote and raw[i - 1] != "\\":
                quote = None
        elif ch in "\"'":
            quote = ch
            current += ch
        elif ch in "[{(":
            depth += 1
            current += ch
        elif ch in "]})":
            depth -= 1
            current += ch
        elif ch == "," and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += ch
        i += 1
    parts.append(current)
    return parts


def _parse_assignment_form(raw: str, signature: List[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    # Each line may hold one or more `key = value` assignments (the min-stack
    # example puts `operations = [...]` and `values = [...]` on separate lines).
    for line in raw.splitlines():
        for part in _split_top_level(line):
            if not part.strip():
                continue
            if "=" not in part:
                continue
            key, _, value = part.partition("=")
            key = key.strip()
            if not key:
                continue
            out[key] = _eval_value(value)
    # Bare assignment-less values should not happen here, but if nothing was
    # extracted, fall through to the whole-string parse.
    if not out:
        raise ValueError("no assignments found")
    return out


def parse_input_kwargs(
    raw_input: Any, signature: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Return the kwargs dict for a canonical solution call.

    ``signature`` lists the canonical function's parameter names in order; a
    positional input (bare array/string/number) maps onto the first parameter.
    """
    signature = signature or []
    if raw_input is None:
        return {}
    if isinstance(raw_input, dict):
        return dict(raw_input)
    if not isinstance(raw_input, str):
        return {signature[0]: raw_input} if signature else {}

    stripped = raw_input.strip()
    if not stripped:
        return {}

    # Whole-value parse first (bare array / object / quoted string / number).
    try:
        parsed = _eval_value(stripped)
        if isinstance(parsed, dict):
            return parsed
        if signature and not isinstance(parsed, str):
            return {signature[0]: parsed}
        if signature and isinstance(parsed, str) and stripped.startswith(('"', "'")):
            # A genuinely quoted string value, e.g. '"()"' → {"s": "()"}.
            return {signature[0]: parsed}
    except Exception:  # noqa: BLE001 - fall through to assignment form
        pass

    # `key = value, key = value` form.
    try:
        return _parse_assignment_form(stripped, signature)
    except (ValueError, TypeError):
        pass

    # Multiline positional input: each line is one positional argument.
    lines = [line.strip() for line in stripped.splitlines() if line.strip()]
    if len(lines) > 1 and signature:
        values = []
        for line in lines:
            try:
                values.append(_eval_value(line))
            except Exception:  # noqa: BLE001
                values.append(line)
        return dict(zip(signature, values))

    # Raw-string fallback (e.g. a bit-string argument like `n = 000...11` has
    # already been handled by the assignment form; bare words land here).
    if signature:
        return {signature[0]: _eval_value(stripped)}
    return {}
