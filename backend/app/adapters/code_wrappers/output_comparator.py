"""Shared test-output comparison for suite runners.

String-returning questions store expected answers as JSON string literals
(e.g. ``"world"`` with quotes), while runners print returned values via
``str()``/``String()`` without the surrounding quotes. A raw ``.strip()``
comparison therefore fails (``world`` != ``"world"``), and stripping
whitespace also breaks answers where spaces are meaningful
(``"  321"`` -> ``"123  "``).

This module provides one Python implementation (``outputs_match``) used by
the Piston re-verification path plus per-language code snippets embedded into
the generated Python / JavaScript / Java suite runners, so every language
compares the same way:

- JSON-encoded strings are decoded before comparing (so ``"world"`` matches ``world``).
- Internal/leading/trailing whitespace is preserved; only a single trailing
  process newline is trimmed.
- Arrays/objects/booleans/numbers keep working (compared as parsed values).
"""

import json
from typing import Any, Optional


def outputs_match(actual: Optional[str], expected: Optional[str]) -> bool:
    """Return True when the runner ``actual`` output matches ``expected``."""
    actual = "" if actual is None else actual
    expected = "" if expected is None else expected
    if actual.endswith("\n"):
        actual = actual[:-1]

    try:
        decoded_expected: Any = json.loads(expected)
    except (ValueError, TypeError):
        decoded_expected = None
    try:
        decoded_actual: Any = json.loads(actual)
    except (ValueError, TypeError):
        decoded_actual = None

    if isinstance(decoded_expected, str):
        return actual == decoded_expected or decoded_actual == decoded_expected
    if decoded_expected is not None:
        return decoded_actual == decoded_expected
    if isinstance(decoded_actual, str):
        return actual == expected or decoded_actual == expected
    return actual == expected


PYTHON_OUTPUT_MATCH = r'''
def __outputs_match(__actual, __expected):
    if __actual.endswith("\n"):
        __actual = __actual[:-1]
    try:
        __decoded_expected = json.loads(__expected)
    except Exception:
        __decoded_expected = None
    try:
        __decoded_actual = json.loads(__actual)
    except Exception:
        __decoded_actual = None
    if isinstance(__decoded_expected, str):
        return __actual == __decoded_expected or __decoded_actual == __decoded_expected
    if __decoded_expected is not None:
        return __decoded_actual == __decoded_expected
    if isinstance(__decoded_actual, str):
        return __actual == __expected or __decoded_actual == __expected
    return __actual == __expected
'''


JS_OUTPUT_MATCH = r'''
function outputsMatch(actual, expected) {
  if (actual.endsWith('\n')) { actual = actual.slice(0, -1); }
  let decodedExpected = null;
  let decodedActual = null;
  try { decodedExpected = JSON.parse(expected); } catch (e) { decodedExpected = null; }
  try { decodedActual = JSON.parse(actual); } catch (e) { decodedActual = null; }
  if (typeof decodedExpected === 'string') { return actual === decodedExpected || decodedActual === decodedExpected; }
  if (decodedExpected !== null && decodedExpected !== undefined) {
    try { return JSON.stringify(decodedActual) === JSON.stringify(decodedExpected); }
    catch (e) { return false; }
  }
  if (typeof decodedActual === 'string') { return actual === expected || decodedActual === expected; }
  return actual === expected;
}
'''


JAVA_OUTPUT_MATCH = r'''
    static boolean outputsMatch(String actual, String expected) {
        if (actual.endsWith("\n")) { actual = actual.substring(0, actual.length() - 1); }
        return decode(actual).equals(decode(expected));
    }

    static String decode(String s) {
        if (s.length() >= 2 && s.charAt(0) == '"' && s.charAt(s.length() - 1) == '"') {
            return s.substring(1, s.length() - 1);
        }
        if (s.length() >= 4 && s.charAt(0) == '\\' && s.charAt(1) == '"'
                && s.charAt(s.length() - 2) == '"' && s.charAt(s.length() - 1) == '\\') {
            return s.substring(2, s.length() - 2);
        }
        return s;
    }
'''
