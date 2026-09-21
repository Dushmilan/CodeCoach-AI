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


class TestTypingEdgeCases:
    """Senior edge coverage for the #231 typing auto-import.

    Every case pins BOTH runner paths (wrap AND wrap_with_tests) and
    execs the runner so a bad import line fails loudly, not silently.
    """

    def test_nested_generics_inject_all_names_once(self):
        code = "def f(m: Dict[str, List[int]]) -> Optional[List[int]]:\n    return None"
        for runner in (
            PythonCodeWrapper().wrap(code),
            PythonCodeWrapper().wrap_with_tests(code, CASES),
        ):
            assert runner.count("from typing import") == 1
            line = next(ln for ln in runner.splitlines() if "from typing import" in ln)
            for name in ("Dict", "List", "Optional"):
                assert name in line
        _exec_single(PythonCodeWrapper().wrap(code), '{"a": [1]}')
        _exec_suite(PythonCodeWrapper().wrap_with_tests(code, CASES))

    def test_typing_attribute_style_injects_typing_module(self):
        code = "def f(nums: typing.List[int]) -> int:\n    return 1"
        for runner in (
            PythonCodeWrapper().wrap(code),
            PythonCodeWrapper().wrap_with_tests(code, CASES),
        ):
            assert "import typing" in runner
        _exec_single(PythonCodeWrapper().wrap(code), "[1,2]")
        _exec_suite(PythonCodeWrapper().wrap_with_tests(code, CASES))

    def test_typing_attribute_with_existing_import_gets_no_injection(self):
        code = "import typing\ndef f(nums: typing.List[int]) -> int:\n    return 1"
        for runner in (
            PythonCodeWrapper().wrap(code),
            PythonCodeWrapper().wrap_with_tests(code, CASES),
        ):
            assert "import typing" in runner  # the user's own line
            assert runner.count("import typing") == 1
        _exec_single(PythonCodeWrapper().wrap(code), "[1,2]")
        _exec_suite(PythonCodeWrapper().wrap_with_tests(code, CASES))

    def test_typing_module_alias_gets_no_injection(self):
        code = "import typing as t\ndef f(nums: t.List[int]) -> int:\n    return 1"
        for runner in (
            PythonCodeWrapper().wrap(code),
            PythonCodeWrapper().wrap_with_tests(code, CASES),
        ):
            assert "from typing import" not in runner
        _exec_single(PythonCodeWrapper().wrap(code), "[1,2]")
        _exec_suite(PythonCodeWrapper().wrap_with_tests(code, CASES))

    def test_from_import_alias_gets_no_injection(self):
        code = "from typing import List as L\ndef f(nums: L[int]) -> int:\n    return 1"
        for runner in (
            PythonCodeWrapper().wrap(code),
            PythonCodeWrapper().wrap_with_tests(code, CASES),
        ):
            assert runner.count("from typing import") == 1
        _exec_single(PythonCodeWrapper().wrap(code), "[1,2]")
        _exec_suite(PythonCodeWrapper().wrap_with_tests(code, CASES))

    def test_partial_import_injects_only_missing_names(self):
        code = (
            "from typing import List\n"
            "def f(nums: List[int]) -> int:\n"
            "    m: Dict[str, int] = {}\n"
            "    return 1"
        )
        for runner in (
            PythonCodeWrapper().wrap(code),
            PythonCodeWrapper().wrap_with_tests(code, CASES),
        ):
            assert runner.count("from typing import") == 2
            assert "from typing import Dict" in runner
        _exec_single(PythonCodeWrapper().wrap(code), "[1,2]")
        _exec_suite(PythonCodeWrapper().wrap_with_tests(code, CASES))

    def test_mixed_attribute_and_bare_names_inject_both_lines(self):
        code = "def f(nums: typing.Optional[List[int]]) -> int:\n    return 1"
        for runner in (
            PythonCodeWrapper().wrap(code),
            PythonCodeWrapper().wrap_with_tests(code, CASES),
        ):
            assert "import typing" in runner
            assert "from typing import List" in runner
        _exec_single(PythonCodeWrapper().wrap(code), "[1,2]")
        _exec_suite(PythonCodeWrapper().wrap_with_tests(code, CASES))

    def test_syntax_error_code_passes_through_without_typing(self):
        code = "def broken(:\n    pass"
        for runner in (
            PythonCodeWrapper().wrap(code),
            PythonCodeWrapper().wrap_with_tests(code, CASES),
        ):
            assert "from typing import" not in runner
            assert "import typing" not in runner


