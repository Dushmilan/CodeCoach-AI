"""
Test configuration and fixtures for CodeCoach AI API testing.
"""
import pytest
import pytest_asyncio
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient
import json
import os
import tempfile
from pathlib import Path

from app.main import app
from app.services.nim_service import NIMService
from app.services.piston_service import PistonService
from app.services.questions_service import QuestionsService


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_client() -> Generator:
    """Create a test client for synchronous testing."""
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture(scope="session")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for asynchronous testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_nim_service():
    """Mock NIM service for testing."""
    class MockNIMService:
        def __init__(self, api_key: str = "test_key"):
            self.api_key = api_key
            
        async def get_coaching_response(self, problem: str, code: str, language: str, 
                                      message: str, mode: str, difficulty: str):
            """Mock coaching response generation."""
            responses = {
                "hint": f"Consider using a hash map to solve this {difficulty} problem.",
                "review": "Your code looks good, but consider edge cases like empty arrays.",
                "explain": f"This is a classic {difficulty} difficulty problem that requires...",
                "debug": "The issue appears to be in your loop condition. Check line 5."
            }
            yield responses.get(mode, "Here's some guidance for your problem.")
    
    return MockNIMService


@pytest.fixture
def mock_piston_service():
    """Mock Piston service for testing."""
    class MockPistonService:
        async def execute_code(self, language: str, code: str, stdin: str = "", version: str = None):
            """Mock code execution."""
            mock_results = {
                "python": {
                    "stdout": "Hello, World!\n",
                    "stderr": "",
                    "exit_code": 0,
                    "execution_time": "0.05s",
                    "memory_usage": "8.2MB",
                    "language": "python",
                    "version": "3.11.0"
                },
                "javascript": {
                    "stdout": "Hello, World!\n",
                    "stderr": "",
                    "exit_code": 0,
                    "execution_time": "0.03s",
                    "memory_usage": "12.1MB",
                    "language": "javascript",
                    "version": "18.17.0"
                }
            }
            
            result = mock_results.get(language, {
                "stdout": "",
                "stderr": f"Language {language} not supported",
                "exit_code": 1,
                "execution_time": "0.01s",
                "memory_usage": "1MB",
                "language": language,
                "version": version or "unknown"
            })
            
            if "error" in code.lower():
                result["stderr"] = "SyntaxError: invalid syntax"
                result["exit_code"] = 1
                
            return result
        
        def validate_code(self, language: str, code: str):
            """Mock code validation."""
            is_valid = "error" not in code.lower()
            return {
                "valid": is_valid,
                "warnings": ["Consider adding type hints"] if language == "python" else [],
                "errors": ["Syntax error on line 1"] if not is_valid else []
            }
        
        async def get_runtimes(self):
            """Mock runtime information."""
            return [
                {
                    "language": "python",
                    "version": "3.11.0",
                    "aliases": ["py", "python3"],
                    "runtime": "cpython"
                },
                {
                    "language": "javascript",
                    "version": "18.17.0",
                    "aliases": ["js", "node"],
                    "runtime": "node"
                },
                {
                    "language": "java",
                    "version": "17.0.0",
                    "aliases": ["java"],
                    "runtime": "openjdk"
                }
            ]
    
    return MockPistonService


@pytest.fixture
def mock_questions_service():
    """Mock questions service for testing."""
    class MockQuestionsService:
        def __init__(self):
            self.questions = self._load_mock_questions()
        
        def _load_mock_questions(self):
            """Load mock questions data."""
            return [
                {
                    "id": "two-sum",
                    "title": "Two Sum",
                    "difficulty": "easy",
                    "category": "arrays",
                    "company_tags": ["Google", "Amazon", "Facebook"],
                    "description": "Given an array of integers, return indices of the two numbers...",
                    "starter": {
                        "python": "def two_sum(nums, target):\n    pass",
                        "javascript": "function twoSum(nums, target) {\n    \n}",
                        "java": "public int[] twoSum(int[] nums, int target) {\n    \n}"
                    },
                    "examples": [
                        {
                            "input": "nums = [2,7,11,15], target = 9",
                            "output": "[0,1]",
                            "explanation": "Because nums[0] + nums[1] = 9"
                        }
                    ],
                    "test_cases": [
                        {
                            "input": "[2,7,11,15]\n9",
                            "expected_output": "[0,1]",
                            "description": "Basic case"
                        }
                    ]
                },
                {
                    "id": "reverse-linked-list",
                    "title": "Reverse Linked List",
                    "difficulty": "medium",
                    "category": "linked-lists",
                    "company_tags": ["Microsoft", "Apple"],
                    "description": "Reverse a singly linked list.",
                    "starter": {
                        "python": "def reverse_list(head):\n    pass",
                        "javascript": "function reverseList(head) {\n    \n}",
                        "java": "public ListNode reverseList(ListNode head) {\n    \n}"
                    },
                    "examples": [
                        {
                            "input": "head = [1,2,3,4,5]",
                            "output": "[5,4,3,2,1]",
                            "explanation": "The reversed linked list"
                        }
                    ],
                    "test_cases": [
                        {
                            "input": "[1,2,3,4,5]",
                            "expected_output": "[5,4,3,2,1]",
                            "description": "Complete reversal"
                        }
                    ]
                }
            ]
        
        def get_all_questions(self, difficulty=None, category=None, page=1, per_page=20):
            questions = self.questions
            if difficulty:
                questions = [q for q in questions if q["difficulty"] == difficulty]
            if category:
                questions = [q for q in questions if q["category"] == category]
            
            start = (page - 1) * per_page
            end = start + per_page
            return questions[start:end]
        
        def get_question_by_id(self, question_id):
            for question in self.questions:
                if question["id"] == question_id:
                    return question
            raise ValueError(f"Question {question_id} not found")
        
        def get_categories(self):
            return list(set(q["category"] for q in self.questions))
        
        def get_company_tags(self):
            companies = set()
            for question in self.questions:
                companies.update(question["company_tags"])
            return list(companies)
        
        def get_total_count(self):
            return len(self.questions)
        
        def search_questions(self, query, difficulty=None, category=None):
            results = []
            for question in self.questions:
                if query.lower() in question["title"].lower() or query.lower() in question["description"].lower():
                    if (not difficulty or question["difficulty"] == difficulty) and \
                       (not category or question["category"] == category):
                        results.append(question)
            return results
    
    return MockQuestionsService


