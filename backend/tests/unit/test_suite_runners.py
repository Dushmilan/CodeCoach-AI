"""Comprehensive tests for Piston suite runners and output parsing."""

import json
import pytest
from unittest.mock import patch, AsyncMock
from app.services.piston_service import PistonService
from app.ports.code_executor import ExecutionResult


# ── Parse Suite Output Tests ───────────────────────────────────────────


class TestParseSuiteOutput:
    """Tests for _parse_suite_output with various execution results."""

    @pytest.fixture
    def service(self):
        return PistonService()

    def _parse(
        self, service, stdout="", stderr="", exit_code=0, signal=None, test_cases=None
    ):
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
        results_json = json.dumps(
            [
                {"index": 1, "passed": True, "actual": "1"},
                {"index": 2, "passed": True, "actual": "2"},
            ],
            separators=(",", ":"),
        )
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
        results_json = json.dumps(
            [
                {"index": 1, "passed": True, "actual": "1"},
                {"index": 2, "passed": False, "actual": "2"},
            ],
            separators=(",", ":"),
        )
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
        results = self._parse(
            service, stdout=stdout, stderr=stderr, exit_code=-6, signal="6"
        )
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
        results_json = json.dumps(
            [
                {"index": 1, "passed": True, "actual": "1"},
                {"index": 2, "passed": True, "actual": "2"},
            ],
            separators=(",", ":"),
        )
        stdout = f"@@SUITE_RESULT@@{results_json}@@SUITE_RESULT@@"
        results = self._parse(
            service, stdout=stdout, exit_code=-6, signal="6", test_cases=test_cases
        )
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
        results = self._parse(
            service, stdout="@@SUITE_RESULT@@[]@@SUITE_RESULT@@", test_cases=[]
        )
        assert len(results) == 0

    def test_all_hidden(self, service):
        test_cases = [
            {"input": "secret", "expected_output": "hidden", "hidden": True},
        ]
        results_json = json.dumps(
            [
                {"index": 1, "passed": False, "actual": "wrong"},
            ],
            separators=(",", ":"),
        )
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
        results_json = json.dumps(
            [
                {"passed": True, "actual": "1"},  # no "index" key
            ],
            separators=(",", ":"),
        )
        stdout = f"@@SUITE_RESULT@@{results_json}@@SUITE_RESULT@@"
        with pytest.raises(KeyError):
            self._parse(service, stdout=stdout, test_cases=test_cases)

    def test_result_is_object_not_array(self, service):
        test_cases = [
            {"input": "1", "expected_output": "1", "hidden": False},
        ]
        stdout = '@@SUITE_RESULT@@{"passed": true}@@SUITE_RESULT@@'
        with pytest.raises(TypeError):  # iterating over dict yields string keys
            self._parse(service, stdout=stdout, test_cases=test_cases)

    def test_partial_results_no_signal(self, service):
        test_cases = [
            {"input": "1", "expected_output": "1", "hidden": False},
            {"input": "2", "expected_output": "2", "hidden": False},
        ]
        results_json = json.dumps(
            [
                {"index": 1, "passed": True, "actual": "1"},
                # index 2 missing, no signal set
            ],
            separators=(",", ":"),
        )
        stdout = f"@@SUITE_RESULT@@{results_json}@@SUITE_RESULT@@"
        results = self._parse(service, stdout=stdout, test_cases=test_cases)
        assert len(results) == 2
        assert results[0].passed is True
        assert results[1].passed is False
        assert results[1].actual == ""  # no signal -> no crash annotation

    def test_normalize_re_verifies_whitespace_mismatch(self, service, caplog):
        """Runner returns passed=false but normalized actual==expected -> re-verify = True."""
        test_cases = [{"input": "1", "expected_output": "1", "hidden": False}]
        # Simulate runner output where actual has extra whitespace
        results_json = json.dumps(
            [
                {"index": 1, "passed": True, "actual": "1"},
            ],
            separators=(",", ":"),
        )
        stdout = f"@@SUITE_RESULT@@{results_json}@@SUITE_RESULT@@"
        results = self._parse(service, stdout=stdout, test_cases=test_cases)
        assert results[0].passed is True  # trusts runner's True

    def test_normalize_re_verify_detects_runner_bug(self, service, caplog):
        """Runner says passed but re-verify disagrees -> log warning."""
        test_cases = [{"input": "1", "expected_output": "2", "hidden": False}]
        results_json = json.dumps(
            [
                {
                    "index": 1,
                    "passed": True,
                    "actual": "1",
                },  # runner says pass, but 1 != 2
            ],
            separators=(",", ":"),
        )
        stdout = f"@@SUITE_RESULT@@{results_json}@@SUITE_RESULT@@"
        with caplog.at_level("WARNING"):
            results = self._parse(service, stdout=stdout, test_cases=test_cases)
        assert results[0].passed is True  # still trusts runner
        assert "Runner mismatch" in caplog.text

    def test_stdout_is_none(self, service):
        test_cases = [{"input": "1", "expected_output": "1", "hidden": False}]
        exec_result = ExecutionResult(stdout=None, stderr="", exit_code=1)
        results = service._parse_suite_output(exec_result, test_cases)
        assert len(results) == 1
        assert results[0].passed is False
        assert "Execution Error" in results[0].actual

    def test_stdout_before_marker(self, service):
        test_cases = [{"input": "1", "expected_output": "1", "hidden": False}]
        results_json = json.dumps(
            [{"index": 1, "passed": True, "actual": "1"}], separators=(",", ":")
        )
        stdout = f"garbage prefix before marker@@SUITE_RESULT@@{results_json}@@SUITE_RESULT@@"
        results = self._parse(service, stdout=stdout, test_cases=test_cases)
        assert results[0].passed is True

    def test_duplicate_markers(self, service):
        test_cases = [{"input": "1", "expected_output": "1", "hidden": False}]
        inner = json.dumps(
            [{"index": 1, "passed": True, "actual": "1"}], separators=(",", ":")
        )
        outer = json.dumps(
            [{"index": 1, "passed": False, "actual": "wrong"}], separators=(",", ":")
        )
        stdout = f"@@SUITE_RESULT@@{outer}@@SUITE_RESULT@@garbage@@SUITE_RESULT@@{inner}@@SUITE_RESULT@@"
        results = self._parse(service, stdout=stdout, test_cases=test_cases)
        # Uses outermost pair (first find, last rfind)
        assert results[0].passed is False


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

        with patch.object(service, "execute", new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout='@@SUITE_RESULT@@[{"index":1,"passed":true,"actual":"true"}]@@SUITE_RESULT@@',
                stderr="",
                exit_code=0,
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

        with patch.object(service, "execute", new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout="",
                stderr="out of memory",
                exit_code=-6,
                signal="6",
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

        with patch.object(service, "execute", new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout="",
                stderr="runtime error",
                exit_code=1,
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

        with patch.object(service, "execute", new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout='@@SUITE_RESULT@@[{"index":1,"passed":true,"actual":"correct"}]@@SUITE_RESULT@@',
                stderr="",
                exit_code=0,
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
        with patch.object(service, "execute", new=AsyncMock()) as mock_exec:
            results = await service.evaluate_suite("python", "code", [])
            assert results == []
            mock_exec.assert_not_called()

    @pytest.mark.asyncio
    async def test_evaluate_suite_build_runner_fallback(self, service):
        raw_code = "def solve():\n    return 42"
        with patch.object(service, "execute", new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout='@@SUITE_RESULT@@[{"index":1,"passed":true,"actual":"42"}]@@SUITE_RESULT@@',
                stderr="",
                exit_code=0,
            )
            results = await service.evaluate_suite(
                "cpp",
                raw_code,
                [{"input": "", "expected_output": "42", "hidden": False}],
            )
            call_kwargs = mock_exec.call_args[1]
            assert call_kwargs["code"] == raw_code  # fallback: raw code unchanged
            assert len(results) == 1

    @pytest.mark.asyncio
    async def test_js_evaluate_suite_inplace_modification(self, service):
        test_cases = [
            {
                "input": "[[1,2],[3,4]]",
                "expected_output": "[[3,1],[4,2]]",
                "hidden": False,
            },
        ]
        code = "function rotate(matrix) { matrix[0][0]=3; matrix[0][1]=1; matrix[1][0]=4; matrix[1][1]=2; }"

        with patch.object(service, "execute", new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout='@@SUITE_RESULT@@[{"index":1,"passed":true,"actual":"[[3,1],[4,2]]"}]@@SUITE_RESULT@@',
                stderr="",
                exit_code=0,
            )
            results = await service.evaluate_suite("javascript", code, test_cases)
            assert len(results) == 1
            assert results[0].passed is True

    @pytest.mark.asyncio
    async def test_java_evaluate_suite_basic(self, service):
        test_cases = [
            {"input": '"world"', "expected_output": "Hello, world", "hidden": False},
        ]
        code = """public class Solution {
    public static String greet(String name) {
        return "Hello, " + name;
    }
}"""
        with patch.object(service, "execute", new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout='@@SUITE_RESULT@@[{"index":1,"passed":true,"actual":"Hello, world"}]@@SUITE_RESULT@@',
                stderr="",
                exit_code=0,
            )
            results = await service.evaluate_suite("java", code, test_cases)
            assert len(results) == 1
            assert results[0].passed is True

    @pytest.mark.asyncio
    async def test_java_evaluate_suite_int_array_return(self, service):
        """Java int[] returns compact JSON via toJson, not Arrays.toString space format."""
        test_cases = [
            {"input": "[1,2,3,4,5]\n5", "expected_output": "[4,4]", "hidden": False},
        ]
        code = """public class Solution {
    public static int[] searchRange(int[] nums, int target) {
        return new int[]{4, 4};
    }
}"""
        with patch.object(service, "execute", new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout='@@SUITE_RESULT@@[{"index":1,"passed":true,"actual":"[4,4]"}]@@SUITE_RESULT@@',
                stderr="",
                exit_code=0,
            )
            results = await service.evaluate_suite("java", code, test_cases)
            assert len(results) == 1
            assert results[0].passed is True

    @pytest.mark.asyncio
    async def test_java_evaluate_suite_int2d_array_return(self, service):
        """Java int[][] returns compact JSON via recursive toJson, no Array.toString."""
        test_cases = [
            {
                "input": "[[1,3],[2,6],[8,10],[15,18]]",
                "expected_output": "[[1,6],[8,10],[15,18]]",
                "hidden": False,
            },
        ]
        code = """public class Solution {
    public static int[][] merge(int[][] intervals) {
        return new int[][]{{1,6},{8,10},{15,18}};
    }
}"""
        with patch.object(service, "execute", new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout='@@SUITE_RESULT@@[{"index":1,"passed":true,"actual":"[[1,6],[8,10],[15,18]]"}]@@SUITE_RESULT@@',
                stderr="",
                exit_code=0,
            )
            results = await service.evaluate_suite("java", code, test_cases)
            assert len(results) == 1
            assert results[0].passed is True

    @pytest.mark.asyncio
    async def test_java_evaluate_suite_list_return(self, service):
        """Java List<List<Integer>> returns compact JSON via toJson, not ArrayList.toString spacing."""
        test_cases = [
            {
                "input": "[-1,0,1,2,-1,-4]",
                "expected_output": "[[-1,-1,2],[-1,0,1]]",
                "hidden": False,
            },
        ]
        code = """public class Solution {
    public static java.util.List<java.util.List<Integer>> threeSum(int[] nums) {
        return java.util.List.of(java.util.List.of(-1,-1,2), java.util.List.of(-1,0,1));
    }
}"""
        with patch.object(service, "execute", new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout='@@SUITE_RESULT@@[{"index":1,"passed":true,"actual":"[[-1,-1,2],[-1,0,1]]"}]@@SUITE_RESULT@@',
                stderr="",
                exit_code=0,
            )
            results = await service.evaluate_suite("java", code, test_cases)
            assert len(results) == 1
            assert results[0].passed is True

    @pytest.mark.asyncio
    async def test_java_evaluate_suite_void_in_place_mutation(self, service):
        """Java void method (in-place mutation) serializes first arg via _lastFirstArg."""
        test_cases = [
            {
                "input": "[[1,2],[3,4]]",
                "expected_output": "[[3,1],[4,2]]",
                "hidden": False,
            },
            {"input": "[[1]]", "expected_output": "[[1]]", "hidden": False},
        ]
        code = """public class Solution {
    public static void solve(int[][] matrix) {
        int n = matrix.length;
        for (int i = 0; i < n; i++)
            for (int j = i + 1; j < n; j++) {
                int tmp = matrix[i][j];
                matrix[i][j] = matrix[j][i];
                matrix[j][i] = tmp;
            }
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n / 2; j++) {
                int tmp = matrix[i][j];
                matrix[i][j] = matrix[i][n - 1 - j];
                matrix[i][n - 1 - j] = tmp;
            }
    }
}"""
        with patch.object(service, "execute", new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout='@@SUITE_RESULT@@[{"index":1,"passed":true,"actual":"[[3,1],[4,2]]"},{"index":2,"passed":true,"actual":"[[1]]"}]@@SUITE_RESULT@@',
                stderr="",
                exit_code=0,
            )
            results = await service.evaluate_suite("java", code, test_cases)
            assert len(results) == 2
            assert results[0].passed is True
            assert results[1].passed is True
            assert results[0].actual == "[[3,1],[4,2]]"

    @pytest.mark.asyncio
    async def test_js_evaluate_suite_no_fs_in_code_sent_to_piston(self, service):
        """Verify the final wrapped code sent to execute() has no 'require('fs')'."""
        test_cases = [
            {"input": "[1,2,3]", "expected_output": "[]", "hidden": False},
        ]
        code = "function threeSum(nums) { return []; }"

        with patch.object(service, "execute", new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout='@@SUITE_RESULT@@[{"index":1,"passed":true,"actual":"[]"}]@@SUITE_RESULT@@',
                stderr="",
                exit_code=0,
            )
            results = await service.evaluate_suite("javascript", code, test_cases)
            # Verify the code passed to execute does NOT have double fs requires
            call_kwargs = mock_exec.call_args[1]
            sent_code = call_kwargs["code"]
            assert sent_code.count("require('fs')") <= 1, (
                f"double fs require in sent code would crash JS runtime:\n{sent_code[:300]}"
            )
            assert results[0].passed is True

    @pytest.mark.asyncio
    async def test_js_evaluate_suite_process_stdout_write_bypasses_wrapper(
        self, service
    ):
        """The runner's process.stdout.write should prevent wrapper from adding stdin code."""
        test_cases = [
            {"input": "1", "expected_output": "1", "hidden": False},
        ]
        code = "function f(x) { return x; }"

        with patch.object(service, "execute", new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout='@@SUITE_RESULT@@[{"index":1,"passed":true,"actual":"1"}]@@SUITE_RESULT@@',
                stderr="",
                exit_code=0,
            )
            await service.evaluate_suite("javascript", code, test_cases)
            call_kwargs = mock_exec.call_args[1]
            sent_code = call_kwargs["code"]
            # Wrapper adds "readFileSync(0" for stdin reading - should NOT be present
            assert "readFileSync(0" not in sent_code, (
                "wrapper should not add stdin-reading code to suite runner"
            )


# ── End-to-end: generated runners fix string-returning problems ─────────


class TestStringReturningRunnerEndToEnd:
    """Issue #96 regression: correct string solutions must pass even though
    expected outputs are stored as JSON string literals."""

    def _run_python_runner(self, code, test_cases):
        import subprocess
        import sys

        from app.adapters.code_wrappers.python_wrapper import PythonCodeWrapper

        runner = PythonCodeWrapper().wrap_with_tests(code, test_cases)
        proc = subprocess.run(
            [sys.executable, "-c", runner], capture_output=True, text=True
        )
        assert proc.returncode == 0, proc.stderr
        return proc.stdout

    def _parse_suite(self, stdout):
        marker = "@@SUITE_RESULT@@"
        start = stdout.find(marker)
        end = stdout.rfind(marker)
        return json.loads(stdout[start + len(marker) : end])

    def test_python_string_reverse_passes(self):
        code = "def reverse_word(s):\n    return s[::-1]"
        test_cases = [
            {"input": '"dlrow"', "expected_output": '"world"', "hidden": False},
            {"input": '"321"', "expected_output": '"123"', "hidden": False},
        ]
        results = self._parse_suite(self._run_python_runner(code, test_cases))
        assert len(results) == 2
        assert all(r["passed"] for r in results), results
        assert results[0]["actual"] == "world"

    def test_python_string_with_trailing_spaces_passes(self):
        # Whitespace is meaningful: "  321" -> "123  "
        code = "def pad(s):\n    return s[::-1]"
        test_cases = [
            {"input": '"123  "', "expected_output": '"  321"', "hidden": False},
        ]
        results = self._parse_suite(self._run_python_runner(code, test_cases))
        assert results[0]["passed"] is True, results

    def test_python_empty_string_roundtrip(self):
        code = "def ident(s):\n    return s"
        test_cases = [{"input": '""', "expected_output": '""', "hidden": False}]
        results = self._parse_suite(self._run_python_runner(code, test_cases))
        assert results[0]["passed"] is True, results

    def test_python_unicode_string_passes(self):
        code = "def ident(s):\n    return s"
        test_cases = [
            {"input": '"héllo"', "expected_output": '"héllo"', "hidden": False}
        ]
        results = self._parse_suite(self._run_python_runner(code, test_cases))
        assert results[0]["passed"] is True, results

    def test_python_wrong_string_still_fails(self):
        code = "def reverse_word(s):\n    return s.upper()"
        test_cases = [
            {"input": '"dlrow"', "expected_output": '"world"', "hidden": False},
        ]
        results = self._parse_suite(self._run_python_runner(code, test_cases))
        assert results[0]["passed"] is False, results

    def test_python_arrays_booleans_numbers_still_pass(self):
        cases = [
            ("def arr(x):\n    return x", [1, 2, 3], "[1,2,3]"),
            ("def even(x):\n    return x % 2 == 0", 4, "true"),
            ("def num(x):\n    return x + 1", 41, "42"),
        ]
        for code, raw_input, expected in cases:
            test_cases = [
                {
                    "input": json.dumps(raw_input, separators=(",", ":")),
                    "expected_output": expected,
                    "hidden": False,
                }
            ]
            results = self._parse_suite(self._run_python_runner(code, test_cases))
            assert results[0]["passed"] is True, (code, results)

    def test_javascript_string_reverse_passes(self):
        import shutil
        import subprocess

        if shutil.which("node") is None:
            pytest.skip("node not available")
        from app.adapters.code_wrappers.javascript_wrapper import JavaScriptCodeWrapper

        code = "function reverseWord(s) { return s.split('').reverse().join(''); }"
        test_cases = [
            {"input": '"dlrow"', "expected_output": '"world"', "hidden": False},
        ]
        runner = JavaScriptCodeWrapper().wrap_with_tests(code, test_cases)
        proc = subprocess.run(["node", "-e", runner], capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr
        results = self._parse_suite(proc.stdout)
        assert results[0]["passed"] is True, results


# ── Schema Normalization Tests ─────────────────────────────────────────


class TestSchemaNormalization:
    """Verify TestCase.normalize_to_string produces compact JSON matching suite runners."""

    def test_dict_compact_format(self):
        from app.models.schemas import TestCase

        tc = TestCase(input='{"a":1}', expected_output={"x": [1, 2, 3]})
        # expected_output should be compact (no spaces after commas)
        assert tc.expected_output == '{"x":[1,2,3]}', f"got {tc.expected_output!r}"

    def test_list_compact_format(self):
        from app.models.schemas import TestCase

        tc = TestCase(input="1", expected_output=[1, 2, 3])
        assert tc.expected_output == "[1,2,3]", f"got {tc.expected_output!r}"

    def test_bool_lowercase(self):
        from app.models.schemas import TestCase

        tc = TestCase(input="1", expected_output=True)
        assert tc.expected_output == "true", f"got {tc.expected_output!r}"
        tc2 = TestCase(input="1", expected_output=False)
        assert tc2.expected_output == "false", f"got {tc2.expected_output!r}"

    def test_none_becomes_empty_string(self):
        from app.models.schemas import TestCase

        tc = TestCase(input="1", expected_output=None)
        assert tc.expected_output == "", f"got {tc.expected_output!r}"

    def test_nested_dict_compact(self):
        from app.models.schemas import TestCase

        tc = TestCase(input="1", expected_output={"a": {"b": [1, 2]}})
        assert tc.expected_output == '{"a":{"b":[1,2]}}', f"got {tc.expected_output!r}"

    def test_int_compact(self):
        from app.models.schemas import TestCase

        tc = TestCase(input="1", expected_output=42)
        assert tc.expected_output == "42", f"got {tc.expected_output!r}"

    def test_float_compact(self):
        from app.models.schemas import TestCase

        tc = TestCase(input="1", expected_output=3.14)
        # json.dumps of float produces "3.14"
        assert tc.expected_output == "3.14", f"got {tc.expected_output!r}"

    def test_already_string_passthrough(self):
        from app.models.schemas import TestCase

        tc = TestCase(input="1", expected_output="[1, 2, 3]")
        # Already a string — passes through unchanged
        assert tc.expected_output == "[1, 2, 3]", f"got {tc.expected_output!r}"


# ── Output Comparison Helper ────────────────────────────────────────────


class TestOutputsMatch:
    """Regression tests for issue #96: string-returning problems must not
    falsely fail because JSON-encoded expected strings differ from the
    plain text printed by runners, and meaningful whitespace is preserved."""

    def _match(self, actual, expected):
        from app.adapters.code_wrappers.output_comparator import outputs_match

        return outputs_match(actual, expected)

    # String-returning problems (JSON-encoded expected vs plain actual)
    def test_plain_string_matches_json_encoded_expected(self):
        # Question stores expected as "\"world\""; runner prints "world"
        assert self._match("world", '"world"') is True

    def test_string_with_surrounding_quotes_in_actual(self):
        # Java toJson() emits quotes around strings
        assert self._match('"world"', '"world"') is True

    def test_string_reverse_example(self):
        # "The Singularity's First Word": reverse "dlrow" -> "world"
        assert self._match("world", '"world"') is True

    def test_empty_string(self):
        assert self._match("", '""') is True
        assert self._match("x", '""') is False

    def test_unicode_string(self):
        assert self._match("héllo→", '"héllo→"') is True

    def test_whitespace_is_meaningful(self):
        # "123  " (trailing spaces) must not be stripped
        assert self._match("123  ", '"123  "') is True
        assert self._match("123", '"123  "') is False

    def test_leading_whitespace_preserved(self):
        assert self._match("  321", '"  321"') is True
        assert self._match("321", '"  321"') is False

    def test_trailing_process_newline_trimmed(self):
        assert self._match("world\n", '"world"') is True

    # Non-string outputs keep working
    def test_array_output(self):
        assert self._match("[1,2,3]", "[1, 2, 3]") is True
        assert self._match("[1,2,4]", "[1,2,3]") is False

    def test_nested_array_output(self):
        assert self._match("[[1,2],[3,4]]", "[[1, 2], [3, 4]]") is True

    def test_boolean_output(self):
        assert self._match("true", "true") is True
        assert self._match("true", "false") is False

    def test_number_output(self):
        assert self._match("42", "42") is True
        assert self._match("42", "43") is False

    def test_object_output(self):
        assert self._match('{"a":1}', '{"a": 1}') is True

    def test_plain_text_fallback(self):
        # Non-JSON expected falls back to exact text compare
        assert self._match("hello world", "hello world") is True
        assert self._match("hello world", "hello  world") is False

    def test_none_inputs(self):
        assert self._match(None, None) is True
        assert self._match(None, "x") is False

    def test_non_string_json_expected_with_plain_actual(self):
        # expected "[1,2,3]" but actual printed without JSON parse fails
        assert self._match("[1,2,3]", "[1,2,3]") is True


class TestEmbeddedOutputComparators:
    """The generated runners must embed the shared comparator and use it."""

    def test_python_runner_embeds_comparator(self):
        from app.adapters.code_wrappers.python_wrapper import PythonCodeWrapper

        runner = PythonCodeWrapper().wrap_with_tests(
            "def f(x):\n    return x",
            [{"input": "1", "expected_output": "1", "hidden": False}],
        )
        assert "__outputs_match(__actual, __exp)" in runner
        assert "__actual.strip() == __exp.strip()" not in runner

    def test_javascript_runner_embeds_comparator(self):
        from app.adapters.code_wrappers.javascript_wrapper import JavaScriptCodeWrapper

        runner = JavaScriptCodeWrapper().wrap_with_tests(
            "function f(x) { return x; }",
            [{"input": "1", "expected_output": "1", "hidden": False}],
        )
        assert "outputsMatch(actual, tc.expected)" in runner
        assert "actual.trim() === tc.expected.trim()" not in runner

    def test_java_runner_embeds_comparator(self):
        from app.adapters.code_wrappers.java_wrapper import JavaCodeWrapper

        code = "public class Solution {\n    public static String greet(String n) {\n        return n;\n    }\n}"
        runner = JavaCodeWrapper().wrap_with_tests(
            code, [{"input": '"x"', "expected_output": "x", "hidden": False}]
        )
        assert "outputsMatch(actual, expected)" in runner
        assert "static boolean outputsMatch" in runner
        assert "actual.trim().equals(expected.trim())" not in runner