class TestFutureImportAndStringAnnotations:
    """String annotations + ``from __future__ import annotations`` (Round 2).

    Probe results (pinned here):
    - ``from __future__ import annotations`` does NOT change the AST —
      annotations still parse as real expressions, so ``_typing_import_block``
      still sees the bare names and must inject. The injected header must go
      AFTER the student's future imports (they must lead the module), or the
      runner is a compile-time SyntaxError.
    - Quoted annotations (``"List[int]"``) parse as string Constants: no
      Name node exists, so nothing is injected. Safe-wont-fix: annotations
      are never evaluated at def-time, so the function defines and runs
      without the import (the runner never calls ``get_type_hints``).
    """

    FUTURE_CODE = (
        "from __future__ import annotations\n"
        "def two_sum(nums: List[int], target: int) -> List[int]:\n"
        "    return list(nums)"
    )

    def test_future_annotations_still_inject_typing(self):
        for runner in (
            PythonCodeWrapper().wrap(self.FUTURE_CODE),
            PythonCodeWrapper().wrap_with_tests(self.FUTURE_CODE, CASES),
        ):
            assert "from typing import List" in runner

    def test_future_import_leads_runner_module(self):
        for runner in (
            PythonCodeWrapper().wrap(self.FUTURE_CODE),
            PythonCodeWrapper().wrap_with_tests(self.FUTURE_CODE, CASES),
        ):
            compile(runner, "<runner>", "exec")
            future_at = runner.index("from __future__ import annotations")
            assert runner.index("import sys") > future_at
            assert runner.index("from typing import List") > future_at

    def test_future_annotated_runner_exec_defines_function(self):
        _exec_suite(PythonCodeWrapper().wrap_with_tests(self.FUTURE_CODE, CASES))
        namespace = _exec_single(
            PythonCodeWrapper().wrap(self.FUTURE_CODE), "[2,7,11,15], 9"
        )
        assert callable(namespace["two_sum"])

    def test_future_import_without_typing_still_compiles(self):
        code = (
            "from __future__ import annotations\n"
            "def add(a: int, b: int) -> int:\n"
            "    return a + b"
        )
        for runner in (
            PythonCodeWrapper().wrap(code),
            PythonCodeWrapper().wrap_with_tests(code, CASES),
        ):
            compile(runner, "<runner>", "exec")
        _exec_suite(PythonCodeWrapper().wrap_with_tests(code, CASES))

    def test_string_annotations_need_no_injection_and_exec(self):
        code = (
            'def two_sum(nums: "List[int]", target: int) -> "List[int]":\n'
            "    return list(nums)"
        )
        for runner in (
            PythonCodeWrapper().wrap(code),
            PythonCodeWrapper().wrap_with_tests(code, CASES),
        ):
            assert "from typing import" not in runner
            compile(runner, "<runner>", "exec")
        namespace = _exec_suite(PythonCodeWrapper().wrap_with_tests(code, CASES))
        assert callable(namespace["two_sum"])

    def test_semicolon_shared_future_import_is_left_untouched(self):
        from app.adapters.code_wrappers.python_wrapper import _split_future_imports

        code = "from __future__ import annotations; x = 1"
        assert _split_future_imports(code) == ("", code)
