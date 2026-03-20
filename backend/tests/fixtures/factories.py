"""
Test data factories for generating realistic test data.
"""
import factory
from factory import Faker
from typing import List, Dict, Any
import json
import random
from datetime import datetime

from app.models.schemas import (
    CoachingRequest, CoachingResponse, CodeExecutionRequest, CodeExecutionResult,
    Question, QuestionSummary, QuestionsListResponse, HealthResponse,
    CoachingMode, Language, Difficulty
)


class CoachingRequestFactory(factory.Factory):
    """Factory for generating coaching requests."""

    class Meta:
        model = CoachingRequest

    problem = factory.Faker('text', max_nb_chars=200)
    code = factory.LazyAttribute(lambda obj: f"def solution():\n    pass")
    language = factory.Iterator([Language.PYTHON])
    message = factory.Faker('text', max_nb_chars=100)
    mode = factory.Iterator([CoachingMode.HINT, CoachingMode.REVIEW, CoachingMode.EXPLAIN, CoachingMode.DEBUG])
    difficulty = factory.Iterator([Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD])


class CoachingResponseFactory(factory.Factory):
    """Factory for generating coaching responses."""

    class Meta:
        model = CoachingResponse

    response = factory.Faker('text', max_nb_chars=500)
    mode = factory.Iterator([CoachingMode.HINT, CoachingMode.REVIEW, CoachingMode.EXPLAIN, CoachingMode.DEBUG])
    language = factory.Iterator([Language.PYTHON])


class CodeExecutionRequestFactory(factory.Factory):
    """Factory for generating code execution requests."""

    class Meta:
        model = CodeExecutionRequest

    language = factory.Iterator([Language.PYTHON])
    code = factory.LazyAttribute(lambda obj: "print('Hello, World!')\nprint(sum([1, 2, 3, 4, 5]))")
    stdin = factory.Faker('text', max_nb_chars=50)
    version = factory.Faker('semver')


class CodeExecutionResultFactory(factory.Factory):
    """Factory for generating code execution results."""

    class Meta:
        model = CodeExecutionResult

    stdout = factory.Faker('text', max_nb_chars=100)
    stderr = factory.Faker('text', max_nb_chars=50)
    exit_code = factory.Iterator([0, 1, 2])
    execution_time = factory.Faker('numerify', text='0.##s')
    memory_usage = factory.Faker('numerify', text='##.#MB')
    language = factory.Iterator(["python"])
    version = factory.Faker('semver')


class QuestionFactory(factory.Factory):
    """Factory for generating complete question objects."""

    class Meta:
        model = Question

    id = factory.Sequence(lambda n: f"question-{n}")
    title = factory.Faker('sentence', nb_words=4)
    difficulty = factory.Iterator([Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD])
    category = factory.Iterator(["arrays", "strings", "linked-lists", "trees", "dynamic-programming"])
    company_tags = factory.LazyFunction(lambda: random.sample(["Google", "Amazon", "Microsoft", "Facebook", "Apple"], k=random.randint(1, 3)))
    description = factory.Faker('text', max_nb_chars=300)
    starter = factory.LazyAttribute(lambda obj: {
        "python": f"def solution({obj.category}):\n    # TODO: Implement solution\n    pass"
    })
    examples = factory.LazyFunction(lambda: [
            {
                "input": f"{random.choice(['nums', 's', 'root'])} = {random.choice(['[1,2,3]', '\"hello\"', '5'])}",
                "output": str(random.randint(1, 100)),
                "explanation": "Example explanation"
            }
            for _ in range(random.randint(1, 3))
    ])
    test_cases = factory.LazyFunction(lambda: [
        {
            "input": str(random.randint(1, 100)),
            "expected_output": str(random.randint(1, 100)),
            "description": factory.Faker('text', max_nb_chars=50),
            "hidden": random.choice([True, False])
        }
        for _ in range(random.randint(2, 5))
    ])
    hints = factory.LazyFunction(lambda: [factory.Faker('text', max_nb_chars=50) for _ in range(random.randint(1, 3))])
    solution = factory.Faker('text', max_nb_chars=200)
    time_complexity = factory.Iterator(["O(1)", "O(n)", "O(n log n)", "O(n²)"])
    space_complexity = factory.Iterator(["O(1)", "O(n)", "O(log n)"])
    constraints = factory.LazyFunction(lambda: [
        f"1 <= len(input) <= {random.randint(100, 10000)}",
        f"-{random.randint(100, 1000)} <= input[i] <= {random.randint(100, 1000)}"
    ])


class QuestionSummaryFactory(factory.Factory):
    """Factory for generating question summary objects."""
    
    class Meta:
        model = QuestionSummary
    
    id = factory.Sequence(lambda n: f"question-{n}")
    title = factory.Faker('sentence', nb_words=4)
    difficulty = factory.Iterator([Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD])
    category = factory.Iterator(["arrays", "strings", "linked-lists", "trees", "dynamic-programming"])
    company_tags = factory.LazyFunction(lambda: random.sample(["Google", "Amazon", "Microsoft", "Facebook", "Apple"], k=random.randint(1, 3)))
    solved = factory.Iterator([True, False])


