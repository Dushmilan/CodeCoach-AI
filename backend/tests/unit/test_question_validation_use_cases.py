"""
Unit tests for question validation use cases.

This module contains test-driven tests for validating questions before they
are made available to users. Tests focus on Python coverage using Piston.
"""

import pytest
from typing import Dict, Any
from unittest.mock import AsyncMock

from app.models.schemas import Question, Difficulty
from app.models.question_validation_schemas import (
    ValidationUseCase,
    ValidationSeverity,
    QuestionValidationConfig,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def valid_question_data() -> Dict[str, Any]:
    """Create valid question data for testing."""
    return {
        "id": "test-question-1",
        "title": "Test Question",
        "difficulty": Difficulty.EASY,
        "category": "Arrays",
        "company_tags": ["Google"],
        "description": "This is a test question description that is long enough to pass validation.",
        "starter": {
            "python": "def solve(nums: List[int]) -> List[int]:\n    # Your code here\n    pass",
            "javascript": "function solve(nums) {\n    // Your code here\n}",
            "java": "class Solution {\n    public int[] solve(int[] nums) {\n        // Your code here\n    }\n}",
        },
        "examples": [
            {
                "input": "nums = [1,2,3]",
                "output": "[1,2,3]",
                "explanation": "Test explanation",
            }
        ],
        "test_cases": [
            {
                "input": "[1,2,3]",
                "expected_output": "[1,2,3]",
                "description": "Basic test case",
                "hidden": False,
            },
            {
                "input": "[4,5,6]",
                "expected_output": "[4,5,6]",
                "description": "Another test case",
                "hidden": True,
            },
        ],
        "hints": ["Think about the problem"],
        "solution": "Return the array as is.",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
        "constraints": ["1 <= nums.length <= 100"],
    }


@pytest.fixture
def valid_question(valid_question_data) -> Question:
    """Create a valid Question instance."""
    return Question(**valid_question_data)


@pytest.fixture
def invalid_question_missing_id() -> Question:
    """Create a question with missing ID."""
    data = {
        "id": "",  # Invalid: empty ID
        "title": "Test Question",
        "difficulty": Difficulty.EASY,
        "category": "Arrays",
        "company_tags": [],
        "description": "A valid description that is long enough.",
        "starter": {
            "python": "def solve(): pass",
            "javascript": "function solve() {}",
            "java": "class Solution { public void solve() {} }",
        },
        "examples": [{"input": "test", "output": "test"}],
        "test_cases": [{"input": "test", "expected_output": "test"}],
        "hints": [],
        "constraints": [],
    }
    return Question(**data)


@pytest.fixture
def question_with_invalid_test_cases() -> Question:
    """Create a question with invalid test cases."""
    data = {
        "id": "invalid-tests",
        "title": "Invalid Test Cases",
        "difficulty": Difficulty.EASY,
        "category": "Arrays",
        "company_tags": [],
        "description": "A valid description that is long enough for validation.",
        "starter": {
            "python": "def solve(): pass",
            "javascript": "function solve() {}",
            "java": "class Solution { public void solve() {} }",
        },
        "examples": [{"input": "test", "output": "test"}],
        "test_cases": [],  # Invalid: no test cases
        "hints": [],
        "constraints": [],
    }
    return Question(**data)


@pytest.fixture
def question_with_bad_starter_code() -> Question:
    """Create a question with invalid starter code."""
    data = {
        "id": "bad-starter",
        "title": "Bad Starter Code",
        "difficulty": Difficulty.EASY,
        "category": "Arrays",
        "company_tags": [],
        "description": "A valid description that is long enough for validation.",
        "starter": {
            "python": "def solve(:",  # Invalid Python syntax
            "javascript": "function solve() {",
            "java": "class Solution { public void solve() {} }",
        },
        "examples": [{"input": "test", "output": "test"}],
        "test_cases": [{"input": "test", "expected_output": "test"}],
        "hints": [],
        "constraints": [],
    }
    return Question(**data)


@pytest.fixture
def mock_piston_service():
    """Create a mock executor for testing."""
    from app.ports.code_executor import CodeExecutor

    return AsyncMock(spec=CodeExecutor)


# ============================================================================
# StructureValidationUseCase Tests
# ============================================================================


class TestStructureValidationUseCase:
    """Tests for the structure validation use case."""

    @pytest.mark.asyncio
    async def test_valid_question_passes_structure_validation(self, valid_question):
        """Test that a valid question passes structure validation."""
        from app.services.question_validator import StructureValidationUseCase

        use_case = StructureValidationUseCase()
        result = await use_case.execute(valid_question)

        assert result.passed is True
        assert result.use_case == ValidationUseCase.STRUCTURE
        assert len(result.issues) == 0

    @pytest.mark.asyncio
    async def test_question_with_empty_id_fails_validation(
        self, invalid_question_missing_id
    ):
        """Test that a question with empty ID fails validation."""
        from app.services.question_validator import StructureValidationUseCase

        use_case = StructureValidationUseCase()
        result = await use_case.execute(invalid_question_missing_id)

        assert result.passed is False
        assert any(issue.field == "id" for issue in result.issues)

    @pytest.mark.asyncio
    async def test_question_with_short_title_fails_validation(
        self, valid_question_data
    ):
        """Test that a question with too short title fails validation."""
        valid_question_data["title"] = "Hi"  # Too short
        question = Question(**valid_question_data)

        from app.services.question_validator import StructureValidationUseCase

        use_case = StructureValidationUseCase()
        result = await use_case.execute(question)

        assert result.passed is False
        assert any(issue.field == "title" for issue in result.issues)

    @pytest.mark.asyncio
    async def test_question_with_short_description_fails_validation(
        self, valid_question_data
    ):
        """Test that a question with too short description fails validation."""
        valid_question_data["description"] = "Too short"  # Less than 50 chars
        question = Question(**valid_question_data)

        from app.services.question_validator import StructureValidationUseCase

        use_case = StructureValidationUseCase()
        result = await use_case.execute(question)

        assert result.passed is False
        assert any(issue.field == "description" for issue in result.issues)

    @pytest.mark.asyncio
    async def test_question_missing_starter_language_fails_validation(
        self, valid_question_data
    ):
        """Test that missing starter code for a language fails validation."""
        valid_question_data["starter"]["python"] = ""  # Empty Python starter
        question = Question(**valid_question_data)

        from app.services.question_validator import StructureValidationUseCase

        use_case = StructureValidationUseCase()
        result = await use_case.execute(question)

        assert result.passed is False
        assert any(issue.language == "python" for issue in result.issues)


# ============================================================================
# TestCaseValidationUseCase Tests
# ============================================================================


class TestTestCaseValidationUseCase:
    """Tests for test case validation use case."""

    @pytest.mark.asyncio
    async def test_question_with_no_test_cases_fails_validation(
        self, question_with_invalid_test_cases
    ):
        """Test that a question with no test cases fails validation."""
        from app.services.question_validator import TestCaseValidationUseCase

        use_case = TestCaseValidationUseCase()
        result = await use_case.execute(question_with_invalid_test_cases)

        assert result.passed is False
        assert any(
            issue.use_case == ValidationUseCase.TEST_CASES for issue in result.issues
        )

    @pytest.mark.asyncio
    async def test_test_case_with_empty_input_fails_validation(
        self, valid_question_data
    ):
        """Test that test case with empty input fails validation."""
        valid_question_data["test_cases"] = [
            {"input": "", "expected_output": "result"}  # Empty input
        ]
        question = Question(**valid_question_data)

        from app.services.question_validator import TestCaseValidationUseCase

        use_case = TestCaseValidationUseCase()
        result = await use_case.execute(question)

        assert result.passed is False

    @pytest.mark.asyncio
    async def test_test_case_executability_validated_with_piston(
        self, valid_question, mock_piston_service
    ):
        """Test that test case executability is validated using Piston."""
        from app.services.question_validator import TestCaseValidationUseCase
        from app.ports.code_executor import ExecutionResult

        # Mock executor response for successful execution
        mock_piston_service.execute.return_value = ExecutionResult(
            stdout="[1, 2, 3]", exit_code=0
        )

        use_case = TestCaseValidationUseCase(executor=mock_piston_service)
        result = await use_case.execute(valid_question)

        # Should have called executor to validate test case executability
        assert mock_piston_service.execute.called or result.passed is True

    @pytest.mark.asyncio
    async def test_hidden_test_cases_have_different_inputs(self, valid_question_data):
        """Test that hidden test cases have different inputs from visible ones."""
        # Create duplicate test cases (one hidden, one visible with same input)
        valid_question_data["test_cases"] = [
            {"input": "[1,2,3]", "expected_output": "[1,2,3]", "hidden": False},
            {
                "input": "[1,2,3]",
                "expected_output": "[1,2,3]",
                "hidden": True,
            },  # Same input!
        ]
        question = Question(**valid_question_data)

        from app.services.question_validator import TestCaseValidationUseCase

        use_case = TestCaseValidationUseCase()
        result = await use_case.execute(question)

        # Should warn about duplicate test cases
        assert any(
            issue.severity == ValidationSeverity.WARNING for issue in result.issues
        )


# ============================================================================
# StarterCodeValidationUseCase Tests
# ============================================================================


class TestStarterCodeValidationUseCase:
    """Tests for starter code validation use case."""

    @pytest.mark.asyncio
    async def test_valid_starter_code_passes_validation(
        self, valid_question, mock_piston_service
    ):
        """Test that valid starter code passes validation."""
        from app.services.question_validator import StarterCodeValidationUseCase
        from app.ports.code_executor import ExecutionResult

        # Mock executor to return success for syntax check
        mock_piston_service.execute.return_value = ExecutionResult(
            stdout="", exit_code=0
        )

        use_case = StarterCodeValidationUseCase(executor=mock_piston_service)
        result = await use_case.execute(valid_question)

        assert result.passed is True

    @pytest.mark.asyncio
    async def test_invalid_python_starter_code_fails_validation(
        self, question_with_bad_starter_code
    ):
        """Test that invalid Python starter code fails validation."""
        from app.services.question_validator import StarterCodeValidationUseCase
        from app.ports.code_executor import CodeExecutor, ExecutionResult

        executor = AsyncMock(spec=CodeExecutor)
        executor.execute.return_value = ExecutionResult(
            exit_code=1, stderr="SyntaxError: invalid syntax"
        )

        use_case = StarterCodeValidationUseCase(executor=executor)
        result = await use_case.execute(question_with_bad_starter_code)

        assert result.passed is False
        assert any(issue.language == "python" for issue in result.issues)

    @pytest.mark.asyncio
    async def test_all_languages_validated(self, valid_question):
        """Test that all three languages are validated."""
        from app.services.question_validator import StarterCodeValidationUseCase
        from app.ports.code_executor import CodeExecutor, ExecutionResult

        executor = AsyncMock(spec=CodeExecutor)
        executor.execute.return_value = ExecutionResult(stdout="", exit_code=0)

        use_case = StarterCodeValidationUseCase(executor=executor)
        _result = await use_case.execute(valid_question)

        # Should validate Python, JavaScript, and Java
        assert executor.execute.call_count >= 3


# ============================================================================
# SolutionValidationUseCase Tests
# ============================================================================


class TestSolutionValidationUseCase:
    """Tests for solution validation use case."""

    @pytest.mark.asyncio
    async def test_solution_passes_all_test_cases(
        self, valid_question_data, mock_piston_service
    ):
        """Test that the reference solution passes all test cases."""
        from app.services.question_validator import SolutionValidationUseCase
        from app.ports.code_executor import ExecutionResult

        # Create a question with actual solution code
        valid_question_data["starter"]["python"] = """
def solve(nums):
    return nums

import sys
import json
lines = sys.stdin.read().strip().split('\\n')
nums = json.loads(lines[0])
result = solve(nums)
print(json.dumps(result))
"""
        valid_question_data["solution"] = "return nums"
        # Use single test case for simplicity
        valid_question_data["test_cases"] = [
            {
                "input": "[1,2,3]",
                "expected_output": "[1,2,3]",
                "description": "Basic test case",
                "hidden": False,
            }
        ]
        question = Question(**valid_question_data)

        # Mock executor to return correct output
        mock_piston_service.execute.return_value = ExecutionResult(
            stdout="[1,2,3]", exit_code=0
        )

        use_case = SolutionValidationUseCase(executor=mock_piston_service)
        result = await use_case.execute(question)

        # Should pass since we have executable code
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_solution_fails_test_case(
        self, valid_question_data, mock_piston_service
    ):
        """Test that solution failing a test case is detected."""
        # Create question with solution that doesn't match expected output
        valid_question_data["solution"] = "def solve(nums): return []"  # Wrong solution
        question = Question(**valid_question_data)

        from app.services.question_validator import SolutionValidationUseCase
        from app.ports.code_executor import ExecutionResult

        # Mock executor to return wrong output
        mock_piston_service.execute.return_value = ExecutionResult(
            stdout="[]", exit_code=0
        )

        use_case = SolutionValidationUseCase(executor=mock_piston_service)
        result = await use_case.execute(question)

        assert result.passed is False
        assert any(
            issue.use_case == ValidationUseCase.SOLUTION for issue in result.issues
        )

    @pytest.mark.asyncio
    async def test_solution_missing_fails_validation(
        self, valid_question_data, mock_piston_service
    ):
        """Test that missing solution fails validation."""
        valid_question_data["solution"] = None
        question = Question(**valid_question_data)

        from app.services.question_validator import SolutionValidationUseCase

        use_case = SolutionValidationUseCase(executor=mock_piston_service)
        result = await use_case.execute(question)

        assert result.passed is False
        assert any("solution" in issue.message.lower() for issue in result.issues)


# ============================================================================
# TimeLimitValidationUseCase Tests
# ============================================================================


class TestTimeLimitValidationUseCase:
    """Tests for time limit validation use case."""

    @pytest.mark.asyncio
    async def test_default_time_limits_are_valid(self, valid_question):
        """Test that default time limits are valid."""
        from app.services.question_validator import TimeLimitValidationUseCase

        use_case = TimeLimitValidationUseCase()
        result = await use_case.execute(valid_question)

        assert result.passed is True

    @pytest.mark.asyncio
    async def test_time_limit_within_bounds(self, valid_question_data):
        """Test that time limits within bounds pass validation."""
        # Time complexity implies reasonable time limit
        valid_question_data["time_complexity"] = "O(n)"
        question = Question(**valid_question_data)

        from app.services.question_validator import TimeLimitValidationUseCase

        use_case = TimeLimitValidationUseCase()
        result = await use_case.execute(question)

        assert result.passed is True

    @pytest.mark.asyncio
    async def test_slow_algorithm_warns_about_time_limit(self, valid_question_data):
        """Test that slow algorithms get warnings about time limits."""
        valid_question_data["time_complexity"] = "O(n^3)"
        question = Question(**valid_question_data)

        from app.services.question_validator import TimeLimitValidationUseCase

        use_case = TimeLimitValidationUseCase()
        result = await use_case.execute(question)

        # Should warn about potential time limit issues
        assert any(
            issue.severity == ValidationSeverity.WARNING for issue in result.issues
        )


# ============================================================================
# FunctionSignatureValidationUseCase Tests
# ============================================================================


class TestFunctionSignatureValidationUseCase:
    """Tests for function signature validation use case."""

    @pytest.mark.asyncio
    async def test_valid_function_signature_passes(self, valid_question_data):
        """Test that valid function signature passes validation."""
        from app.services.question_validator import FunctionSignatureValidationUseCase

        # Create question with valid Java method signature and Python type hints
        valid_question_data["starter"]["java"] = """
class Solution {
    public int[] solve(int[] nums) {
        // Your code here
        return new int[0];
    }
}
"""
        valid_question_data["starter"]["python"] = """
from typing import List

def solve(nums: List[int]) -> List[int]:
    # Your code here
    pass
"""
        question = Question(**valid_question_data)

        use_case = FunctionSignatureValidationUseCase()
        result = await use_case.execute(question)

        assert result.passed is True

    @pytest.mark.asyncio
    async def test_missing_type_hints_warning(self, valid_question_data):
        """Test that missing type hints generate warnings."""
        # Remove type hints from Python starter
        valid_question_data["starter"]["python"] = "def solve(nums):\n    pass"
        question = Question(**valid_question_data)

        from app.services.question_validator import FunctionSignatureValidationUseCase

        use_case = FunctionSignatureValidationUseCase(require_type_hints=True)
        result = await use_case.execute(question)

        assert any(
            issue.severity == ValidationSeverity.WARNING for issue in result.issues
        )

    @pytest.mark.asyncio
    async def test_invalid_return_type_fails(self, valid_question_data):
        """Test that invalid return type fails validation."""
        # Use invalid return type
        valid_question_data["starter"]["python"] = (
            "def solve(nums) -> InvalidType:\n    pass"
        )
        question = Question(**valid_question_data)

        from app.services.question_validator import FunctionSignatureValidationUseCase

        use_case = FunctionSignatureValidationUseCase()
        result = await use_case.execute(question)

        # Should warn about potentially invalid type hint
        assert len(result.issues) > 0


class TestFunctionSignatureCoverageGaps:
    """Round 2: close the function_signature.py coverage gap with real tests.

    Each test pins observable validator behavior for a previously
    unexecuted line/branch (measured 87.4% lines unit-only vs the 91.1%
    floor): default-valued params, case-insensitive builtins, trailing
    commas, missing definitions, invalid names, arrow-function JS,
    non-camelCase Java, cross-language name mismatches, and the
    generic-alias validity path (Optional/Union/Callable).
    """

    def _use_case(self):
        from app.services.question_validator import FunctionSignatureValidationUseCase

        return FunctionSignatureValidationUseCase()

    def _python_issues(self, code: str):
        return self._use_case()._validate_python_signature(code)

    def _js_issues(self, code: str):
        return self._use_case()._validate_javascript_signature(code)

    def _java_issues(self, code: str):
        return self._use_case()._validate_java_signature(code)

    def test_default_valued_params_are_stripped_not_flagged(self):
        issues = self._python_issues(
            "def solve(nums: List[int] = None, target: int = 0) -> int:\n    pass"
        )
        assert [i for i in issues if i.severity == ValidationSeverity.ERROR] == []
        assert not any("missing type hint" in i.message for i in issues)

    def test_case_insensitive_builtin_spellings_are_valid(self):
        issues = self._python_issues("def solve(nums: LIST) -> INT:\n    pass")
        assert not any("Potentially invalid" in i.message for i in issues)

    def test_generic_aliases_validate_without_startswith_fallback(self):
        for hint in ("Optional[int]", "Union[int, str]", "Callable[[int], int]"):
            assert self._use_case()._is_valid_python_type(hint) is True

    def test_nested_generic_commas_do_not_split_params(self):
        params = self._use_case()._parse_python_params("m: Dict[str, int]")
        assert params == [("m", "Dict[str, int]")]

    def test_trailing_comma_param_is_ignored(self):
        params = self._use_case()._parse_python_params("nums: List[int],")
        assert params == [("nums", "List[int]")]

    def test_missing_python_definition_is_error(self):
        issues = self._python_issues("nums = [1, 2, 3]")
        assert any(
            i.severity == ValidationSeverity.ERROR
            and "No valid Python function definition" in i.message
            for i in issues
        )

    def test_invalid_python_function_name_warns(self):
        issues = self._python_issues("def 2solve(nums: int) -> int:\n    pass")
        assert any(
            i.severity == ValidationSeverity.WARNING
            and "Invalid Python function name" in i.message
            for i in issues
        )

    def test_unknown_param_type_hint_is_info(self):
        issues = self._python_issues("def solve(nums: CustomType) -> int:\n    pass")
        assert any(
            i.severity == ValidationSeverity.INFO
            and "nums" in i.message
            and "CustomType" in i.message
            for i in issues
        )

    def test_arrow_function_js_has_no_missing_definition_error(self):
        issues = self._js_issues("const solve = (nums) => nums;")
        assert [i for i in issues if i.severity == ValidationSeverity.ERROR] == []

    def test_missing_js_definition_is_error(self):
        issues = self._js_issues("let x = 42;")
        assert any(
            i.severity == ValidationSeverity.ERROR
            and "No valid JavaScript function definition" in i.message
            for i in issues
        )

    def test_invalid_js_function_name_warns(self):
        issues = self._js_issues("const 123abc = (x) => x;")
        assert any(
            i.severity == ValidationSeverity.WARNING
            and "Invalid JavaScript function name" in i.message
            for i in issues
        )

    def test_missing_java_definition_is_error(self):
        issues = self._java_issues("class Solution { int x = 1; }")
        assert any(
            i.severity == ValidationSeverity.ERROR
            and "No valid Java method definition" in i.message
            for i in issues
        )

    def test_non_camelcase_java_method_name_is_info(self):
        issues = self._java_issues(
            "class Solution { public int Solve(int[] nums) { return 0; } }"
        )
        assert any(
            i.severity == ValidationSeverity.INFO and "camelCase" in i.message
            for i in issues
        )

    def test_extract_java_method_name_returns_none_without_public_method(self):
        assert self._use_case()._extract_java_method_name("class A { int x; }") is None

    def test_python_js_name_mismatch_is_info(self, valid_question_data):
        valid_question_data["starter"]["python"] = (
            "def solve(nums: List[int]) -> List[int]:\n    pass"
        )
        valid_question_data["starter"]["javascript"] = (
            "function resolver(nums) {\n    return nums;\n}"
        )
        question = Question(**valid_question_data)
        issues = self._use_case()._check_signature_consistency(question)
        assert any(
            i.severity == ValidationSeverity.INFO
            and "solve" in i.message
            and "resolver" in i.message
            for i in issues
        )


# ============================================================================
# OutputFormatValidationUseCase Tests
# ============================================================================


class TestOutputFormatValidationUseCase:
    """Tests for output format validation use case."""

    @pytest.mark.asyncio
    async def test_valid_output_format_passes(self, valid_question):
        """Test that valid output format passes validation."""
        from app.services.question_validator import OutputFormatValidationUseCase

        use_case = OutputFormatValidationUseCase()
        result = await use_case.execute(valid_question)

        assert result.passed is True

    @pytest.mark.asyncio
    async def test_inconsistent_output_format_fails(self, valid_question_data):
        """Test that inconsistent output formats across test cases fail."""
        # Different output formats for same problem
        valid_question_data["test_cases"] = [
            {"input": "test1", "expected_output": "[1,2,3]"},  # JSON array
            {"input": "test2", "expected_output": "hello"},  # String - inconsistent!
        ]
        question = Question(**valid_question_data)

        from app.services.question_validator import OutputFormatValidationUseCase

        use_case = OutputFormatValidationUseCase()
        result = await use_case.execute(question)

        assert result.passed is False


# ============================================================================
# QuestionValidatorService Tests
# ============================================================================


class TestQuestionValidatorService:
    """Tests for the main question validator service."""

    @pytest.mark.asyncio
    async def test_valid_question_passes_all_validations(
        self, valid_question_data, mock_piston_service
    ):
        """Test that a valid question passes all validations."""
        from app.services.question_validator import QuestionValidatorService
        from app.ports.code_executor import ExecutionResult
        import json

        # Make the fixture animatable: binary-search is in the curated catalog
        # (question_catalog.QUESTION_ALGORITHMS) and its canonical input
        # "nums = [...], target = ..." maps to signature ["nums","target"].
        valid_question_data["id"] = "binary-search"
        valid_question_data["title"] = "Binary Search"
        valid_question_data["category"] = "Binary Search"
        valid_question_data["description"] = (
            "Given a sorted array nums and a target value, return the index of "
            "target using binary search or -1 if not found. This is long enough to pass."
        )
        valid_question_data["examples"] = [
            {
                "input": "nums = [2,4,7,9,13,18,21], target = 13",
                "output": "4",
                "explanation": "Target 13 found at index 4",
            }
        ]
        valid_question_data["starter"]["java"] = """
class Solution {
    public int binarySearch(int[] nums, int target) {
        return 0;
    }
}
"""
        valid_question_data["starter"]["python"] = """
from typing import List

def solve(nums: List[int], target: int) -> int:
    return 0

import sys
import json
lines = sys.stdin.read().strip().split('\\n')
nums = json.loads(lines[0])
target = json.loads(lines[1]) if len(lines) > 1 else 0
result = solve(nums, target)
print(json.dumps(result))
"""
        valid_question_data["solution"] = "binary search return mid"
        valid_question_data["test_cases"] = [
            {
                "input": "[2,4,7,9,13,18,21]\n13",
                "expected_output": "4",
                "description": "Basic test case",
                "hidden": False,
            },
            {
                "input": "[1,3,5]\n2",
                "expected_output": "-1",
                "description": "Not found",
                "hidden": True,
            },
        ]
        question = Question(**valid_question_data)

        service = QuestionValidatorService(executor=mock_piston_service)

        # Mock executor: animation trace for binary_search + normal test-case outputs
        trace = json.dumps(
            [
                {
                    "event": "init",
                    "values": [2, 4, 7, 9, 13, 18, 21],
                    "family": "array",
                },
                {"event": "pointer", "name": "low", "index": 0},
                {"event": "pointer", "name": "high", "index": 6},
                {"event": "pointer", "name": "mid", "index": 3},
                {"event": "compare", "i": 3},
                {"event": "mark", "i": 4, "state": "match"},
                {"event": "return", "result": 4},
            ]
        )

        def mock_execute_side_effect(language, code, stdin="", version=None):
            # Animation path: traced binary_search code contains the function name
            if "binary_search" in code:
                return ExecutionResult(stdout=trace, exit_code=0)
            if "[1,3,5]" in stdin or "5]" in stdin:
                return ExecutionResult(stdout="-1", exit_code=0)
            return ExecutionResult(stdout="4", exit_code=0)

        mock_piston_service.execute.side_effect = mock_execute_side_effect

        result = await service.validate_question(question)

        assert result.valid is True
        assert result.error_count == 0

    @pytest.mark.asyncio
    async def test_invalid_question_fails_validation(
        self, question_with_invalid_test_cases, mock_piston_service
    ):
        """Test that an invalid question fails validation."""
        from app.services.question_validator import QuestionValidatorService
        from app.ports.code_executor import ExecutionResult

        mock_piston_service.execute.return_value = ExecutionResult(
            stdout="", exit_code=0
        )

        service = QuestionValidatorService(executor=mock_piston_service)
        result = await service.validate_question(question_with_invalid_test_cases)

        assert result.valid is False
        assert result.error_count > 0

    @pytest.mark.asyncio
    async def test_all_use_cases_are_executed(
        self, valid_question, mock_piston_service
    ):
        """Test that all validation use cases are executed."""
        from app.services.question_validator import QuestionValidatorService
        from app.ports.code_executor import ExecutionResult

        service = QuestionValidatorService(executor=mock_piston_service)

        mock_piston_service.execute.return_value = ExecutionResult(
            stdout="result", exit_code=0
        )

        result = await service.validate_question(valid_question)

        # Check that all use cases were run
        expected_use_cases = [
            ValidationUseCase.STRUCTURE,
            ValidationUseCase.TEST_CASES,
            ValidationUseCase.STARTER_CODE,
            ValidationUseCase.SOLUTION,
            ValidationUseCase.TIME_LIMITS,
            ValidationUseCase.FUNCTION_SIGNATURE,
            ValidationUseCase.OUTPUT_FORMAT,
        ]

        for use_case in expected_use_cases:
            assert use_case in result.results

    @pytest.mark.asyncio
    async def test_validation_can_be_skipped_for_specific_use_cases(
        self, valid_question, mock_piston_service
    ):
        """Test that specific use cases can be skipped."""
        from app.services.question_validator import QuestionValidatorService
        from app.ports.code_executor import ExecutionResult

        config = QuestionValidationConfig(skip_use_cases=[ValidationUseCase.SOLUTION])

        service = QuestionValidatorService(executor=mock_piston_service, config=config)

        mock_piston_service.execute.return_value = ExecutionResult(
            stdout="result", exit_code=0
        )

        result = await service.validate_question(valid_question)

        # Solution validation should be skipped
        assert ValidationUseCase.SOLUTION not in result.results


# ============================================================================
# Integration with QuestionBank Tests
# ============================================================================


class TestQuestionBankValidationIntegration:
    """Tests for validation integration with QuestionBank."""

    @pytest.fixture
    def empty_repo(self, test_db):
        from app.repositories.sql_question_repository import SqlQuestionRepository

        return SqlQuestionRepository(test_db)

    @pytest.mark.asyncio
    async def test_invalid_question_not_loaded(
        self, question_with_invalid_test_cases, empty_repo
    ):
        """Test that invalid questions are not loaded into the question bank."""
        from app.services.question_bank import QuestionBank

        bank = QuestionBank(repository=empty_repo)

        result = await bank.add(question_with_invalid_test_cases, validate=False)

        assert result.is_validated is False

    @pytest.mark.asyncio
    async def test_validation_status_stored_with_question(
        self, valid_question, mock_piston_service, empty_repo
    ):
        """Test that validation status is stored with the question."""
        from app.services.question_bank import QuestionBank
        from app.services.question_validator import QuestionValidatorService
        from app.ports.code_executor import ExecutionResult

        validator = QuestionValidatorService(executor=mock_piston_service)
        bank = QuestionBank(repository=empty_repo, validator=validator)

        # Mock executor response for tests that execute code
        mock_piston_service.execute.return_value = ExecutionResult(
            stdout="result", exit_code=0
        )

        _result = await bank.add(valid_question, validate=True)

        statuses = await empty_repo.get_validation_statuses()
        assert valid_question.id in statuses


# ============================================================================
# API Endpoint Tests
# ============================================================================


class TestQuestionValidationAPI:
    """Tests for question validation API endpoints."""

    async def _admin_headers(self, client) -> dict:
        """Register an admin and promote it via the users table."""
        res = client.post(
            "/api/auth/register",
            json={
                "username": "unitvaladmin",
                "email": "unitvaladmin@test.com",
                "password": "testpass123",
            },
        )
        if res.status_code != 201:
            res = client.post(
                "/api/auth/login",
                json={"username": "unitvaladmin", "password": "testpass123"},
            )
        token = res.json()["access_token"]

        from tests.db_helpers import promote_to_admin

        await promote_to_admin("unitvaladmin")

        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.asyncio
    async def test_validate_endpoint_returns_validation_result(
        self, valid_question_data, test_client
    ):
        """Test that the validate endpoint returns proper validation result."""
        client = test_client
        headers = await self._admin_headers(client)

        response = client.post(
            "/api/question-validation/validate",
            json=valid_question_data,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert "results" in data

    @pytest.mark.asyncio
    async def test_validate_endpoint_rejects_unauthenticated(
        self, valid_question_data, test_client
    ):
        """Test that the validate endpoint rejects unauthenticated requests."""
        client = test_client

        response = client.post(
            "/api/question-validation/validate", json=valid_question_data
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_batch_validate_endpoint_validates_multiple_questions(
        self, valid_question_data, test_client
    ):
        """Test that batch validate endpoint can validate multiple questions."""
        client = test_client
        headers = await self._admin_headers(client)

        questions = [valid_question_data, valid_question_data.copy()]
        questions[1]["id"] = "test-question-2"

        response = client.post(
            "/api/question-validation/batch-validate",
            json=questions,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2


class TestExecutorFailureHandling:
    """Executor outages must degrade to WARNING/INFO issues, never crash.

    Regression guards for the ``except Exception`` paths in the Piston-backed
    use cases. These branches previously received coverage only when the real
    Piston endpoint happened to be unreachable in the environment, which made
    the coverage-budget gate depend on infrastructure state; pin them
    deterministically here instead.
    """

    @pytest.mark.asyncio
    async def test_starter_code_survives_executor_crash(self, valid_question):
        """A raising executor yields per-language WARNING issues, not a crash."""
        from app.services.question_validator import StarterCodeValidationUseCase
        from app.models.question_validation_schemas import ValidationSeverity
        from app.ports.code_executor import CodeExecutor

        executor = AsyncMock(spec=CodeExecutor)
        executor.execute.side_effect = RuntimeError("piston unavailable")

        use_case = StarterCodeValidationUseCase(executor=executor)
        result = await use_case.execute(valid_question)

        failures = [
            i
            for i in result.issues
            if i.severity == ValidationSeverity.WARNING
            and i.message.startswith("Failed to validate")
            and (i.field or "").startswith("starter.")
        ]
        assert failures, f"expected degraded starter issues, got {result.issues}"
        # Warnings are not errors: validation itself still 'passes'.
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_test_case_executability_survives_executor_crash(
        self, valid_question
    ):
        """A raising executor yields INFO issues per test case, not a crash."""
        from app.services.question_validator import TestCaseValidationUseCase
        from app.models.question_validation_schemas import ValidationSeverity
        from app.ports.code_executor import CodeExecutor

        executor = AsyncMock(spec=CodeExecutor)
        executor.execute.side_effect = RuntimeError("piston unavailable")

        use_case = TestCaseValidationUseCase(executor=executor)
        result = await use_case.execute(valid_question)

        degraded = [
            i
            for i in result.issues
            if i.severity == ValidationSeverity.INFO
            and i.message.startswith("Failed to validate test case")
        ]
        assert degraded, f"expected degraded testcase issues, got {result.issues}"


# ============================================================================
# Round 3: sibling validator edge coverage (output_format / starter_code /
# solution). Same recipe as Round 2's function_signature work: real behavior
# tests over every live branch; only provably-dead branches removed.
# ============================================================================


class TestOutputFormatEdgeCases:
    """Behavior coverage for OutputFormatValidationUseCase branches."""

    def _use_case(self):
        from app.services.question_validator import OutputFormatValidationUseCase

        return OutputFormatValidationUseCase()

    def test_detect_output_format_matrix(self):
        uc = self._use_case()
        assert uc._detect_output_format("[1,2,3]") == uc.FORMAT_JSON_ARRAY
        assert uc._detect_output_format('{"a": 1}') == uc.FORMAT_JSON_OBJECT
        assert uc._detect_output_format("3.14") == uc.FORMAT_NUMBER
        assert uc._detect_output_format("42") == uc.FORMAT_NUMBER
        assert uc._detect_output_format("True") == uc.FORMAT_BOOLEAN
        assert uc._detect_output_format("false") == uc.FORMAT_BOOLEAN
        assert uc._detect_output_format("hello") == uc.FORMAT_STRING
        # Looks like JSON but does not parse -> falls through to string.
        assert uc._detect_output_format("[1,2,") == uc.FORMAT_STRING
        assert uc._detect_output_format("{oops}") == uc.FORMAT_STRING

    def test_are_formats_compatible_matrix(self):
        uc = self._use_case()
        assert uc._are_formats_compatible(uc.FORMAT_NUMBER, uc.FORMAT_NUMBER) is True
        assert uc._are_formats_compatible(uc.FORMAT_NUMBER, uc.FORMAT_STRING) is True
        assert uc._are_formats_compatible(uc.FORMAT_BOOLEAN, uc.FORMAT_STRING) is True
        assert uc._are_formats_compatible(uc.FORMAT_BOOLEAN, uc.FORMAT_NUMBER) is False
        assert (
            uc._are_formats_compatible(uc.FORMAT_JSON_ARRAY, uc.FORMAT_JSON_OBJECT)
            is False
        )
        assert (
            uc._are_formats_compatible(uc.FORMAT_JSON_ARRAY, uc.FORMAT_NUMBER) is False
        )

    @pytest.mark.asyncio
    async def test_no_test_cases_is_error(self, valid_question_data):
        valid_question_data["test_cases"] = []
        question = Question(**valid_question_data)
        result = await self._use_case().execute(question)
        assert result.passed is False
        assert any("No test cases" in i.message for i in result.issues)

    @pytest.mark.asyncio
    async def test_json_array_and_object_mix_is_error(self, valid_question_data):
        valid_question_data["test_cases"] = [
            {"input": "a", "expected_output": "[1,2]"},
            {"input": "b", "expected_output": '{"x": 1}'},
        ]
        question = Question(**valid_question_data)
        result = await self._use_case().execute(question)
        assert result.passed is False
        assert any("arrays and objects" in i.message for i in result.issues)

    @pytest.mark.asyncio
    async def test_json_and_primitive_mix_is_error(self, valid_question_data):
        valid_question_data["test_cases"] = [
            {"input": "a", "expected_output": "[1,2]"},
            {"input": "b", "expected_output": "42"},
        ]
        question = Question(**valid_question_data)
        result = await self._use_case().execute(question)
        assert result.passed is False
        assert any("primitive types" in i.message for i in result.issues)

    @pytest.mark.asyncio
    async def test_minor_inconsistency_is_warning_only(self, valid_question_data):
        # number vs string: distinct formats, no JSON involved -> WARNING.
        valid_question_data["test_cases"] = [
            {"input": "a", "expected_output": "42"},
            {"input": "b", "expected_output": "hello"},
        ]
        question = Question(**valid_question_data)
        result = await self._use_case().execute(question)
        assert result.passed is True
        assert any(
            i.severity == ValidationSeverity.WARNING
            and "Minor output format inconsistency" in i.message
            for i in result.issues
        )

    def test_single_output_branches(self):
        from app.models.question_validation_schemas import ValidationSeverity

        uc = self._use_case()
        # Empty output -> WARNING.
        issues = uc._validate_single_output("   ", 0)
        assert any(i.severity == ValidationSeverity.WARNING for i in issues)
        # Empty array -> INFO nudge.
        issues = uc._validate_single_output("[]", 0)
        assert any(
            i.severity == ValidationSeverity.INFO and "empty array" in i.message
            for i in issues
        )
        # Mixed element types -> WARNING.
        issues = uc._validate_single_output('[1, "a"]', 0)
        assert any("mixed element types" in i.message for i in issues)
        # Homogeneous array -> no issues.
        assert uc._validate_single_output("[1, 2]", 0) == []
        # Invalid JSON -> ERROR.
        issues = uc._validate_single_output("[1,", 0)
        assert any(i.severity == ValidationSeverity.ERROR for i in issues)
        # Uppercase boolean -> INFO lowercase nudge.
        issues = uc._validate_single_output("True", 0)
        assert any(
            i.severity == ValidationSeverity.INFO and "lowercase" in i.message
            for i in issues
        )
        assert uc._validate_single_output("true", 0) == []

    def test_examples_consistency_branches(self, valid_question_data):
        from app.models.question_validation_schemas import ValidationSeverity

        uc = self._use_case()
        # No examples -> no issues.
        valid_question_data["examples"] = []
        question = Question(**valid_question_data)
        assert uc._check_examples_consistency(question) == []
        # Compatible example format (number test-case vs string example)
        # -> INFO; incompatible (array test-case vs number example) -> WARNING.
        valid_question_data["test_cases"] = [{"input": "a", "expected_output": "42"}]
        valid_question_data["examples"] = [
            {"input": "a", "output": "hello", "explanation": "e"},
            {"input": "b", "output": "hello", "explanation": "e"},
        ]
        question = Question(**valid_question_data)
        issues = uc._check_examples_consistency(question)
        assert any(
            i.severity == ValidationSeverity.INFO and "differs" in i.message
            for i in issues
        )
        valid_question_data["test_cases"] = [{"input": "a", "expected_output": "[1]"}]
        valid_question_data["examples"] = [
            {"input": "a", "output": "42", "explanation": "e"},
        ]
        question = Question(**valid_question_data)
        issues = uc._check_examples_consistency(question)
        assert any(
            i.severity == ValidationSeverity.WARNING and "incompatible" in i.message
            for i in issues
        )
        # Examples present but no test cases -> no issues.
        valid_question_data["test_cases"] = []
        question = Question(**valid_question_data)
        assert uc._check_examples_consistency(question) == []


class TestStarterCodeEdgeCases:
    """Behavior coverage for StarterCodeValidationUseCase branches."""

    def _use_case(self, executor=None):
        from app.services.question_validator import StarterCodeValidationUseCase

        return StarterCodeValidationUseCase(executor=executor)

    def test_escape_code_handles_backslash_and_triple_quote(self):
        uc = self._use_case()
        assert uc._escape_code('a\\b """c"""') == 'a\\\\b \\"\\"\\"c\\"\\"\\"'

    def test_parse_error_message_branches(self):
        uc = self._use_case()
        assert uc._parse_error_message("python", "") == "Unknown error"
        assert (
            uc._parse_error_message("python", "  SyntaxError: bad\nnote line\n")
            == "SyntaxError: bad"
        )
        # No error keyword -> first non-empty line.
        assert uc._parse_error_message("python", "boom\nsecond") == "boom"
        # Blank stderr -> over-long tail branch.
        long_blank = "\n" * 300
        assert uc._parse_error_message("python", long_blank) == long_blank[:200]
        short_blank = "  \n "
        assert uc._parse_error_message("python", short_blank) == short_blank

    def test_create_syntax_test_code_per_language(self):
        uc = self._use_case()
        assert "compile(" in uc._create_syntax_test_code("python", "x = 1")
        js = uc._create_syntax_test_code("javascript", "var x = 1;")
        assert js.startswith("var x = 1;") and "Syntax OK" in js
        assert uc._create_syntax_test_code("java", "class A {}") == "class A {}"
        assert uc._create_syntax_test_code("ruby", "puts 1") == "puts 1"

    def test_basic_validate_dispatch(self):
        uc = self._use_case()
        assert uc._basic_validate("python", "def f():\n    pass") == []
        assert uc._basic_validate("javascript", "function f() {}") == []
        assert uc._basic_validate("java", "class A {}") == []
        assert uc._basic_validate("ruby", "puts 1") == []

    def test_basic_python_flags_unbalanced_and_missing_colon(self):
        from app.models.question_validation_schemas import ValidationSeverity

        uc = self._use_case()
        issues = uc._basic_python_validate("def f((x):\n    pass")
        assert any(
            "Unbalanced" in i.message and i.severity == ValidationSeverity.WARNING
            for i in issues
        )
        issues = uc._basic_python_validate("def f(x)\n    pass")
        assert any(
            "missing colon" in i.message and i.severity == ValidationSeverity.ERROR
            for i in issues
        )

    def test_basic_javascript_flags_unbalanced(self):
        uc = self._use_case()
        issues = uc._basic_javascript_validate("function f( {")
        assert any("Unbalanced" in i.message for i in issues)
        assert uc._basic_javascript_validate("function f() {}") == []

    def test_basic_java_flags_missing_class_and_braces(self):
        from app.models.question_validation_schemas import ValidationSeverity

        uc = self._use_case()
        issues = uc._basic_java_validate("public void solve() {}")
        assert any(
            "class definition" in i.message and i.severity == ValidationSeverity.WARNING
            for i in issues
        )
        issues = uc._basic_java_validate("class A { void m() {")
        assert any("Unbalanced braces" in i.message for i in issues)

    @pytest.mark.asyncio
    async def test_missing_language_is_error(self, valid_question_data):
        valid_question_data["starter"]["java"] = ""
        question = Question(**valid_question_data)
        result = await self._use_case().execute(question)
        assert result.passed is False
        assert any(
            i.field == "starter.java" and "missing" in i.message for i in result.issues
        )

    @pytest.mark.asyncio
    async def test_basic_path_flags_bad_python_without_executor(
        self, valid_question_data
    ):
        valid_question_data["starter"]["python"] = "def f((x):\n    pass"
        question = Question(**valid_question_data)
        result = await self._use_case().execute(question)
        assert any(
            i.language == "python" and "Unbalanced" in i.message for i in result.issues
        )

    @pytest.mark.asyncio
    async def test_executor_syntax_error_reports_stderr(self, valid_question):
        from app.ports.code_executor import CodeExecutor, ExecutionResult

        executor = AsyncMock(spec=CodeExecutor)
        executor.execute.return_value = ExecutionResult(
            exit_code=1, stderr="file.py line 3\nSyntaxError: bad indent"
        )
        result = await self._use_case(executor).execute(valid_question)
        assert result.passed is False
        assert any(
            "Syntax error in python" in i.message and "bad indent" in i.message
            for i in result.issues
        )


class TestSolutionEdgeCases:
    """Behavior coverage for SolutionValidationUseCase branches."""

    def _use_case(self, executor=None):
        from app.services.question_validator import SolutionValidationUseCase

        return SolutionValidationUseCase(executor=executor)

    def test_compare_outputs_matrix(self):
        uc = self._use_case()
        assert uc._compare_outputs("42", "42") is True
        assert uc._compare_outputs("42\n", "42") is True
        assert uc._compare_outputs("[1, 2]", "[1,2]") is True
        assert uc._compare_outputs("42.0", "42") is True
        assert uc._compare_outputs("True", "true") is True
        assert uc._compare_outputs("True", "False") is False
        assert uc._compare_outputs("abc", "def") is False

    def test_create_executable_solution_branches(self, valid_question_data):
        uc = self._use_case()
        # Interactive questions run the solution body as-is.
        valid_question_data["is_interactive"] = True
        valid_question_data["solution"] = "print('hi')"
        question = Question(**valid_question_data)
        assert uc._create_executable_solution(question) == "print('hi')"
        # Interactive without a solution body -> None.
        valid_question_data["solution"] = None
        question = Question(**valid_question_data)
        assert uc._create_executable_solution(question) is None
        # Non-interactive without a def -> None.
        valid_question_data["is_interactive"] = False
        valid_question_data["starter"]["python"] = "x = 1"
        question = Question(**valid_question_data)
        assert uc._create_executable_solution(question) is None
        # Pass-only stub -> None (nothing executable to validate).
        valid_question_data["starter"]["python"] = "def solve(nums):\n    pass"
        question = Question(**valid_question_data)
        assert uc._create_executable_solution(question) is None
        # Stub with a return -> runnable runner embedding the function.
        valid_question_data["starter"]["python"] = "def solve(nums):\n    return nums"
        question = Question(**valid_question_data)
        runner = uc._create_executable_solution(question)
        assert runner is not None and "solve" in runner

    @pytest.mark.asyncio
    async def test_no_executor_is_warning_not_error(self, valid_question):
        from app.models.question_validation_schemas import ValidationSeverity

        result = await self._use_case().execute(valid_question)
        assert result.passed is True
        assert any(
            i.severity == ValidationSeverity.WARNING and "without Piston" in i.message
            for i in result.issues
        )

    @pytest.mark.asyncio
    async def test_executor_failure_and_mismatch_reported(
        self, valid_question_data, mock_piston_service
    ):
        from app.ports.code_executor import ExecutionResult

        valid_question_data["starter"]["python"] = "def solve(nums):\n    return nums"
        valid_question_data["test_cases"] = [
            {"input": "[1]", "expected_output": "[1]"},
            {"input": "[2]", "expected_output": "[2]"},
        ]
        question = Question(**valid_question_data)
        mock_piston_service.execute.side_effect = [
            ExecutionResult(stdout="[9]", exit_code=0),
            ExecutionResult(stdout="", stderr="boom", exit_code=1),
        ]
        result = await self._use_case(mock_piston_service).execute(question)
        assert result.passed is False
        assert any("mismatch" in i.message for i in result.issues)
        assert any("failed on test case 2" in i.message for i in result.issues)
        assert any("only passed 0/2" in i.message for i in result.issues)

    @pytest.mark.asyncio
    async def test_executor_exception_degrades_to_issue(
        self, valid_question_data, mock_piston_service
    ):
        valid_question_data["starter"]["python"] = "def solve(nums):\n    return nums"
        valid_question_data["test_cases"] = [
            {"input": "[1]", "expected_output": "[1]"},
        ]
        question = Question(**valid_question_data)
        mock_piston_service.execute.side_effect = RuntimeError("piston down")
        result = await self._use_case(mock_piston_service).execute(question)
        assert any("Failed to execute solution" in i.message for i in result.issues)

    @pytest.mark.asyncio
    async def test_no_test_cases_passes_without_summary(
        self, valid_question_data, mock_piston_service
    ):
        valid_question_data["starter"]["python"] = "def solve(nums):\n    return nums"
        valid_question_data["test_cases"] = []
        question = Question(**valid_question_data)
        result = await self._use_case(mock_piston_service).execute(question)
        assert result.passed is True
        assert result.issues == []
        mock_piston_service.execute.assert_not_called()


# ============================================================================
# Round 4: solution-vs-starter attribution probe
# (solution.py:_create_executable_solution latent-bug investigation).
# The reference solution lives in ``question.solution``; the starter template
# lives in ``question.starter.python``. These probes pin which artifact the
# SOLUTION use case actually executes.
# ============================================================================


class TestSolutionAttributionRound4:
    """Failing-test probe: runner must come from the reference solution."""

    def _use_case(self, executor=None):
        from app.services.question_validator import SolutionValidationUseCase

        return SolutionValidationUseCase(executor=executor)

    def test_executable_reference_solution_beats_pass_stub(self, valid_question_data):
        """A working reference solution + pass-only starter must be runnable.

        Before the fix this returns None ("Could not create executable
        solution") even though an executable reference solution exists.
        """
        valid_question_data["solution"] = "def solve(nums):\n    return nums"
        valid_question_data["starter"]["python"] = "def solve(nums):\n    pass"
        question = Question(**valid_question_data)
        runner = self._use_case()._create_executable_solution(question)
        assert runner is not None
        assert "return nums" in runner

    @pytest.mark.asyncio
    async def test_wrong_reference_not_masked_by_starter(
        self, valid_question_data, mock_piston_service
    ):
        """The executor must receive the reference solution, not the starter.

        Wrong reference + correct starter: before the fix the starter body is
        executed and attributed to the solution (false pass); the executed
        code must contain the reference body instead.
        """
        from app.ports.code_executor import ExecutionResult

        valid_question_data["solution"] = "def solve(nums):\n    return ['WRONG']"
        valid_question_data["starter"]["python"] = "def solve(nums):\n    return nums"
        valid_question_data["test_cases"] = [
            {"input": "[1]", "expected_output": "[1]"},
        ]
        question = Question(**valid_question_data)
        mock_piston_service.execute.return_value = ExecutionResult(
            stdout="['WRONG']", exit_code=0
        )
        result = await self._use_case(mock_piston_service).execute(question)
        sent_code = mock_piston_service.execute.call_args.kwargs["code"]
        assert "WRONG" in sent_code
        assert result.passed is False
        assert any("mismatch" in i.message for i in result.issues)

    @pytest.mark.asyncio
    async def test_correct_reference_with_stub_starter_passes(
        self, valid_question_data, mock_piston_service
    ):
        """End to end: correct reference + stub starter must pass validation.

        Before the fix this reports ERROR ("Could not create executable
        solution from reference solution") on real-shaped data.
        """
        from app.ports.code_executor import ExecutionResult

        valid_question_data["solution"] = "def solve(nums):\n    return nums"
        valid_question_data["starter"]["python"] = "def solve(nums):\n    pass"
        valid_question_data["test_cases"] = [
            {"input": "[1,2,3]", "expected_output": "[1,2,3]"},
        ]
        question = Question(**valid_question_data)
        mock_piston_service.execute.return_value = ExecutionResult(
            stdout="[1,2,3]", exit_code=0
        )
        result = await self._use_case(mock_piston_service).execute(question)
        assert result.passed is True


# ============================================================================
# Round 4: time_limits.py coverage rot (same recipe as Rounds 2-3: real
# behavior tests over live branches; only provably-dead branches removed).
# ============================================================================


class TestTimeLimitsCoverageRound4:
    """Behavior coverage for TimeLimitValidationUseCase branches."""

    def _use_case(self):
        from app.services.question_validator import TimeLimitValidationUseCase

        return TimeLimitValidationUseCase()

    @pytest.mark.asyncio
    async def test_non_standard_notation_is_warning_only(self, valid_question_data):
        from app.models.question_validation_schemas import ValidationSeverity

        valid_question_data["time_complexity"] = "linear"
        question = Question(**valid_question_data)
        result = await self._use_case().execute(question)
        assert result.passed is True
        assert any(
            i.severity == ValidationSeverity.WARNING
            and "standard Big O notation" in i.message
            for i in result.issues
        )

    @pytest.mark.asyncio
    async def test_exponential_blows_time_budget(self, valid_question_data):
        from app.models.question_validation_schemas import ValidationSeverity

        valid_question_data["time_complexity"] = "O(2^n)"
        valid_question_data["constraints"] = ["n <= 40"]
        question = Question(**valid_question_data)
        result = await self._use_case().execute(question)
        assert any(
            i.severity == ValidationSeverity.WARNING
            and "may exceed time limit" in i.message
            and i.details["estimated_operations"] == 2**30
            for i in result.issues
        )

    @pytest.mark.asyncio
    async def test_ten_power_constraint_parses_input_size(self, valid_question_data):
        from app.models.question_validation_schemas import ValidationSeverity

        valid_question_data["time_complexity"] = "O(n^2)"
        valid_question_data["constraints"] = ["input size up to 10^5"]
        question = Question(**valid_question_data)
        result = await self._use_case().execute(question)
        assert any(
            i.severity == ValidationSeverity.WARNING
            and "may exceed time limit" in i.message
            and i.details["max_input_size"] == 100000
            for i in result.issues
        )

    @pytest.mark.asyncio
    async def test_unmatched_constraints_skip_operation_estimate(
        self, valid_question_data
    ):
        valid_question_data["time_complexity"] = "O(n)"
        valid_question_data["constraints"] = ["Be kind to newcomers"]
        question = Question(**valid_question_data)
        uc = self._use_case()
        assert uc._validate_constraints_for_time(question) == []
        result = await uc.execute(question)
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_missing_time_complexity_is_warning_only(self, valid_question_data):
        from app.models.question_validation_schemas import ValidationSeverity

        valid_question_data["time_complexity"] = None
        question = Question(**valid_question_data)
        result = await self._use_case().execute(question)
        assert result.passed is True
        assert any(
            i.severity == ValidationSeverity.WARNING
            and "should be specified" in i.message
            for i in result.issues
        )

    def test_empty_thresholds_yield_no_issues(self, valid_question_data):
        # Defensive `if thresholds:` false path: unknown difficulty config
        # degrades to no threshold issues instead of crashing.
        uc = self._use_case()
        uc.COMPLEXITY_THRESHOLDS = {}
        question = Question(**valid_question_data)
        assert uc._validate_time_complexity(question) == []


# ============================================================================
# Round 5: SOLUTION non-executable reference is WARNING, not ERROR.
# Real-bank shape (prose solution + pass-only stub) yields no runnable
# artifact; flagging the whole bank with ERROR for that is noise. Genuinely
# executable references that fail cases must STILL be ERROR.
# ============================================================================


class TestSolutionNonExecutableWarningRound5:
    """Non-executable reference -> WARNING; bad executable -> ERROR."""

    def _use_case(self, executor=None):
        from app.services.question_validator import SolutionValidationUseCase

        return SolutionValidationUseCase(executor=executor)

    @pytest.mark.asyncio
    async def test_prose_solution_with_stub_starter_is_warning_not_error(
        self, valid_question_data, mock_piston_service
    ):
        valid_question_data["solution"] = "Return the array as is."
        valid_question_data["starter"]["python"] = "def solve(nums):\n    pass"
        question = Question(**valid_question_data)
        assert self._use_case()._create_executable_solution(question) is None
        result = await self._use_case(mock_piston_service).execute(question)
        assert result.passed is True
        assert len(result.issues) == 1
        issue = result.issues[0]
        assert issue.use_case == ValidationUseCase.SOLUTION
        assert issue.severity == ValidationSeverity.WARNING
        assert (
            issue.message
            == "Could not create executable solution from reference solution"
        )
        assert issue.field == "solution"
        mock_piston_service.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_bad_executable_reference_is_still_error(
        self, valid_question_data, mock_piston_service
    ):
        from app.ports.code_executor import ExecutionResult

        valid_question_data["solution"] = "def solve(nums):\n    return []"
        valid_question_data["test_cases"] = [
            {"input": "[1]", "expected_output": "[1]"},
        ]
        question = Question(**valid_question_data)
        mock_piston_service.execute.return_value = ExecutionResult(
            stdout="[]", exit_code=0
        )
        result = await self._use_case(mock_piston_service).execute(question)
        assert result.passed is False
        assert any(
            i.severity == ValidationSeverity.ERROR and "mismatch" in i.message
            for i in result.issues
        )

    @pytest.mark.asyncio
    async def test_good_executable_reference_passes_clean(
        self, valid_question_data, mock_piston_service
    ):
        from app.ports.code_executor import ExecutionResult

        valid_question_data["solution"] = "def solve(nums):\n    return nums"
        valid_question_data["starter"]["python"] = "def solve(nums):\n    pass"
        valid_question_data["test_cases"] = [
            {"input": "[1,2,3]", "expected_output": "[1,2,3]"},
        ]
        question = Question(**valid_question_data)
        mock_piston_service.execute.return_value = ExecutionResult(
            stdout="[1,2,3]", exit_code=0
        )
        result = await self._use_case(mock_piston_service).execute(question)
        assert result.passed is True
        assert result.issues == []


# ============================================================================
# Round 5: COMPLEXITY_THRESHOLDS dead-config probe.
# `warning_complexity` keys are defined but never read — only
# `max_complexity` drives `_validate_time_complexity`, and every breach is a
# single-tier WARNING. These tests pin the removal + the surviving boundary.
# ============================================================================


class TestComplexityThresholdsRound5:
    """Dead warning_complexity keys are gone; max_complexity boundary holds."""

    def _use_case(self):
        from app.services.question_validator import TimeLimitValidationUseCase

        return TimeLimitValidationUseCase()

    def test_no_dead_warning_complexity_keys(self):
        uc = self._use_case()
        assert uc.COMPLEXITY_THRESHOLDS != {}
        for difficulty, thresholds in uc.COMPLEXITY_THRESHOLDS.items():
            assert "warning_complexity" not in thresholds, difficulty
            assert "max_complexity" in thresholds, difficulty

    @pytest.mark.asyncio
    async def test_medium_boundary_pins_max_only_semantics(self, valid_question_data):
        from app.models.schemas import Difficulty

        # At max (O(n log n) for medium): no threshold warning.
        valid_question_data["difficulty"] = Difficulty.MEDIUM
        valid_question_data["time_complexity"] = "O(n log n)"
        question = Question(**valid_question_data)
        result = await self._use_case().execute(question)
        assert not any("may be too high" in i.message for i in result.issues)
        # Above max (O(n^2) for medium): WARNING, never ERROR.
        valid_question_data["time_complexity"] = "O(n^2)"
        question = Question(**valid_question_data)
        result = await self._use_case().execute(question)
        assert any(
            i.severity == ValidationSeverity.WARNING and "may be too high" in i.message
            for i in result.issues
        )
        assert result.passed is True


# ============================================================================
# Round 5: starter-fallback contract pin.
# `_create_executable_solution` prefers the reference solution and falls back
# to the starter only when the solution carries no executable function.
# Behavior is correct post-Round-4; these tests lock the contract so future
# changes cannot silently misattribute again.
# ============================================================================


class TestStarterFallbackContractRound5:
    """Pin when the fallback fires, what it executes, and its label."""

    def _use_case(self, executor=None):
        from app.services.question_validator import SolutionValidationUseCase

        return SolutionValidationUseCase(executor=executor)

    def test_prose_solution_plus_stub_starter_yields_none(self, valid_question_data):
        # Exact real-bank shape: nothing executable anywhere -> None.
        valid_question_data["solution"] = "Return the array as is."
        valid_question_data["starter"]["python"] = "def solve(nums):\n    pass"
        question = Question(**valid_question_data)
        assert self._use_case()._create_executable_solution(question) is None

    def test_fallback_fires_only_for_prose_solution(self, valid_question_data):
        # Prose solution + executable starter -> runner embeds the STARTER.
        valid_question_data["solution"] = "Two-pointer prose explanation."
        valid_question_data["starter"]["python"] = (
            "def solve(nums):\n    return ['STARTER']"
        )
        question = Question(**valid_question_data)
        runner = self._use_case()._create_executable_solution(question)
        assert runner is not None
        assert "STARTER" in runner

    def test_executable_solution_shadows_executable_starter(self, valid_question_data):
        # Both executable -> the REFERENCE wins; starter body never embedded.
        valid_question_data["solution"] = "def solve(nums):\n    return ['REF']"
        valid_question_data["starter"]["python"] = (
            "def solve(nums):\n    return ['STARTER']"
        )
        question = Question(**valid_question_data)
        runner = self._use_case()._create_executable_solution(question)
        assert runner is not None
        assert "REF" in runner
        assert "STARTER" not in runner

    def test_pass_only_solution_defers_to_executable_starter(self, valid_question_data):
        # A def with a bare pass (no return) is not executable -> defer.
        valid_question_data["solution"] = "def solve(nums):\n    pass"
        valid_question_data["starter"]["python"] = (
            "def solve(nums):\n    return ['STARTER']"
        )
        question = Question(**valid_question_data)
        runner = self._use_case()._create_executable_solution(question)
        assert runner is not None
        assert "STARTER" in runner

    @pytest.mark.asyncio
    async def test_fallback_execution_attributed_to_solution_use_case(
        self, valid_question_data, mock_piston_service
    ):
        # Fallback-executed code failing cases is still ERROR, labeled SOLUTION.
        from app.ports.code_executor import ExecutionResult

        valid_question_data["solution"] = "Two-pointer prose explanation."
        valid_question_data["starter"]["python"] = (
            "def solve(nums):\n    return ['STARTER']"
        )
        valid_question_data["test_cases"] = [
            {"input": "[1]", "expected_output": "[1]"},
        ]
        question = Question(**valid_question_data)
        mock_piston_service.execute.return_value = ExecutionResult(
            stdout="['STARTER']", exit_code=0
        )
        result = await self._use_case(mock_piston_service).execute(question)
        sent_code = mock_piston_service.execute.call_args.kwargs["code"]
        assert "STARTER" in sent_code
        assert result.passed is False
        assert any(
            i.use_case == ValidationUseCase.SOLUTION
            and i.severity == ValidationSeverity.ERROR
            for i in result.issues
        )


# ============================================================================
# Round 6: starter-fallback attribution note.
# When the reference solution is prose and the executed artifact came from
# the starter fallback, per-test-case SOLUTION ERRORs must say so instead
# of reading as if the reference itself failed. No exact-text consumer
# exists for these messages (repo-wide grep: only solution.py emits them;
# tests match substrings), so clarifying the text is safe.
# ============================================================================


class TestStarterFallbackAttributionRound6:
    """Fallback failures carry a starter-fallback note; reference failures don't."""

    def _use_case(self, executor=None):
        from app.services.question_validator import SolutionValidationUseCase

        return SolutionValidationUseCase(executor=executor)

    @pytest.mark.asyncio
    async def test_fallback_exit_failure_notes_starter_fallback(
        self, valid_question_data, mock_piston_service
    ):
        from app.ports.code_executor import ExecutionResult

        valid_question_data["solution"] = "Two-pointer prose explanation."
        valid_question_data["starter"]["python"] = (
            "def solve(nums):\n    raise ValueError('boom')"
        )
        valid_question_data["test_cases"] = [
            {"input": "[1]", "expected_output": "[1]"},
        ]
        question = Question(**valid_question_data)
        mock_piston_service.execute.return_value = ExecutionResult(
            stdout="", stderr="ValueError: boom", exit_code=1
        )
        result = await self._use_case(mock_piston_service).execute(question)
        assert result.passed is False
        failures = [
            i
            for i in result.issues
            if i.use_case == ValidationUseCase.SOLUTION
            and i.severity == ValidationSeverity.ERROR
            and "failed on test case" in i.message
        ]
        assert len(failures) == 1
        assert "starter" in failures[0].message.lower()

    @pytest.mark.asyncio
    async def test_fallback_mismatch_notes_starter_fallback(
        self, valid_question_data, mock_piston_service
    ):
        from app.ports.code_executor import ExecutionResult

        valid_question_data["solution"] = "Two-pointer prose explanation."
        valid_question_data["starter"]["python"] = (
            "def solve(nums):\n    return ['STARTER']"
        )
        valid_question_data["test_cases"] = [
            {"input": "[1]", "expected_output": "[1]"},
        ]
        question = Question(**valid_question_data)
        mock_piston_service.execute.return_value = ExecutionResult(
            stdout="['STARTER']", exit_code=0
        )
        result = await self._use_case(mock_piston_service).execute(question)
        assert result.passed is False
        mismatches = [
            i
            for i in result.issues
            if i.use_case == ValidationUseCase.SOLUTION
            and i.severity == ValidationSeverity.ERROR
            and "mismatch" in i.message
        ]
        assert len(mismatches) == 1
        assert "starter" in mismatches[0].message.lower()

    @pytest.mark.asyncio
    async def test_reference_failure_carries_no_fallback_note(
        self, valid_question_data, mock_piston_service
    ):
        from app.ports.code_executor import ExecutionResult

        valid_question_data["solution"] = "def solve(nums):\n    return []"
        valid_question_data["starter"]["python"] = (
            "def solve(nums):\n    return ['STARTER']"
        )
        valid_question_data["test_cases"] = [
            {"input": "[1]", "expected_output": "[1]"},
        ]
        question = Question(**valid_question_data)
        mock_piston_service.execute.return_value = ExecutionResult(
            stdout="[]", exit_code=0
        )
        result = await self._use_case(mock_piston_service).execute(question)
        assert result.passed is False
        errors = [
            i
            for i in result.issues
            if i.use_case == ValidationUseCase.SOLUTION
            and i.severity == ValidationSeverity.ERROR
        ]
        assert errors != []
        assert all("starter" not in i.message.lower() for i in errors)

    def test_executable_candidate_rejects_empty(self):
        uc = self._use_case()
        assert uc._executable_candidate("") is False
        assert uc._executable_candidate(None) is False

    def test_no_fallback_for_interactive(self, valid_question_data):
        valid_question_data["is_interactive"] = True
        valid_question_data["solution"] = "print('hi')"
        question = Question(**valid_question_data)
        assert self._use_case()._used_starter_fallback(question) is False

    def test_empty_starter_yields_no_executable(self, valid_question_data):
        valid_question_data["solution"] = "Prose only."
        valid_question_data["starter"]["python"] = ""
        question = Question(**valid_question_data)
        assert self._use_case()._create_executable_solution(question) is None
        assert self._use_case()._used_starter_fallback(question) is False

    def test_non_model_starter_never_fallback(self, valid_question_data):
        valid_question_data["solution"] = "Prose only."
        valid_question_data["starter"] = "just text"
        question = Question(**valid_question_data)
        assert self._use_case()._used_starter_fallback(question) is False
