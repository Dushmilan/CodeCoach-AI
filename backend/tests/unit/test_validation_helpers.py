"""Unit tests for validation helper branches (complexity levels, output
formats, output comparison, starter-code parsing).

These pure-logic helpers back the question-validation gate; pinning their
branches keeps the gate's decisions deterministic and covered.
"""

import pytest

from app.ports.code_executor import ExecutionResult
from app.use_cases.question_validation.output_format import (
    OutputFormatValidationUseCase,
)
from app.use_cases.question_validation.solution import SolutionValidationUseCase
from app.use_cases.question_validation.starter_code import (
    StarterCodeValidationUseCase,
)
from app.use_cases.question_validation.time_limits import TimeLimitValidationUseCase


class TestComplexityLevels:
    @pytest.mark.parametrize(
        "complexity,expected",
        [
            ("O(1)", 0),
            ("constant time", 0),
            ("O(log n)", 1),
            ("O(n)", 2),
            ("linear", 2),
            ("O(n log n)", 3),
            ("O(n^2)", 4),
            ("O(n²)", 4),
            ("O(n^3)", 5),
            ("O(2^n)", 6),
            ("O(n!)", 7),
            ("", 0),
            ("mystery", 2),
        ],
    )
    def test_get_complexity_level(self, complexity, expected):
        uc = TimeLimitValidationUseCase()
        assert uc._get_complexity_level(complexity) == expected

    @pytest.mark.parametrize(
        "complexity,n,expected",
        [
            ("O(1)", 1000, 1),
            ("O(log n)", 8, 3.0),
            ("O(n)", 50, 50),
            ("O(n log n)", 8, 24.0),
            ("O(n^2)", 9, 81),
            ("O(n^3)", 4, 64),
            ("O(2^n)", 5, 32),
            ("O(n!)", 4, 24),
            ("O(n)", 0, 0),
        ],
    )
    def test_estimate_operations(self, complexity, n, expected):
        uc = TimeLimitValidationUseCase()
        assert uc._estimate_operations(complexity, n) == expected


class TestOutputFormatDetection:
    @pytest.mark.parametrize(
        "output,expected",
        [
            ("[1,2,3]", "json_array"),
            ("[1,2", "string"),
            ('{"a": 1}', "json_object"),
            ('{"a": }', "string"),
            ("42", "number"),
            ("3.14", "number"),
            ("true", "boolean"),
            ("FALSE", "boolean"),
            ("hello world", "string"),
        ],
    )
    def test_detect_output_format(self, output, expected):
        uc = OutputFormatValidationUseCase()
        assert uc._detect_output_format(output) == expected

    def test_number_string_compatible(self):
        uc = OutputFormatValidationUseCase()
        assert uc._are_formats_compatible("number", "string") is True
        assert uc._are_formats_compatible("boolean", "string") is True
        assert uc._are_formats_compatible("number", "boolean") is False
        assert uc._are_formats_compatible("json_array", "json_object") is False


class TestCompareOutputs:
    @pytest.mark.parametrize(
        "actual,expected,match",
        [
            ("42", "42", True),
            ("42\n", "42", True),
            ("[1, 2]", "[1,2]", True),
            ("3.0", "3", True),
            ("True", "true", True),
            ("abc", "abd", False),
            ("[1]", '{"a": 1}', False),
        ],
    )
    def test_compare_outputs(self, actual, expected, match):
        uc = SolutionValidationUseCase()
        assert uc._compare_outputs(actual, expected) is match


class TestStarterCodeHelpers:
    def test_escape_code(self):
        uc = StarterCodeValidationUseCase()
        assert uc._escape_code('a\\b """c"""') == 'a\\\\b \\"\\"\\"c\\"\\"\\"'

    def test_parse_error_message_variants(self):
        uc = StarterCodeValidationUseCase()
        assert uc._parse_error_message("python", "") == "Unknown error"
        assert (
            uc._parse_error_message("python", "ok\nSyntaxError: bad\nmore")
            == "SyntaxError: bad"
        )
        assert (
            uc._parse_error_message("python", "some output line") == "some output line"
        )
        long_err = "x" * 300
        assert uc._parse_error_message("python", long_err) == "x" * 300
        assert uc._parse_error_message("python", "   \n  ") == ("   \n  ")[:200]

    def test_syntax_test_code_per_language(self):
        uc = StarterCodeValidationUseCase()
        assert "compile(" in uc._create_syntax_test_code("python", "x=1")
        js = uc._create_syntax_test_code("javascript", "let x = 1;")
        assert js.startswith("let x = 1;")
        assert uc._create_syntax_test_code("java", "code") == "code"
        assert uc._create_syntax_test_code("go", "code") == "code"

    @pytest.mark.asyncio
    async def test_basic_validate_unknown_language_returns_no_issues(self):
        uc = StarterCodeValidationUseCase()
        assert uc._basic_validate("go", "package main") == []

    @pytest.mark.asyncio
    async def test_executor_exception_becomes_warning(self):
        class BoomExecutor:
            async def execute(self, **kwargs):
                raise RuntimeError("sandbox down")

        uc = StarterCodeValidationUseCase(executor=BoomExecutor())
        issues = await uc._validate_syntax("python", "x = 1")
        assert len(issues) == 1
        assert issues[0].severity.value == "warning"

    @pytest.mark.asyncio
    async def test_executor_failure_reports_syntax_error(self):
        class FailExecutor:
            async def execute(self, **kwargs):
                return ExecutionResult(
                    stdout="", stderr="SyntaxError: invalid syntax", exit_code=1
                )

        uc = StarterCodeValidationUseCase(executor=FailExecutor())
        issues = await uc._validate_syntax("python", "def broken(:")
        assert len(issues) == 1
        assert "Syntax error" in issues[0].message
