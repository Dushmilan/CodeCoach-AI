"""Comprehensive tests for Piston suite runners and output parsing."""

import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.piston_service import PistonService
from app.ports.code_executor import ExecutionResult, TestCaseResult


# ── Python Suite Runner Tests ──────────────────────────────────────────

class TestPythonSuiteRunner:
    """Tests for _python_suite_runner generated code patterns."""

    @pytest.fixture
    def service(self):
        return PistonService()

    def _generate(self, service, code, test_cases):
        return service._python_suite_runner(code, test_cases)

    def test_single_param_list_return(self, service):
        """three-sum style: single param, returns list of lists."""
        code = "def threeSum(nums):\n    return [[-4,-2,6],[-4,0,4]]"
        test_cases = [
            {"input": "[-4,-2,-2,-2,0,1,2,2,2,3,3,4,4,6,6]", "expected_output": "[[-4,-2,6],[-4,0,4]]", "hidden": False},
        ]
        runner = self._generate(service, code, test_cases)
        assert "def threeSum(nums):" in runner
        assert "json.dumps(__out, separators=(\",\", \":\"))" in runner
        assert "__out, __in_val = __run_test(__tc)" in runner
        assert "threeSum(__parsed)" in runner
        assert "hidden" not in runner

    def test_two_param_int_return(self, service):
        """subarray-sum style: two \\n-separated params, returns int."""
        code = "def subarraySum(nums, k):\n    return 1"
        test_cases = [
            {"input": "[1]\n1", "expected_output": "1", "hidden": False},
        ]
        runner = self._generate(service, code, test_cases)
        assert "subarraySum(__a, __b)" in runner
        assert "str(__out)" in runner  # int return -> str()

    def test_inplace_modification(self, service):
        """rotate-image style: returns None, compare modified input."""
        code = "def rotate(matrix):\n    matrix[:] = [[row[i] for row in reversed(matrix)] for i in range(len(matrix[0]))]"
        test_cases = [
            {"input": "[[1]]", "expected_output": "[[1]]", "hidden": False},
        ]
        runner = self._generate(service, code, test_cases)
        assert "if __out is None:" in runner
        assert "json.dumps(__in_val" in runner

    def test_two_param_list_return(self, service):
        """searchRange style: two params, returns list."""
        code = "def searchRange(nums, target):\n    return [-1,-1]"
        test_cases = [
            {"input": "[]\n0", "expected_output": "[-1,-1]", "hidden": False},
        ]
        runner = self._generate(service, code, test_cases)
        assert "searchRange(__a, __b)" in runner
        assert "json.dumps(__out" in runner

    def test_self_stripping(self, service):
        """User code with 'self' as first param -> regex strips it."""
        code = "def solve(self, nums):\n    return len(nums)"
        test_cases = [
            {"input": "[1,2,3]", "expected_output": "3", "hidden": False},
        ]
        runner = self._generate(service, code, test_cases)
        # self should be stripped from user_code
        assert "(self, nums)" not in runner
        assert "def solve(nums):" in runner

    def test_bool_return(self, service):
        """Function returns bool -> str(out).lower()."""
        code = "def isEven(n):\n    return n % 2 == 0"
        test_cases = [
            {"input": "4", "expected_output": "true", "hidden": False},
        ]
        runner = self._generate(service, code, test_cases)
        assert "str(__out).lower()" in runner

    def test_exception_during_run(self, service):
        """User code raises -> passed=False, actual=error string."""
        code = "def fail(n):\n    raise ValueError('bad')"
        test_cases = [
            {"input": "1", "expected_output": "1", "hidden": False},
        ]
        runner = self._generate(service, code, test_cases)
        assert "except Exception as __e:" in runner
        assert "__passed = False" in runner

    def test_empty_test_cases(self, service):
        """Empty test list -> generated runner with no loop."""
        runner = self._generate(service, "def f(x):\n    return x", [])
        # Should still be valid code
        assert "__test_cases = " in runner
        assert "run_suite()" in runner

    def test_multi_param_spread(self, service):
        """3+ params: each line parsed and spread via *args."""
        code = "def bypass(a, b, c):\n    return a + b + c"
        test_cases = [
            {"input": "1\n2\n3", "expected_output": "6", "hidden": False},
        ]
        runner = self._generate(service, code, test_cases)
        assert "__parsed_args = [json.loads(ln)" in runner
        assert "bypass(*__parsed_args)" in runner
        assert "__parsed_args[0]" in runner  # inVal = first arg

    def test_hidden_not_in_runner(self, service):
        """hidden field removed from repr() to avoid Signal 6 with Python booleans."""
        test_cases = [
            {"input": "1", "expected_output": "1", "hidden": True},
            {"input": "2", "expected_output": "2", "hidden": False},
        ]
        runner = self._generate(service, "def f(x):\n    return x", test_cases)
        assert "\"hidden\"" not in runner
        assert "True" not in runner.replace("True", "", 1)  # only exception handling

    def test_none_return_vs_string_return(self, service):
        """Function returns string (not None) -> str(out)."""
        code = "def greet(name):\n    return 'hello'"
        test_cases = [
            {"input": "\"world\"", "expected_output": "hello", "hidden": False},
        ]
        runner = self._generate(service, code, test_cases)
        assert "if __out is None:" in runner
        assert "str(__out)" in runner


