"""Issue #231: /run + /submit fail correct Python using typing names.

Student code like ``def canJump(nums: List[int])`` with no explicit
``typing`` import raises ``NameError: List is not defined`` at def-time
on Piston, because the built runner only injects ``sys``/``json``.
"""

import io
from unittest import mock

from app.adapters.code_wrappers.python_wrapper import PythonCodeWrapper

TYPED_CODE = """def canJump(nums: List[int]) -> bool:
    return True
"""

CASES = [{"input": "[2,3,1,1,4]", "expected_output": "true"}]


def _exec_suite(runner: str) -> dict:
    """Exec a wrap_with_tests runner without running its suite."""
    namespace: dict = {"__name__": "wrap_test"}
    exec(compile(runner, "<runner>", "exec"), namespace)
    return namespace


def _exec_single(runner: str, stdin_data: str = "1") -> dict:
    """Exec a wrap runner with mocked stdin (it reads stdin at top level)."""
    namespace: dict = {"__name__": "wrap_test"}
    with mock.patch("sys.stdin", io.StringIO(stdin_data)):
        exec(compile(runner, "<runner>", "exec"), namespace)
    return namespace


class TestTypingAutoImport:
    def test_wrap_injects_list_import(self):
        runner = PythonCodeWrapper().wrap(TYPED_CODE)
        assert "from typing import List" in runner
        namespace = _exec_single(runner, "[2,3,1,1,4]")
        assert callable(namespace["canJump"])

    def test_wrap_with_tests_injects_list_import(self):
        runner = PythonCodeWrapper().wrap_with_tests(TYPED_CODE, CASES)
        assert "from typing import List" in runner

    def test_runner_exec_defines_function(self):
        runner = PythonCodeWrapper().wrap_with_tests(TYPED_CODE, CASES)
        assert callable(_exec_suite(runner)["canJump"])

    def test_each_typing_name_injected(self):
        for name in ["List", "Dict", "Optional", "Set", "Tuple"]:
            code = f"def f(x: {name}) -> int:\n    return 1"
            single = PythonCodeWrapper().wrap(code)
            assert f"from typing import {name}" in single
            _exec_single(single)
            suite = PythonCodeWrapper().wrap_with_tests(code, CASES)
            assert f"from typing import {name}" in suite
            _exec_suite(suite)

    def test_lowercase_builtin_needs_no_typing(self):
        code = "def f(nums: list[int]) -> bool:\n    return True"
        assert "from typing import" not in PythonCodeWrapper().wrap(code)
        _exec_single(PythonCodeWrapper().wrap(code), "[1,2]")
        suite = PythonCodeWrapper().wrap_with_tests(code, CASES)
        assert "from typing import" not in suite
        _exec_suite(suite)

    def test_explicit_user_import_not_duplicated(self):
        code = (
            "from typing import List\n\n"
            "def f(nums: List[int]) -> bool:\n    return True"
        )
        for runner in (
            PythonCodeWrapper().wrap(code),
            PythonCodeWrapper().wrap_with_tests(code, CASES),
        ):
            assert runner.count("from typing import") == 1
        _exec_single(PythonCodeWrapper().wrap(code), "[1,2]")
        _exec_suite(PythonCodeWrapper().wrap_with_tests(code, CASES))

    def test_plain_code_gets_no_typing_import(self):
        code = "def add(a, b):\n    return a + b"
        assert "from typing import" not in PythonCodeWrapper().wrap(code)
        runner = PythonCodeWrapper().wrap_with_tests(
            code, [{"input": "1\\n2", "expected_output": "3"}]
        )
        assert "from typing import" not in runner

    def test_function_local_import_does_not_suppress_injection(self):
        code = (
            "def f(nums: List[int]) -> bool:\n"
            "    from typing import List\n"
            "    return True"
        )
        runner = PythonCodeWrapper().wrap_with_tests(code, CASES)
        assert "from typing import List" in runner
        _exec_suite(runner)