class QuestionsListResponseFactory(factory.Factory):
    """Factory for generating questions list response objects."""
    
    class Meta:
        model = QuestionsListResponse
    
    questions = factory.LazyFunction(lambda: [QuestionSummaryFactory() for _ in range(random.randint(5, 20))])
    total = factory.LazyAttribute(lambda obj: len(obj.questions) + random.randint(0, 100))
    page = factory.Iterator([1, 2, 3])
    per_page = factory.Iterator([10, 20, 50])


class HealthResponseFactory(factory.Factory):
    """Factory for generating health response objects."""
    
    class Meta:
        model = HealthResponse
    
    status = factory.Iterator(["healthy", "degraded", "unhealthy"])
    service = "codecoach-ai-backend"
    version = "1.0.0"
    timestamp = factory.LazyFunction(lambda: datetime.utcnow().isoformat() + "Z")
    dependencies = factory.LazyFunction(lambda: {
        "fastapi": "running",
        "uvicorn": "running",
        "cors": "configured",
        "rate_limiting": "enabled"
    })


class TestDataGenerator:
    """Utility class for generating test data with specific characteristics."""
    
    @staticmethod
    def generate_boundary_test_data():
        """Generate test data for boundary condition testing."""
        return {
            "empty_strings": "",
            "max_length_strings": "a" * 1000,
            "special_characters": "!@#$%^&*()_+-=[]{}|;':\",./<>?",
            "unicode_strings": "こんにちは世界🌍🚀",
            "large_numbers": 2**31 - 1,
            "negative_numbers": -2**31,
            "empty_arrays": [],
            "large_arrays": list(range(1000)),
            "nested_objects": {"level1": {"level2": {"level3": "deep"}}},
            "null_values": None,
            "boolean_edge_cases": [True, False, None]
        }
    
    @staticmethod
    def generate_security_test_payloads():
        """Generate test payloads for security testing."""
        return {
            "sql_injection": [
                "'; DROP TABLE users; --",
                "1' OR '1'='1",
                "admin'--",
                "1' UNION SELECT * FROM passwords--"
            ],
            "xss_payloads": [
                "<script>alert('XSS')</script>",
                "<img src=x onerror=alert('XSS')>",
                "javascript:alert('XSS')",
                "<svg onload=alert('XSS')>"
            ],
            "path_traversal": [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
                "file:///etc/passwd"
            ],
            "command_injection": [
                "; cat /etc/passwd",
                "| whoami",
                "&& rm -rf /",
                "`cat /etc/passwd`"
            ],
            "xxe_payloads": [
                "<!DOCTYPE foo [<!ENTITY xxe SYSTEM \"file:///etc/passwd\">]><foo>&xxe;</foo>",
                "<!ENTITY % xxe SYSTEM \"file:///etc/passwd\"> %xxe;"
            ]
        }
    
    @staticmethod
    def generate_performance_test_data():
        """Generate test data for performance testing."""
        return {
            "large_code_snippets": {
                "python": "\n".join([f"def function_{i}():\n    return {i}" for i in range(100)])
            },
            "complex_problems": [
                "Given a 1000x1000 matrix, find the longest increasing path...",
                "Implement a distributed consistent hash ring...",
                "Design a distributed rate limiter..."
            ],
            "heavy_computation": [
                "Calculate the first 1000 prime numbers",
                "Find all permutations of a 10-element array",
                "Solve the traveling salesman problem for 20 cities"
            ]
        }
    
    @staticmethod
    def generate_valid_test_questions(count: int = 10):
        """Generate a set of valid test questions."""
        questions = []
        for i in range(count):
            question = QuestionFactory()
            questions.append({
                "id": f"test-question-{i}",
                "title": question.title,
                "difficulty": question.difficulty.value,
                "category": question.category,
                "company_tags": question.company_tags,
                "description": question.description,
                "starter": {
                    "python": f"def solution(input):\n    # TODO: Implement solution for {question.title}\n    pass"
                },
                "examples": [
                    {
                        "input": f"input = {random.choice(['[1,2,3]', '"hello"', '5'])}",
                        "output": str(random.randint(1, 100)),
                        "explanation": f"Example for {question.title}"
                    }
                ],
                "test_cases": [
                    {
                        "input": str(random.randint(1, 100)),
                        "expected_output": str(random.randint(1, 100)),
                        "description": f"Test case for {question.title}",
                        "hidden": False
                    }
                ]
            })
        return questions


# Pre-defined test data sets
VALID_TEST_QUESTIONS = TestDataGenerator.generate_valid_test_questions(20)

BOUNDARY_TEST_DATA = TestDataGenerator.generate_boundary_test_data()

SECURITY_TEST_PAYLOADS = TestDataGenerator.generate_security_test_payloads()

PERFORMANCE_TEST_DATA = TestDataGenerator.generate_performance_test_data()

# Common test scenarios
COMMON_TEST_SCENARIOS = {
    "valid_requests": [
        {
            "problem": "Find the maximum element in an array",
            "code": "def max_element(arr):\n    return max(arr)",
            "language": "python",
            "message": "Is this the most efficient solution?",
            "mode": "review",
            "difficulty": "easy"
        }
    ],
    "invalid_requests": [
        {
            "problem": "",  # Empty problem
            "code": "invalid code",
            "language": "python",
            "message": "",
            "mode": "invalid_mode",
            "difficulty": "invalid_difficulty"
        }
    ]
}