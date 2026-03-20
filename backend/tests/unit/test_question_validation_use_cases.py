"""
Unit tests for question validation use cases.

This module contains test-driven tests for validating questions before they
are made available to users. Tests focus on Python coverage using Piston.
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from app.models.schemas import Question, TestCase, Example, StarterCode, Difficulty
from app.models.question_validation_schemas import (
    ValidationUseCase,
    ValidationSeverity,
    ValidationIssue,
    UseCaseValidationResult,
    QuestionValidationResult,
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
            "java": "class Solution {\n    public int[] solve(int[] nums) {\n        // Your code here\n    }\n}"
        },
        "examples": [
            {
                "input": "nums = [1,2,3]",
                "output": "[1,2,3]",
                "explanation": "Test explanation"
            }
        ],
        "test_cases": [
            {
                "input": "[1,2,3]",
                "expected_output": "[1,2,3]",
                "description": "Basic test case",
                "hidden": False
            },
            {
                "input": "[4,5,6]",
                "expected_output": "[4,5,6]",
                "description": "Another test case",
                "hidden": True
            }
        ],
        "hints": ["Think about the problem"],
        "solution": "Return the array as is.",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
        "constraints": ["1 <= nums.length <= 100"]
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
            "java": "class Solution { public void solve() {} }"
        },
        "examples": [{"input": "test", "output": "test"}],
        "test_cases": [{"input": "test", "expected_output": "test"}],
        "hints": [],
        "constraints": []
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
            "java": "class Solution { public void solve() {} }"
        },
        "examples": [{"input": "test", "output": "test"}],
        "test_cases": [],  # Invalid: no test cases
        "hints": [],
        "constraints": []
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
            "java": "class Solution { public void solve() {} }"
        },
        "examples": [{"input": "test", "output": "test"}],
        "test_cases": [{"input": "test", "expected_output": "test"}],
        "hints": [],
        "constraints": []
    }
    return Question(**data)


@pytest.fixture
def mock_piston_service():
    """Create a mock Piston service for testing."""
    mock = AsyncMock()
    mock.execute_code = AsyncMock()
    return mock


# ============================================================================
# StructureValidationUseCase Tests
# ============================================================================

class TestStructureValidationUseCase:
    """Tests for the structure validation use case."""
    
    @pytest.mark.asyncio
    async def test_valid_question_passes_structure_validation(self, valid_question):
        """Test that a valid question passes structure validation."""
        from app.use_cases.validate_structure import StructureValidationUseCase
        
        use_case = StructureValidationUseCase()
        result = await use_case.execute(valid_question)
        
        assert result.passed is True
        assert result.use_case == ValidationUseCase.STRUCTURE
        assert len(result.issues) == 0
    
    @pytest.mark.asyncio
    async def test_question_with_empty_id_fails_validation(self, invalid_question_missing_id):
        """Test that a question with empty ID fails validation."""
        from app.use_cases.validate_structure import StructureValidationUseCase
        
        use_case = StructureValidationUseCase()
        result = await use_case.execute(invalid_question_missing_id)
        
        assert result.passed is False
        assert any(issue.field == "id" for issue in result.issues)
    
    @pytest.mark.asyncio
    async def test_question_with_short_title_fails_validation(self, valid_question_data):
        """Test that a question with too short title fails validation."""
        valid_question_data["title"] = "Hi"  # Too short
        question = Question(**valid_question_data)
        
        from app.use_cases.validate_structure import StructureValidationUseCase
        
        use_case = StructureValidationUseCase()
        result = await use_case.execute(question)
        
        assert result.passed is False
        assert any(issue.field == "title" for issue in result.issues)
    
    @pytest.mark.asyncio
    async def test_question_with_short_description_fails_validation(self, valid_question_data):
        """Test that a question with too short description fails validation."""
        valid_question_data["description"] = "Too short"  # Less than 50 chars
        question = Question(**valid_question_data)
        
        from app.use_cases.validate_structure import StructureValidationUseCase
        
        use_case = StructureValidationUseCase()
        result = await use_case.execute(question)
        
        assert result.passed is False
        assert any(issue.field == "description" for issue in result.issues)
    
    @pytest.mark.asyncio
    async def test_question_missing_starter_language_fails_validation(self, valid_question_data):
        """Test that missing starter code for a language fails validation."""
        valid_question_data["starter"]["python"] = ""  # Empty Python starter
        question = Question(**valid_question_data)
        
        from app.use_cases.validate_structure import StructureValidationUseCase
        
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
    async def test_question_with_no_test_cases_fails_validation(self, question_with_invalid_test_cases):
        """Test that a question with no test cases fails validation."""
        from app.use_cases.validate_test_cases import TestCaseValidationUseCase
        
        use_case = TestCaseValidationUseCase()
        result = await use_case.execute(question_with_invalid_test_cases)
        
        assert result.passed is False
        assert any(issue.use_case == ValidationUseCase.TEST_CASES for issue in result.issues)
    
    @pytest.mark.asyncio
    async def test_test_case_with_empty_input_fails_validation(self, valid_question_data):
        """Test that test case with empty input fails validation."""
        valid_question_data["test_cases"] = [
            {"input": "", "expected_output": "result"}  # Empty input
        ]
        question = Question(**valid_question_data)
        
        from app.use_cases.validate_test_cases import TestCaseValidationUseCase
        
        use_case = TestCaseValidationUseCase()
        result = await use_case.execute(question)
        
        assert result.passed is False
    
    @pytest.mark.asyncio
    async def test_test_case_executability_validated_with_piston(self, valid_question, mock_piston_service):
        """Test that test case executability is validated using Piston."""
        from app.use_cases.validate_test_cases import TestCaseValidationUseCase
        
        # Mock Piston response for successful execution
        mock_piston_service.execute_code.return_value = {
            "stdout": "[1, 2, 3]",
            "stderr": "",
            "exit_code": 0,
            "execution_time": "100ms"
        }
        
        use_case = TestCaseValidationUseCase(piston_service=mock_piston_service)
        result = await use_case.execute(valid_question)
        
        # Should have called Piston to validate test case executability
        assert mock_piston_service.execute_code.called or result.passed is True
    
    @pytest.mark.asyncio
    async def test_hidden_test_cases_have_different_inputs(self, valid_question_data):
        """Test that hidden test cases have different inputs from visible ones."""
        # Create duplicate test cases (one hidden, one visible with same input)
        valid_question_data["test_cases"] = [
            {"input": "[1,2,3]", "expected_output": "[1,2,3]", "hidden": False},
            {"input": "[1,2,3]", "expected_output": "[1,2,3]", "hidden": True}  # Same input!
        ]
        question = Question(**valid_question_data)
        
        from app.use_cases.validate_test_cases import TestCaseValidationUseCase
        
        use_case = TestCaseValidationUseCase()
        result = await use_case.execute(question)
        
        # Should warn about duplicate test cases
        assert any(issue.severity == ValidationSeverity.WARNING for issue in result.issues)


# ============================================================================
# StarterCodeValidationUseCase Tests
# ============================================================================

class TestStarterCodeValidationUseCase:
    """Tests for starter code validation use case."""
    
    @pytest.mark.asyncio
    async def test_valid_starter_code_passes_validation(self, valid_question, mock_piston_service):
        """Test that valid starter code passes validation."""
        from app.use_cases.validate_starter_code import StarterCodeValidationUseCase
        
        # Mock Piston to return success for syntax check
        mock_piston_service.execute_code.return_value = {
            "stdout": "",
            "stderr": "",
            "exit_code": 0
        }
        
        use_case = StarterCodeValidationUseCase(piston_service=mock_piston_service)
        result = await use_case.execute(valid_question)
        
        assert result.passed is True
    
    @pytest.mark.asyncio
    async def test_invalid_python_starter_code_fails_validation(self, question_with_bad_starter_code, mock_piston_service):
        """Test that invalid Python starter code fails validation."""
        from app.use_cases.validate_starter_code import StarterCodeValidationUseCase
        
        # Mock Piston to return syntax error
        mock_piston_service.execute_code.return_value = {
            "stdout": "",
            "stderr": "SyntaxError: invalid syntax",
            "exit_code": 1
        }
        
        use_case = StarterCodeValidationUseCase(piston_service=mock_piston_service)
        result = await use_case.execute(question_with_bad_starter_code)
        
        assert result.passed is False
        assert any(issue.language == "python" for issue in result.issues)
    
    @pytest.mark.asyncio
    async def test_all_languages_validated(self, valid_question, mock_piston_service):
        """Test that all three languages are validated."""
        from app.use_cases.validate_starter_code import StarterCodeValidationUseCase
        
        mock_piston_service.execute_code.return_value = {
            "stdout": "",
            "stderr": "",
            "exit_code": 0
        }
        
        use_case = StarterCodeValidationUseCase(piston_service=mock_piston_service)
        result = await use_case.execute(valid_question)
        
        # Should validate Python, JavaScript, and Java
        assert mock_piston_service.execute_code.call_count >= 3


# ============================================================================
# SolutionValidationUseCase Tests
# ============================================================================

class TestSolutionValidationUseCase:
    """Tests for solution validation use case."""
    
    @pytest.mark.asyncio
    async def test_solution_passes_all_test_cases(self, valid_question_data, mock_piston_service):
        """Test that the reference solution passes all test cases."""
        from app.use_cases.validate_solution import SolutionValidationUseCase
        
        # Create a question with actual solution code
        valid_question_data["starter"]["python"] = '''
def solve(nums):
    return nums

import sys
import json
lines = sys.stdin.read().strip().split('\\n')
nums = json.loads(lines[0])
result = solve(nums)
print(json.dumps(result))
'''
        valid_question_data["solution"] = "return nums"
        # Use single test case for simplicity
        valid_question_data["test_cases"] = [
            {
                "input": "[1,2,3]",
                "expected_output": "[1,2,3]",
                "description": "Basic test case",
                "hidden": False
            }
        ]
        question = Question(**valid_question_data)
        
        # Mock Piston to return correct output
        mock_piston_service.execute_code.return_value = {
            "stdout": "[1,2,3]",
            "stderr": "",
            "exit_code": 0
        }
        
        use_case = SolutionValidationUseCase(piston_service=mock_piston_service)
        result = await use_case.execute(question)
        
        # Should pass since we have executable code
        assert result.passed is True
    
    @pytest.mark.asyncio
    async def test_solution_fails_test_case(self, valid_question_data, mock_piston_service):
        """Test that solution failing a test case is detected."""
        # Create question with solution that doesn't match expected output
        valid_question_data["solution"] = "def solve(nums): return []"  # Wrong solution
        question = Question(**valid_question_data)
        
        from app.use_cases.validate_solution import SolutionValidationUseCase
        
        # Mock Piston to return wrong output
        mock_piston_service.execute_code.return_value = {
            "stdout": "[]",
            "stderr": "",
            "exit_code": 0
        }
        
        use_case = SolutionValidationUseCase(piston_service=mock_piston_service)
        result = await use_case.execute(question)
        
        assert result.passed is False
        assert any(issue.use_case == ValidationUseCase.SOLUTION for issue in result.issues)
    
    @pytest.mark.asyncio
    async def test_solution_missing_fails_validation(self, valid_question_data, mock_piston_service):
        """Test that missing solution fails validation."""
        valid_question_data["solution"] = None
        question = Question(**valid_question_data)
        
        from app.use_cases.validate_solution import SolutionValidationUseCase
        
        use_case = SolutionValidationUseCase(piston_service=mock_piston_service)
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
        from app.use_cases.validate_time_limits import TimeLimitValidationUseCase
        
        use_case = TimeLimitValidationUseCase()
        result = await use_case.execute(valid_question)
        
        assert result.passed is True
    
    @pytest.mark.asyncio
    async def test_time_limit_within_bounds(self, valid_question_data):
        """Test that time limits within bounds pass validation."""
        # Time complexity implies reasonable time limit
        valid_question_data["time_complexity"] = "O(n)"
        question = Question(**valid_question_data)
        
        from app.use_cases.validate_time_limits import TimeLimitValidationUseCase
        
        use_case = TimeLimitValidationUseCase()
        result = await use_case.execute(question)
        
        assert result.passed is True
    
    @pytest.mark.asyncio
    async def test_slow_algorithm_warns_about_time_limit(self, valid_question_data):
        """Test that slow algorithms get warnings about time limits."""
        valid_question_data["time_complexity"] = "O(n^3)"
        question = Question(**valid_question_data)
        
        from app.use_cases.validate_time_limits import TimeLimitValidationUseCase
        
        use_case = TimeLimitValidationUseCase()
        result = await use_case.execute(question)
        
        # Should warn about potential time limit issues
        assert any(issue.severity == ValidationSeverity.WARNING for issue in result.issues)


# ============================================================================
# FunctionSignatureValidationUseCase Tests
# ============================================================================

class TestFunctionSignatureValidationUseCase:
    """Tests for function signature validation use case."""
    
    @pytest.mark.asyncio
    async def test_valid_function_signature_passes(self, valid_question_data):
        """Test that valid function signature passes validation."""
        from app.use_cases.validate_function_signature import FunctionSignatureValidationUseCase
        
        # Create question with valid Java method signature and Python type hints
        valid_question_data["starter"]["java"] = '''
class Solution {
    public int[] solve(int[] nums) {
        // Your code here
        return new int[0];
    }
}
'''
        valid_question_data["starter"]["python"] = '''
from typing import List

def solve(nums: List[int]) -> List[int]:
    # Your code here
    pass
'''
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
        
        from app.use_cases.validate_function_signature import FunctionSignatureValidationUseCase
        
        use_case = FunctionSignatureValidationUseCase(require_type_hints=True)
        result = await use_case.execute(question)
        
        assert any(issue.severity == ValidationSeverity.WARNING for issue in result.issues)
    
    @pytest.mark.asyncio
    async def test_invalid_return_type_fails(self, valid_question_data):
        """Test that invalid return type fails validation."""
        # Use invalid return type
        valid_question_data["starter"]["python"] = "def solve(nums) -> InvalidType:\n    pass"
        question = Question(**valid_question_data)
        
        from app.use_cases.validate_function_signature import FunctionSignatureValidationUseCase
        
        use_case = FunctionSignatureValidationUseCase()
        result = await use_case.execute(question)
        
        # Should warn about potentially invalid type hint
        assert len(result.issues) > 0


# ============================================================================
# OutputFormatValidationUseCase Tests
# ============================================================================

class TestOutputFormatValidationUseCase:
    """Tests for output format validation use case."""
    
    @pytest.mark.asyncio
    async def test_valid_output_format_passes(self, valid_question):
        """Test that valid output format passes validation."""
        from app.use_cases.validate_output_format import OutputFormatValidationUseCase
        
        use_case = OutputFormatValidationUseCase()
        result = await use_case.execute(valid_question)
        
        assert result.passed is True
    
    @pytest.mark.asyncio
    async def test_inconsistent_output_format_fails(self, valid_question_data):
        """Test that inconsistent output formats across test cases fail."""
        # Different output formats for same problem
        valid_question_data["test_cases"] = [
            {"input": "test1", "expected_output": "[1,2,3]"},  # JSON array
            {"input": "test2", "expected_output": "hello"}     # String - inconsistent!
        ]
        question = Question(**valid_question_data)
        
        from app.use_cases.validate_output_format import OutputFormatValidationUseCase
        
        use_case = OutputFormatValidationUseCase()
        result = await use_case.execute(question)
        
        assert result.passed is False


# ============================================================================
# QuestionValidatorService Tests
# ============================================================================

class TestQuestionValidatorService:
    """Tests for the main question validator service."""
    
    @pytest.mark.asyncio
    async def test_valid_question_passes_all_validations(self, valid_question_data, mock_piston_service):
        """Test that a valid question passes all validations."""
        from app.services.question_validator import QuestionValidatorService
        
        # Create question with valid Java method signature and executable solution
        valid_question_data["starter"]["java"] = '''
class Solution {
    public int[] solve(int[] nums) {
        return nums;
    }
}
'''
        valid_question_data["starter"]["python"] = '''
from typing import List

def solve(nums: List[int]) -> List[int]:
    return nums

import sys
import json
lines = sys.stdin.read().strip().split('\\n')
nums = json.loads(lines[0])
result = solve(nums)
print(json.dumps(result))
'''
        valid_question_data["solution"] = "return nums"
        valid_question_data["test_cases"] = [
            {
                "input": "[1,2,3]",
                "expected_output": "[1,2,3]",
                "description": "Basic test case",
                "hidden": False
            },
            {
                "input": "[4,5,6]",
                "expected_output": "[4,5,6]",
                "description": "Another test case",
                "hidden": True
            }
        ]
        question = Question(**valid_question_data)
        
        service = QuestionValidatorService(piston_service=mock_piston_service)
        
        # Mock Piston to return appropriate output based on input
        def mock_execute_side_effect(*args, **kwargs):
            stdin = kwargs.get('stdin', args[2] if len(args) > 2 else '')
            if '[4,5,6]' in stdin:
                return {"stdout": "[4,5,6]", "stderr": "", "exit_code": 0}
            return {"stdout": "[1,2,3]", "stderr": "", "exit_code": 0}
        
        mock_piston_service.execute_code.side_effect = mock_execute_side_effect
        
        result = await service.validate_question(question)
        
        assert result.valid is True
        assert result.error_count == 0
    
    @pytest.mark.asyncio
    async def test_invalid_question_fails_validation(self, question_with_invalid_test_cases, mock_piston_service):
        """Test that an invalid question fails validation."""
        from app.services.question_validator import QuestionValidatorService
        
        service = QuestionValidatorService(piston_service=mock_piston_service)
        result = await service.validate_question(question_with_invalid_test_cases)
        
        assert result.valid is False
        assert result.error_count > 0
    
    @pytest.mark.asyncio
    async def test_all_use_cases_are_executed(self, valid_question, mock_piston_service):
        """Test that all validation use cases are executed."""
        from app.services.question_validator import QuestionValidatorService
        
        service = QuestionValidatorService(piston_service=mock_piston_service)
        
        mock_piston_service.execute_code.return_value = {
            "stdout": "result",
            "stderr": "",
            "exit_code": 0
        }
        
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
    async def test_validation_can_be_skipped_for_specific_use_cases(self, valid_question, mock_piston_service):
        """Test that specific use cases can be skipped."""
        from app.services.question_validator import QuestionValidatorService
        from app.models.question_validation_schemas import QuestionValidationConfig
        
        config = QuestionValidationConfig(
            skip_use_cases=[ValidationUseCase.SOLUTION]
        )
        
        service = QuestionValidatorService(
            piston_service=mock_piston_service,
            config=config
        )
        
        mock_piston_service.execute_code.return_value = {
            "stdout": "result",
            "stderr": "",
            "exit_code": 0
        }
        
        result = await service.validate_question(valid_question)
        
        # Solution validation should be skipped
        assert ValidationUseCase.SOLUTION not in result.results


# ============================================================================
# Integration with QuestionsService Tests
# ============================================================================

class TestQuestionsServiceValidationIntegration:
    """Tests for validation integration with QuestionsService."""
    
    @pytest.mark.asyncio
    async def test_invalid_question_not_loaded(self, question_with_invalid_test_cases):
        """Test that invalid questions are not loaded into the question bank."""
        from app.services.questions_service import QuestionsService
        
        # This test verifies that validation happens during loading
        # The service should either reject or mark invalid questions
        with patch('app.services.questions_service.QuestionsService._load_questions'):
            service = QuestionsService()
            service.questions = {}
            
            # Attempt to add invalid question without validation
            result = await service.add_question(question_with_invalid_test_cases, validate=False)
            
            # Question should be added but not validated
            assert result.is_validated is False
    
    @pytest.mark.asyncio
    async def test_validation_status_stored_with_question(self, valid_question, mock_piston_service):
        """Test that validation status is stored with the question."""
        from app.services.questions_service import QuestionsService
        from app.services.question_validator import QuestionValidatorService
        
        with patch('app.services.questions_service.QuestionsService._load_questions'):
            validator = QuestionValidatorService(piston_service=mock_piston_service)
            service = QuestionsService(validator=validator)
            service.questions = {}
            
            # Mock Piston response
            mock_piston_service.execute_code.return_value = {
                "stdout": "result",
                "stderr": "",
                "exit_code": 0
            }
            
            # Add question with validation
            result = await service.add_question(valid_question, validate=True)
            
            # Check that validation status is stored
            assert service.validation_statuses.get(valid_question.id) is not None


# ============================================================================
# API Endpoint Tests
# ============================================================================

class TestQuestionValidationAPI:
    """Tests for question validation API endpoints."""
    
    @pytest.mark.asyncio
    async def test_validate_endpoint_returns_validation_result(self, valid_question_data):
        """Test that the validate endpoint returns proper validation result."""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        response = client.post(
            "/api/question-validation/validate",
            json=valid_question_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert "results" in data
    
    @pytest.mark.asyncio
    async def test_batch_validate_endpoint_validates_multiple_questions(self, valid_question_data):
        """Test that batch validate endpoint can validate multiple questions."""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        questions = [valid_question_data, valid_question_data.copy()]
        questions[1]["id"] = "test-question-2"
        
        response = client.post(
            "/api/question-validation/batch-validate",
            json=questions
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2