@pytest.fixture
def test_env_vars():
    """Set up test environment variables."""
    env_vars = {
        "NVIDIA_API_KEY": "test_nvidia_key",
        "PISTON_API_URL": "https://emkc.org/api/v2/piston",
        "QUESTIONS_FILE_PATH": "tests/fixtures/test_questions.json",
        "RATE_LIMIT_PER_MINUTE": "100",
        "RATE_LIMIT_PER_HOUR": "1000",
        "ENVIRONMENT": "testing"
    }
    
    # Store original values
    original_values = {}
    for key, value in env_vars.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restore original values
    for key, original_value in original_values.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture
def sample_question_data():
    """Provide sample question data for testing."""
    return {
        "id": "test-question",
        "title": "Test Question",
        "difficulty": "easy",
        "category": "arrays",
        "company_tags": ["TestCompany"],
        "description": "This is a test question for unit testing.",
        "starter": {
            "python": "def test_function(input):\n    pass",
            "javascript": "function testFunction(input) {\n    \n}",
            "java": "public int testFunction(int input) {\n    \n}"
        },
        "examples": [
            {
                "input": "input = [1, 2, 3]",
                "output": "6",
                "explanation": "Sum of array elements"
            }
        ],
        "test_cases": [
            {
                "input": "[1, 2, 3]",
                "expected_output": "6",
                "description": "Basic test case",
                "hidden": False
            }
        ],
        "hints": ["Consider using a loop", "Think about edge cases"],
        "solution": "Use a simple loop to sum the elements",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
        "constraints": ["1 <= len(array) <= 1000", "-1000 <= array[i] <= 1000"]
    }


@pytest.fixture
def sample_coaching_request():
    """Provide sample coaching request data."""
    return {
        "problem": "Given an array of integers, find the maximum sum of any contiguous subarray.",
        "code": "def max_subarray_sum(nums):\n    max_sum = nums[0]\n    current_sum = nums[0]\n    \n    for i in range(1, len(nums)):\n        current_sum = max(nums[i], current_sum + nums[i])\n        max_sum = max(max_sum, current_sum)\n    \n    return max_sum",
        "language": "python",
        "message": "Can you review my solution and suggest improvements?",
        "mode": "review",
        "difficulty": "medium"
    }


@pytest.fixture
def sample_code_execution_request():
    """Provide sample code execution request data."""
    return {
        "language": "python",
        "code": "print('Hello, World!')\nprint(sum([1, 2, 3, 4, 5]))",
        "stdin": "",
        "version": "3.11.0"
    }


@pytest.fixture
def temp_questions_file():
    """Create a temporary questions file for testing."""
    test_questions = [
        {
            "id": "test-question-1",
            "title": "Test Question 1",
            "difficulty": "easy",
            "category": "arrays",
            "company_tags": ["TestCompany"],
            "description": "Test description 1",
            "starter": {
                "python": "def test1(input):\n    pass",
                "javascript": "function test1(input) {\n    \n}",
                "java": "public int test1(int input) {\n    \n}"
            },
            "examples": [{"input": "[1,2,3]", "output": "6", "explanation": "Sum"}],
            "test_cases": [{"input": "[1,2,3]", "expected_output": "6", "description": "Test"}]
        },
        {
            "id": "test-question-2",
            "title": "Test Question 2",
            "difficulty": "medium",
            "category": "strings",
            "company_tags": ["AnotherCompany"],
            "description": "Test description 2",
            "starter": {
                "python": "def test2(input):\n    pass",
                "javascript": "function test2(input) {\n    \n}",
                "java": "public String test2(String input) {\n    \n}"
            },
            "examples": [{"input": "'hello'", "output": "'olleh'", "explanation": "Reverse"}],
            "test_cases": [{"input": "'hello'", "expected_output": "'olleh'", "description": "Test"}]
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_questions, f, indent=2)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)