# ── JavaScript Suite Runner Tests ──────────────────────────────────────

class TestJavaScriptSuiteRunner:
    @pytest.fixture
    def service(self):
        return PistonService()

    def _generate(self, service, code, test_cases):
        return service._javascript_suite_runner(code, test_cases)

    def test_single_param(self, service):
        code = "function threeSum(nums) { return [[-4,-2,6],[-4,0,4]]; }"
        test_cases = [
            {"input": "[-4,-2,-2,-2,0,1,2,2,2,3,3,4,4,6,6]", "expected_output": "[[-4,-2,6],[-4,0,4]]", "hidden": False},
        ]
        runner = self._generate(service, code, test_cases)
        assert "threeSum(parsed)" in runner
        assert "inVal = parsed" in runner

    def test_multi_param_spread(self, service):
        code = "function add(a, b, c) { return a + b + c; }"
        test_cases = [
            {"input": "1\n2\n3", "expected_output": "6", "hidden": False},
        ]
        runner = self._generate(service, code, test_cases)
        assert "parsedArgs = lines.map" in runner
        assert "add(...parsedArgs)" in runner

    def test_inplace_modification(self, service):
        code = "function rotate(matrix) { matrix.reverse(); }"
        test_cases = [
            {"input": "[[1,2],[3,4]]", "expected_output": "[[3,4],[1,2]]", "hidden": False},
        ]
        runner = self._generate(service, code, test_cases)
        assert "out == null" in runner
        assert "inVal = parsed" in runner

    def test_bool_return(self, service):
        code = "function isEven(n) { return n % 2 === 0; }"
        test_cases = [
            {"input": "4", "expected_output": "true", "hidden": False},
        ]
        runner = self._generate(service, code, test_cases)
        assert "typeof out === 'boolean'" in runner
        assert "String(out)" in runner

    def test_arrow_function(self, service):
        code = "const threeSum = (nums) => { return []; }"
        test_cases = [
            {"input": "[]", "expected_output": "[]", "hidden": False},
        ]
        runner = self._generate(service, code, test_cases)
        assert "threeSum(parsed)" in runner

    def test_no_fs_require(self, service):
        """Runner should NOT include 'const fs = require' - it would conflict with wrapper."""
        code = "function f(x) { return x; }"
        test_cases = [{"input": "1", "expected_output": "1", "hidden": False}]
        runner = self._generate(service, code, test_cases)
        assert "require('fs')" not in runner
        assert "require(\"fs\")" not in runner

    def test_uses_process_stdout_write(self, service):
        """Runner uses process.stdout.write, which bypasses the wrapper."""
        code = "function f(x) { return x; }"
        test_cases = [{"input": "1", "expected_output": "1", "hidden": False}]
        runner = self._generate(service, code, test_cases)
        assert "process.stdout.write" in runner


# ── Java Suite Runner Tests ────────────────────────────────────────────

class TestJavaSuiteRunner:
    @pytest.fixture
    def service(self):
        return PistonService()

    def _generate(self, service, code, test_cases):
        return service._java_suite_runner(code, test_cases)

    def test_single_string_param(self, service):
        code = """public class Solution {
    public static String greet(String name) {
        return "Hello, " + name;
    }
}"""
        test_cases = [
            {"input": "\"world\"", "expected_output": "Hello, world", "hidden": False},
        ]
        runner = self._generate(service, code, test_cases)
        assert "import java.util.*" in runner
        assert "import java.lang.reflect.*" in runner
        assert "public class Solution" in runner

    def test_generates_valid_structure(self, service):
        code = """public class Solution {
    public static int add(int a, int b) {
        return a + b;
    }
}"""
        test_cases = [
            {"input": "1\n2", "expected_output": "3", "hidden": False},
        ]
        runner = self._generate(service, code, test_cases)
        assert "@@SUITE_RESULT@@" in runner
        assert "parseTcArray" in runner
        assert "toJson(results)" in runner


