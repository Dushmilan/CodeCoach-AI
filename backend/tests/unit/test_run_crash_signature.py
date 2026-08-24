"""Unit tests for the crash-signature derivation used by the run endpoint.

A crashed free-run inside a question workspace feeds mistake-memory with a
stable-ish signature: the first non-empty stderr line, capped at 255 chars.
"""

from app.api.run import _crash_signature


class TestCrashSignature:
    def test_first_non_empty_line_wins(self):
        stderr = "\n  Traceback (most recent call last):\n  ZeroDivisionError\n"
        assert _crash_signature(stderr) == "Traceback (most recent call last):"

    def test_truncated_to_255_chars(self):
        assert len(_crash_signature("x" * 500)) == 255

    def test_whitespace_only_stderr_is_none(self):
        assert _crash_signature(" \n\t\n") is None

    def test_empty_stderr_is_none(self):
        assert _crash_signature("") is None
