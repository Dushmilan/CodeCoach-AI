"""
Test data factories for generating realistic test data.
"""

import random


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
            "negative_numbers": -(2**31),
            "empty_arrays": [],
            "large_arrays": list(range(1000)),
            "nested_objects": {"level1": {"level2": {"level3": "deep"}}},
            "null_values": None,
            "boolean_edge_cases": [True, False, None],
        }

    @staticmethod
    def generate_security_test_payloads():
        """Generate test payloads for security testing."""
        return {
            "sql_injection": [
                "'; DROP TABLE users; --",
                "1' OR '1'='1",
                "admin'--",
                "1' UNION SELECT * FROM passwords--",
            ],
            "xss_payloads": [
                "<script>alert('XSS')</script>",
                "<img src=x onerror=alert('XSS')>",
                "javascript:alert('XSS')",
                "<svg onload=alert('XSS')>",
            ],
            "path_traversal": [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
                "file:///etc/passwd",
            ],
            "command_injection": [
                "; cat /etc/passwd",
                "| whoami",
                "&& rm -rf /",
                "`cat /etc/passwd`",
            ],
            "xxe_payloads": [
                '<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>',
                '<!ENTITY % xxe SYSTEM "file:///etc/passwd"> %xxe;',
            ],
        }

    @staticmethod
    def generate_performance_test_data():
        """Generate test data for performance testing."""
        return {
            "large_code_snippets": {
                "python": "\n".join(
                    [f"def function_{i}():\n    return {i}" for i in range(100)]
                )
            },
            "complex_problems": [
                "Given a 1000x1000 matrix, find the longest increasing path...",
                "Implement a distributed consistent hash ring...",
                "Design a distributed rate limiter...",
            ],
            "heavy_computation": [
                "Calculate the first 1000 prime numbers",
                "Find all permutations of a 10-element array",
                "Solve the traveling salesman problem for 20 cities",
            ],
        }

    @staticmethod
    def generate_valid_test_questions(count: int = 10):
        """Generate a set of valid test questions."""
        categories = ["arrays", "strings", "dynamic-programming", "trees", "graphs"]
        difficulties = ["easy", "medium", "hard"]
        titles = [
            "Two Sum",
            "Reverse String",
            "Binary Search",
            "Valid Parentheses",
            "Merge Sort",
            "BFS Traversal",
            "Quick Sort",
            "Heap Sort",
            "LRU Cache",
            "Maximum Subarray",
        ]
        questions = []
        for i in range(count):
            title = titles[i % len(titles)]
            questions.append(
                {
                    "id": f"test-question-{i}",
                    "title": title,
                    "difficulty": random.choice(difficulties),
                    "category": random.choice(categories),
                    "company_tags": ["Google", "Amazon"],
                    "description": f"Solve {title}",
                    "starter": {
                        "python": f"def solution(input):\n    # TODO: Implement {title}\n    pass"
                    },
                    "examples": [
                        {
                            "input": "input = {}".format(
                                random.choice(["[1,2,3]", '"hello"', "5"])
                            ),
                            "output": str(random.randint(1, 100)),
                            "explanation": f"Example for {title}",
                        }
                    ],
                    "test_cases": [
                        {
                            "input": str(random.randint(1, 100)),
                            "expected_output": str(random.randint(1, 100)),
                            "description": f"Test case for {title}",
                            "hidden": False,
                        }
                    ],
                }
            )
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
            "difficulty": "easy",
        }
    ],
    "invalid_requests": [
        {
            "problem": "",  # Empty problem
            "code": "invalid code",
            "language": "python",
            "message": "",
            "mode": "invalid_mode",
            "difficulty": "invalid_difficulty",
        }
    ],
}