# ── Parse Suite Output Tests ───────────────────────────────────────────

class TestParseSuiteOutput:
    """Tests for _parse_suite_output with various execution results."""

    @pytest.fixture
    def service(self):
        return PistonService()

    def _parse(self, service, stdout="", stderr="", exit_code=0, signal=None, test_cases=None):
        if test_cases is None:
            test_cases = [{"input": "1", "expected_output": "1", "hidden": False}]
        exec_result = ExecutionResult(
            stdout=stdout, stderr=stderr, exit_code=exit_code, signal=signal
        )
        return service._parse_suite_output(exec_result, test_cases)

    def test_normal_all_pass(self, service):
        test_cases = [
            {"input": "1", "expected_output": "1", "hidden": False},
            {"input": "2", "expected_output": "2", "hidden": True},
        ]
        results_json = json.dumps([
            {"index": 1, "passed": True, "actual": "1"},
            {"index": 2, "passed": True, "actual": "2"},
        ], separators=(",", ":"))
        stdout = f"@@SUITE_RESULT@@{results_json}@@SUITE_RESULT@@"
        results = self._parse(service, stdout=stdout, test_cases=test_cases)
        assert len(results) == 2
        assert results[0].passed is True
        assert results[0].actual == "1"
        assert results[0].input == "1"
        assert results[1].passed is True
        assert results[1].hidden is True
        assert results[1].input == ""  # hidden -> redacted

    def test_partial_pass(self, service):
        test_cases = [
            {"input": "1", "expected_output": "1", "hidden": False},
            {"input": "2", "expected_output": "3", "hidden": False},
        ]
        results_json = json.dumps([
            {"index": 1, "passed": True, "actual": "1"},
            {"index": 2, "passed": False, "actual": "2"},
        ], separators=(",", ":"))
        stdout = f"@@SUITE_RESULT@@{results_json}@@SUITE_RESULT@@"
        results = self._parse(service, stdout=stdout, test_cases=test_cases)
        assert results[0].passed is True
        assert results[1].passed is False
        assert results[1].actual == "2"

    def test_no_marker_in_stdout(self, service):
        stdout = "some random output without markers"
        stderr = "NameError: name 'x' is not defined"
        results = self._parse(service, stdout=stdout, stderr=stderr, exit_code=1)
        assert len(results) == 1
        assert results[0].passed is False
        assert "Execution Error" in results[0].actual
        assert "NameError" in results[0].actual

    def test_signal_set_no_marker(self, service):
        stdout = ""
        stderr = "Process crashed"
        results = self._parse(service, stdout=stdout, stderr=stderr, exit_code=-6, signal="6")
        assert len(results) == 1
        assert results[0].passed is False
        assert "signal 6" in results[0].actual
        assert "Execution Error" in results[0].actual

    def test_signal_set_partial_results(self, service):
        """Runner returned only 2 of 3 test results before signal 6 crash."""
        test_cases = [
            {"input": "1", "expected_output": "1", "hidden": False},
            {"input": "2", "expected_output": "2", "hidden": False},
            {"input": "3", "expected_output": "3", "hidden": False},
        ]
        results_json = json.dumps([
            {"index": 1, "passed": True, "actual": "1"},
            {"index": 2, "passed": True, "actual": "2"},
        ], separators=(",", ":"))
        stdout = f"@@SUITE_RESULT@@{results_json}@@SUITE_RESULT@@"
        results = self._parse(service, stdout=stdout, exit_code=-6, signal="6", test_cases=test_cases)
        assert len(results) == 3
        assert results[0].passed is True
        assert results[1].passed is True
        assert results[2].passed is False
        assert "Crashed" in results[2].actual
        assert "signal 6" in results[2].actual

    def test_json_decode_error(self, service):
        stdout = "@@SUITE_RESULT@@not valid json@@SUITE_RESULT@@"
        results = self._parse(service, stdout=stdout)
        assert len(results) == 1
        assert results[0].passed is False

    def test_signal_with_json_decode_error(self, service):
        stdout = "@@SUITE_RESULT@@broken@@SUITE_RESULT@@"
        results = self._parse(service, stdout=stdout, exit_code=-6, signal="6")
        assert len(results) == 1
        assert results[0].passed is False
        assert "signal 6" in results[0].actual

    def test_empty_test_cases(self, service):
        results = self._parse(service, stdout="@@SUITE_RESULT@@[]@@SUITE_RESULT@@", test_cases=[])
        assert len(results) == 0

    def test_all_hidden(self, service):
        test_cases = [
            {"input": "secret", "expected_output": "hidden", "hidden": True},
        ]
        results_json = json.dumps([
            {"index": 1, "passed": False, "actual": "wrong"},
        ], separators=(",", ":"))
        stdout = f"@@SUITE_RESULT@@{results_json}@@SUITE_RESULT@@"
        results = self._parse(service, stdout=stdout, test_cases=test_cases)
        assert results[0].input == ""
        assert results[0].expected == ""
        assert results[0].actual == ""
        assert results[0].hidden is True

    def test_empty_stdout(self, service):
        results = self._parse(service, stdout="")
        assert len(results) == 1
        assert results[0].passed is False

    def test_missing_index_key_in_results(self, service):
        test_cases = [
            {"input": "1", "expected_output": "1", "hidden": False},
        ]
        results_json = json.dumps([
            {"passed": True, "actual": "1"},  # no "index" key
        ], separators=(",", ":"))
        stdout = f"@@SUITE_RESULT@@{results_json}@@SUITE_RESULT@@"
        with pytest.raises(KeyError):
            self._parse(service, stdout=stdout, test_cases=test_cases)

    def test_result_is_object_not_array(self, service):
        test_cases = [
            {"input": "1", "expected_output": "1", "hidden": False},
        ]
        stdout = "@@SUITE_RESULT@@{\"passed\": true}@@SUITE_RESULT@@"
        with pytest.raises(TypeError):  # iterating over dict yields string keys
            self._parse(service, stdout=stdout, test_cases=test_cases)

    def test_partial_results_no_signal(self, service):
        test_cases = [
            {"input": "1", "expected_output": "1", "hidden": False},
            {"input": "2", "expected_output": "2", "hidden": False},
        ]
        results_json = json.dumps([
            {"index": 1, "passed": True, "actual": "1"},
            # index 2 missing, no signal set
        ], separators=(",", ":"))
        stdout = f"@@SUITE_RESULT@@{results_json}@@SUITE_RESULT@@"
        results = self._parse(service, stdout=stdout, test_cases=test_cases)
        assert len(results) == 2
        assert results[0].passed is True
        assert results[1].passed is False
        assert results[1].actual == ""  # no signal -> no crash annotation

    def test_stdout_is_none(self, service):
        test_cases = [{"input": "1", "expected_output": "1", "hidden": False}]
        exec_result = ExecutionResult(stdout=None, stderr="", exit_code=1)
        results = service._parse_suite_output(exec_result, test_cases)
        assert len(results) == 1
        assert results[0].passed is False
        assert "Execution Error" in results[0].actual

    def test_stdout_before_marker(self, service):
        test_cases = [{"input": "1", "expected_output": "1", "hidden": False}]
        results_json = json.dumps([{"index": 1, "passed": True, "actual": "1"}], separators=(",", ":"))
        stdout = f"garbage prefix before marker@@SUITE_RESULT@@{results_json}@@SUITE_RESULT@@"
        results = self._parse(service, stdout=stdout, test_cases=test_cases)
        assert results[0].passed is True

    def test_duplicate_markers(self, service):
        test_cases = [{"input": "1", "expected_output": "1", "hidden": False}]
        inner = json.dumps([{"index": 1, "passed": True, "actual": "1"}], separators=(",", ":"))
        outer = json.dumps([{"index": 1, "passed": False, "actual": "wrong"}], separators=(",", ":"))
        stdout = f"@@SUITE_RESULT@@{outer}@@SUITE_RESULT@@garbage@@SUITE_RESULT@@{inner}@@SUITE_RESULT@@"
        results = self._parse(service, stdout=stdout, test_cases=test_cases)
        # Uses outermost pair (first find, last rfind)
        assert results[0].passed is False


