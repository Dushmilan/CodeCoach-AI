"""
Unit tests for boundary condition validation.
"""
import pytest
from pydantic import ValidationError

from app.models.schemas import (
    CoachingRequest, CodeExecutionRequest, Question, QuestionSummary,
    CoachingMode, Language, Difficulty, StarterCode, TestCase, Example
)


class TestBoundaryConditions:
    """Test cases for boundary conditions."""
    
    def test_coaching_request_max_lengths(self):
        """Test coaching request with maximum string lengths."""
        # Test with very long problem description
        max_problem = "x" * 5000
        max_code = "x" * 10000
        max_message = "x" * 2000
        
        request = CoachingRequest(
            problem=max_problem,
            code=max_code,
            language=Language.PYTHON,
            message=max_message,
            mode=CoachingMode.HINT,
            difficulty=Difficulty.EASY
        )
        
        assert request.problem == max_problem
        assert request.code == max_code
        assert request.message == max_message
    
    def test_coaching_request_empty_strings(self):
        """Test coaching request with empty strings."""
        request = CoachingRequest(
            problem="",
            code="",
            language=Language.PYTHON,
            message="",
            mode=CoachingMode.HINT,
            difficulty=Difficulty.EASY
        )
        
        assert request.problem == ""
        assert request.code == ""
        assert request.message == ""
    
    def test_coaching_request_unicode_strings(self):
        """Test coaching request with unicode strings."""
        unicode_problem = "こんにちは世界🌍🚀" * 50
        unicode_code = "def こんにちは():\n    return '世界'"
        unicode_message = "テストメッセージ🔥"
        
        request = CoachingRequest(
            problem=unicode_problem,
            code=unicode_code,
            language=Language.PYTHON,
            message=unicode_message,
            mode=CoachingMode.HINT,
            difficulty=Difficulty.EASY
        )
        
        assert request.problem == unicode_problem
        assert request.code == unicode_code
        assert request.message == unicode_message
    
    def test_code_execution_request_max_lengths(self):
        """Test code execution request with maximum string lengths."""
        max_code = "x" * 10000
        max_stdin = "x" * 5000
        max_version = "x" * 50
        
        request = CodeExecutionRequest(
            language=Language.PYTHON,
            code=max_code,
            stdin=max_stdin,
            version=max_version
        )
        
        assert request.code == max_code
        assert request.stdin == max_stdin
        assert request.version == max_version
    
    def test_code_execution_request_empty_strings(self):
        """Test code execution request with empty strings."""
        request = CodeExecutionRequest(
            language=Language.PYTHON,
            code="",
            stdin="",
            version=""
        )
        
        assert request.code == ""
        assert request.stdin == ""
        assert request.version == ""
    
    def test_question_max_lengths(self):
        """Test question with maximum string lengths."""
        max_id = "x" * 100
        max_title = "x" * 200
        max_description = "x" * 10000
        max_solution = "x" * 5000
        max_constraints = ["x" * 200] * 10

        starter = StarterCode(
            python="x" * 1000,
            javascript="",
            java=""
        )

        examples = [Example(input="x" * 500, output="x" * 500, explanation="x" * 1000)] * 5
        test_cases = [TestCase(input="x" * 500, expected_output="x" * 500, description="x" * 200, hidden=False)] * 10

        question = Question(
            id=max_id,
            title=max_title,
            difficulty=Difficulty.EASY,
            category="x" * 50,
            company_tags=["x" * 50] * 20,
            description=max_description,
            starter=starter,
            examples=examples,
            test_cases=test_cases,
            hints=["x" * 200] * 5,
            solution=max_solution,
            time_complexity="x" * 20,
            space_complexity="x" * 20,
            constraints=max_constraints
        )

        assert question.id == max_id
        assert question.title == max_title
        assert question.description == max_description
        assert question.solution == max_solution

    def test_question_empty_arrays(self):
        """Test question with empty arrays."""
        starter = StarterCode(
            python="",
            javascript="",
            java=""
        )

        question = Question(
            id="test",
            title="Test",
            difficulty=Difficulty.EASY,
            category="test",
            company_tags=[],
            description="test",
            starter=starter,
            examples=[],
            test_cases=[],
            hints=[],
            solution="",
            time_complexity="",
            space_complexity="",
            constraints=[]
        )

        assert question.company_tags == []
        assert question.examples == []
        assert question.test_cases == []
        assert question.hints == []
        assert question.constraints == []

    def test_question_large_arrays(self):
        """Test question with large arrays."""
        large_company_tags = [f"company_{i}" for i in range(100)]
        large_examples = [Example(input=f"input_{i}", output=f"output_{i}", explanation=f"explanation_{i}") for i in range(50)]
        large_test_cases = [TestCase(input=f"input_{i}", expected_output=f"output_{i}", description=f"test_{i}", hidden=i % 2 == 0) for i in range(100)]

        starter = StarterCode(
            python="def test(): pass",
            javascript="",
            java=""
        )

        question = Question(
            id="test",
            title="Test",
            difficulty=Difficulty.EASY,
            category="test",
            company_tags=large_company_tags,
            description="test",
            starter=starter,
            examples=large_examples,
            test_cases=large_test_cases,
            hints=[f"hint_{i}" for i in range(20)],
            solution="solution",
            time_complexity="O(n)",
            space_complexity="O(1)",
            constraints=[f"constraint_{i}" for i in range(10)]
        )

        assert len(question.company_tags) == 100
        assert len(question.examples) == 50
        assert len(question.test_cases) == 100
        assert len(question.hints) == 20
        assert len(question.constraints) == 10
    
    def test_enum_boundary_values(self):
        """Test enum boundary values."""
        # Test all valid enum values
        difficulties = [Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD]
        languages = [Language.PYTHON]
        modes = [CoachingMode.HINT, CoachingMode.REVIEW, CoachingMode.EXPLAIN, CoachingMode.DEBUG]

        for difficulty in difficulties:
            request = CoachingRequest(
                problem="test",
                code="test",
                language=Language.PYTHON,
                message="test",
                mode=CoachingMode.HINT,
                difficulty=difficulty
            )
            assert request.difficulty == difficulty

        for language in languages:
            request = CodeExecutionRequest(
                language=language,
                code="test"
            )
            assert request.language == language
    
    def test_invalid_enum_values(self):
        """Test invalid enum values."""
        with pytest.raises(ValidationError):
            CoachingRequest(
                problem="test",
                code="test",
                language="invalid_language",
                message="test",
                mode=CoachingMode.HINT,
                difficulty=Difficulty.EASY
            )
        
        with pytest.raises(ValidationError):
            CoachingRequest(
                problem="test",
                code="test",
                language=Language.PYTHON,
                message="test",
                mode="invalid_mode",
                difficulty=Difficulty.EASY
            )
    
    def test_special_characters_in_strings(self):
        """Test special characters in strings."""
        special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        unicode_chars = "こんにちは世界🌍🚀"
        control_chars = "\n\t\r\b\f"
        
        request = CoachingRequest(
            problem=f"Problem with {special_chars} and {unicode_chars}",
            code=f"def test():\n    print('{special_chars}')\n    print('{unicode_chars}')\n    print('{control_chars}')",
            language=Language.PYTHON,
            message=f"Message with {special_chars} and {unicode_chars}",
            mode=CoachingMode.HINT,
            difficulty=Difficulty.EASY
        )
        
        assert special_chars in request.problem
        assert unicode_chars in request.problem
        assert control_chars in request.code
    
    def test_numeric_boundary_values(self):
        """Test numeric boundary values in constraints."""
        # Test large numbers in constraints
        large_constraints = [
            f"1 <= n <= {2**31-1}",
            f"-{2**31} <= nums[i] <= {2**31-1}",
            f"0 <= len(s) <= {10**6}",
            f"1 <= k <= {10**9}"
        ]

        starter = StarterCode(
            python="def test(): pass",
            javascript="",
            java=""
        )

        examples = [Example(input="1", output="1", explanation="test")]
        test_cases = [TestCase(input="1", expected_output="1", description="test", hidden=False)]

        question = Question(
            id="test",
            title="Test",
            difficulty=Difficulty.EASY,
            category="test",
            company_tags=["test"],
            description="test",
            starter=starter,
            examples=examples,
            test_cases=test_cases,
            constraints=large_constraints
        )
        
        assert len(question.constraints) == 4
        for constraint in question.constraints:
            assert isinstance(constraint, str)
            assert len(constraint) > 0
    
    def test_nested_object_boundaries(self):
        """Test nested object boundaries."""
        # Test deeply nested starter code
        nested_starter = StarterCode(
            python="def solution():\n    def helper():\n        def inner():\n            return 'nested'\n        return inner()\n    return helper()",
            javascript="",
            java=""
        )

        examples = [Example(input="1", output="1", explanation="test")]
        test_cases = [TestCase(input="1", expected_output="1", description="test", hidden=False)]

        question = Question(
            id="test",
            title="Test",
            difficulty=Difficulty.EASY,
            category="test",
            company_tags=["test"],
            description="test",
            starter=nested_starter,
            examples=examples,
            test_cases=test_cases
        )

        assert len(question.starter.python) > 100
    
    def test_boolean_edge_cases(self):
        """Test boolean edge cases."""
        # Test hidden flag in test cases
        test_cases = [
            TestCase(input="1", expected_output="1", description="test", hidden=True),
            TestCase(input="2", expected_output="2", description="test", hidden=False),
            TestCase(input="3", expected_output="3", description="test")  # hidden defaults to False
        ]

        starter = StarterCode(
            python="def test(): pass",
            javascript="",
            java=""
        )

        examples = [Example(input="1", output="1", explanation="test")]

        question = Question(
            id="test",
            title="Test",
            difficulty=Difficulty.EASY,
            category="test",
            company_tags=["test"],
            description="test",
            starter=starter,
            examples=examples,
            test_cases=test_cases
        )

        assert len(question.test_cases) == 3
        assert question.test_cases[0].hidden is True
        assert question.test_cases[1].hidden is False
        assert question.test_cases[2].hidden is False

    def test_zero_and_negative_values(self):
        """Test zero and negative value handling."""
        # Test with zero values in constraints
        zero_constraints = [
            "0 <= n <= 0",
            "-1 <= nums[i] <= 1",
            "len(s) = 0"
        ]

        starter = StarterCode(
            python="def test(): pass",
            javascript="",
            java=""
        )

        examples = [Example(input="0", output="0", explanation="zero test")]
        test_cases = [TestCase(input="0", expected_output="0", description="zero test", hidden=False)]

        question = Question(
            id="test",
            title="Test",
            difficulty=Difficulty.EASY,
            category="test",
            company_tags=["test"],
            description="test",
            starter=starter,
            examples=examples,
            test_cases=test_cases,
            constraints=zero_constraints
        )
        
        assert len(question.constraints) == 3
        for constraint in question.constraints:
            assert isinstance(constraint, str)
    
    def test_empty_object_handling(self):
        """Test empty object handling."""
        # Test empty starter code object
        empty_starter = StarterCode(
            python="",
            javascript="",
            java=""
        )

        question = Question(
            id="test",
            title="Test",
            difficulty=Difficulty.EASY,
            category="test",
            company_tags=["test"],
            description="test",
            starter=empty_starter,
            examples=[],
            test_cases=[],
            constraints=[]
        )

        assert question.starter.python == ""
        assert len(question.examples) == 0
        assert len(question.test_cases) == 0
        assert len(question.constraints) == 0
    
    def test_version_string_formats(self):
        """Test version string format boundaries."""
        version_formats = [
            "1.0.0",
            "1.2.3-alpha",
            "2.0.0-beta.1",
            "10.20.30",
            "0.0.1",
            "999.999.999"
        ]
        
        for version in version_formats:
            request = CodeExecutionRequest(
                language=Language.PYTHON,
                code="print('test')",
                version=version
            )
            assert request.version == version