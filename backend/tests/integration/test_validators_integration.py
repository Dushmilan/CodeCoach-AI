"""
Integration tests for simple validators.
Tests cover end-to-end validation workflows for Python.
"""

import pytest
from app.services.simple_validators import (
    SimplePythonValidator,
    SimpleTestRunner
)


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def sample_test_cases():
    """Sample test cases for testing."""
    return [
        {
            "input": "[2,7,11,15]\n9",
            "expected_output": "[0, 1]",
            "description": "Basic two-sum case"
        },
        {
            "input": "[3,2,4]\n6",
            "expected_output": "[1, 2]",
            "description": "Non-consecutive indices"
        },
        {
            "input": "[3,3]\n6",
            "expected_output": "[0, 1]",
            "description": "Duplicate values"
        }
    ]


# ==============================================================================
# Integration Tests
# ==============================================================================

@pytest.mark.integration
def test_end_to_end_python(sample_test_cases):
    """End-to-end test for Python validation."""
    runner = SimpleTestRunner()

    code = '''
import sys
def twoSum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []

nums = eval(input().strip())
target = int(input().strip())
print(twoSum(nums, target))
'''

    results = runner.run_all_tests('python', code, sample_test_cases)

    # Should pass all basic test cases
    assert results['total_tests'] == 3
    assert results['passed_tests'] == 3
    assert results['success_rate'] == 1.0


@pytest.mark.integration
def test_cross_language_consistency():
    """Test that Python validator produces consistent result structures."""
    runner = SimpleTestRunner()

    # Simple code that outputs "42"
    python_code = 'print(42)'

    test_case = {"input": "", "expected_output": "42", "description": "Output 42"}

    # Run for Python
    python_result = runner.run_single_test('python', python_code, test_case)

    # Check result structure consistency
    assert 'passed' in python_result, "Python result missing 'passed' key"
    assert 'execution_time' in python_result, "Python result missing 'execution_time' key"
    assert python_result['passed'] == True, "Python should have passed"


@pytest.mark.integration
def test_error_handling_consistency():
    """Test that Python validator handles errors consistently."""
    runner = SimpleTestRunner()

    # Code with syntax error in Python
    python_invalid = 'def broken('  # Missing closing parenthesis and colon

    test_case = {"input": "", "expected_output": "", "description": "Invalid code"}

    # Should fail gracefully
    python_result = runner.run_single_test('python', python_invalid, test_case)

    assert python_result['passed'] == False
    assert python_result['error'] is not None