# ── Wrapper Compatibility Tests ─────────────────────────────────────────

class TestJavaScriptWrapperCompat:
    """Verify JS suite runner output is safe when passed through JavaScriptCodeWrapper.wrap().

    The evaluate_suite codepath calls execute(), which wraps ALL code via
    JavaScriptCodeWrapper.wrap() before sending to Piston. If the generated
    runner code conflicts with the wrapper (e.g. both add 'const fs = require'),
    the submission crashes with a redeclaration SyntaxError.
    """

    @pytest.fixture
    def service(self):
        return PistonService()

    def test_runner_does_not_get_wrapped(self, service):
        """Runner uses process.stdout.write, so wrapper skips it entirely."""
        from app.services.piston_service import JavaScriptCodeWrapper
        wrapper = JavaScriptCodeWrapper()
        code = "function f(x) { return x; }"
        runner = service._javascript_suite_runner(code, [
            {"input": "1", "expected_output": "1", "hidden": False},
        ])
        wrapped = wrapper.wrap(runner)
        # The wrapper should NOT add anything to code that has process.stdout.write
        assert wrapped == runner, "wrapper should skip code with process.stdout.write"

    def test_no_double_fs_declaration(self, service):
        """After wrapping, the final code should have at most one 'require('fs')'."""
        from app.services.piston_service import JavaScriptCodeWrapper
        wrapper = JavaScriptCodeWrapper()
        code = "function f(x) { return x; }"
        runner = service._javascript_suite_runner(code, [
            {"input": "1", "expected_output": "1", "hidden": False},
        ])
        wrapped = wrapper.wrap(runner)
        count = wrapped.count("require('fs')")
        assert count <= 1, f"expected <=1 fs requires, got {count}"


# ── Integration: Suite Runner + Parse Output ───────────────────────────

class TestSuiteRunnerIntegration:
    """End-to-end tests: generate runner, then verify parse logic with mock Piston."""

    @pytest.fixture
    def service(self):
        return PistonService()

    @pytest.mark.asyncio
    async def test_evaluate_suite_mocked(self, service):
        """Mock Piston API call, verify evaluate_suite flow."""
        test_cases = [
            {"input": "4", "expected_output": "true", "hidden": False},
        ]
        code = "def isEven(n):\n    return n % 2 == 0"

        with patch.object(service, 'execute', new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout="@@SUITE_RESULT@@[{\"index\":1,\"passed\":true,\"actual\":\"true\"}]@@SUITE_RESULT@@",
                stderr="", exit_code=0,
            )
            results = await service.evaluate_suite("python", code, test_cases)
            assert len(results) == 1
            assert results[0].passed is True
            assert results[0].actual == "true"
            # Verify execute was called with proper runner code
            call_kwargs = mock_exec.call_args[1]
            assert "isEven" in call_kwargs["code"]
            assert "str(__out).lower()" in call_kwargs["code"]

    @pytest.mark.asyncio
    async def test_evaluate_suite_signal_error(self, service):
        """Piston returns signal 6 -> all tests show signal error."""
        test_cases = [
            {"input": "1", "expected_output": "1", "hidden": False},
        ]
        code = "def f(x):\n    return x"

        with patch.object(service, 'execute', new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout="", stderr="out of memory", exit_code=-6, signal="6",
            )
            results = await service.evaluate_suite("python", code, test_cases)
            assert len(results) == 1
            assert results[0].passed is False
            assert "signal 6" in results[0].actual

    @pytest.mark.asyncio
    async def test_evaluate_suite_no_output(self, service):
        """Empty stdout from Piston -> whole suite failed."""
        test_cases = [
            {"input": "1", "expected_output": "1", "hidden": False},
        ]
        code = "def f(x):\n    return x"

        with patch.object(service, 'execute', new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout="", stderr="runtime error", exit_code=1,
            )
            results = await service.evaluate_suite("python", code, test_cases)
            assert len(results) == 1
            assert results[0].passed is False
            assert "Execution Error" in results[0].actual

    @pytest.mark.asyncio
    async def test_evaluate_suite_hidden(self, service):
        """Hidden test cases -> actual blanked out."""
        test_cases = [
            {"input": "secret", "expected_output": "hidden_val", "hidden": True},
        ]
        code = "def f(x):\n    return x"

        with patch.object(service, 'execute', new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout="@@SUITE_RESULT@@[{\"index\":1,\"passed\":true,\"actual\":\"correct\"}]@@SUITE_RESULT@@",
                stderr="", exit_code=0,
            )
            results = await service.evaluate_suite("python", code, test_cases)
            assert results[0].hidden is True
            assert results[0].passed is True
            assert results[0].input == ""
            assert results[0].expected == ""
            assert results[0].actual == ""

    # ── JavaScript integration tests ────────────────────────────────────

    @pytest.mark.asyncio
    async def test_evaluate_suite_unsupported_language(self, service):
        with pytest.raises(Exception) as exc:
            await service.evaluate_suite("brainfuck", "code", [])
        assert "Unsupported" in str(exc.value)

    @pytest.mark.asyncio
    async def test_evaluate_suite_empty_test_cases(self, service):
        with patch.object(service, 'execute', new=AsyncMock()) as mock_exec:
            results = await service.evaluate_suite("python", "code", [])
            assert results == []
            mock_exec.assert_not_called()

    @pytest.mark.asyncio
    async def test_evaluate_suite_build_runner_fallback(self, service):
        raw_code = "def solve():\n    return 42"
        with patch.object(service, 'execute', new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout="@@SUITE_RESULT@@[{\"index\":1,\"passed\":true,\"actual\":\"42\"}]@@SUITE_RESULT@@",
                stderr="", exit_code=0,
            )
            results = await service.evaluate_suite("cpp", raw_code, [{"input": "", "expected_output": "42", "hidden": False}])
            call_kwargs = mock_exec.call_args[1]
            assert call_kwargs["code"] == raw_code  # fallback: raw code unchanged
            assert len(results) == 1

    @pytest.mark.asyncio
    async def test_js_evaluate_suite_inplace_modification(self, service):
        test_cases = [
            {"input": "[[1,2],[3,4]]", "expected_output": "[[3,1],[4,2]]", "hidden": False},
        ]
        code = "function rotate(matrix) { matrix[0][0]=3; matrix[0][1]=1; matrix[1][0]=4; matrix[1][1]=2; }"

        with patch.object(service, 'execute', new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout="@@SUITE_RESULT@@[{\"index\":1,\"passed\":true,\"actual\":\"[[3,1],[4,2]]\"}]@@SUITE_RESULT@@",
                stderr="", exit_code=0,
            )
            results = await service.evaluate_suite("javascript", code, test_cases)
            assert len(results) == 1
            assert results[0].passed is True

    @pytest.mark.asyncio
    async def test_java_evaluate_suite_basic(self, service):
        test_cases = [
            {"input": "\"world\"", "expected_output": "Hello, world", "hidden": False},
        ]
        code = """public class Solution {
    public static String greet(String name) {
        return "Hello, " + name;
    }
}"""
        with patch.object(service, 'execute', new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout="@@SUITE_RESULT@@[{\"index\":1,\"passed\":true,\"actual\":\"Hello, world\"}]@@SUITE_RESULT@@",
                stderr="", exit_code=0,
            )
            results = await service.evaluate_suite("java", code, test_cases)
            assert len(results) == 1
            assert results[0].passed is True

    @pytest.mark.asyncio
    async def test_js_evaluate_suite_no_fs_in_code_sent_to_piston(self, service):
        """Verify the final wrapped code sent to execute() has no 'require('fs')'."""
        test_cases = [
            {"input": "[1,2,3]", "expected_output": "[]", "hidden": False},
        ]
        code = "function threeSum(nums) { return []; }"

        with patch.object(service, 'execute', new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout="@@SUITE_RESULT@@[{\"index\":1,\"passed\":true,\"actual\":\"[]\"}]@@SUITE_RESULT@@",
                stderr="", exit_code=0,
            )
            results = await service.evaluate_suite("javascript", code, test_cases)
            # Verify the code passed to execute does NOT have double fs requires
            call_kwargs = mock_exec.call_args[1]
            sent_code = call_kwargs["code"]
            assert sent_code.count("require('fs')") <= 1, \
                f"double fs require in sent code would crash JS runtime:\n{sent_code[:300]}"
            assert results[0].passed is True

    @pytest.mark.asyncio
    async def test_js_evaluate_suite_process_stdout_write_bypasses_wrapper(self, service):
        """The runner's process.stdout.write should prevent wrapper from adding stdin code."""
        test_cases = [
            {"input": "1", "expected_output": "1", "hidden": False},
        ]
        code = "function f(x) { return x; }"

        with patch.object(service, 'execute', new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout="@@SUITE_RESULT@@[{\"index\":1,\"passed\":true,\"actual\":\"1\"}]@@SUITE_RESULT@@",
                stderr="", exit_code=0,
            )
            await service.evaluate_suite("javascript", code, test_cases)
            call_kwargs = mock_exec.call_args[1]
            sent_code = call_kwargs["code"]
            # Wrapper adds "readFileSync(0" for stdin reading - should NOT be present
            assert "readFileSync(0" not in sent_code, \
                "wrapper should not add stdin-reading code to suite runner"
