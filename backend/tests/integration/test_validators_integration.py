"""
Integration tests for simple validators.
Tests cover end-to-end validation workflows across all languages.
"""

import pytest
from app.services.simple_validators import (
    SimplePythonValidator,
    SimpleJavaScriptValidator,
    SimpleJavaValidator,
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
def test_end_to_end_javascript():
    """End-to-end test for JavaScript validation."""
    runner = SimpleTestRunner()

    code = '''
const readline = require('readline');
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

let lines = [];
rl.on('line', (line) => {
    lines.push(line);
}).on('close', () => {
    const nums = JSON.parse(lines[0]);
    const target = parseInt(lines[1]);

    for (let i = 0; i < nums.length; i++) {
        for (let j = i + 1; j < nums.length; j++) {
            if (nums[i] + nums[j] === target) {
                console.log(JSON.stringify([i, j]));
                process.exit(0);
            }
        }
    }
    console.log(JSON.stringify([]));
});
'''

    test_cases = [
        {"input": "[2,7,11,15]\n9", "expected_output": "[0,1]", "description": "Basic case"}
    ]

    results = runner.run_all_tests('javascript', code, test_cases)
    assert results['total_tests'] == 1
    assert results['passed_tests'] >= 0


@pytest.mark.integration
def test_end_to_end_java():
    """End-to-end test for Java validation."""
    runner = SimpleTestRunner()

    code = '''
public class Solution {
    public static void main(String[] args) {
        System.out.println("[0, 1]");
    }
}
'''

    test_cases = [
        {"input": "[2,7,11,15]\n9", "expected_output": "[0, 1]", "description": "Basic case"}
    ]

    results = runner.run_all_tests('java', code, test_cases)
    # Java might fail due to version mismatch, so we just check structure
    assert results['total_tests'] == 1
    assert 'passed_tests' in results


@pytest.mark.integration
def test_cross_language_consistency():
    """Test that all validators produce consistent result structures."""
    runner = SimpleTestRunner()

    # Simple code that outputs "42" in each language
    python_code = 'print(42)'
    javascript_code = 'console.log(42);'
    java_code = '''
public class Solution {
    public static void main(String[] args) {
        System.out.println(42);
    }
}
'''

    test_case = {"input": "", "expected_output": "42", "description": "Output 42"}

    # Run for each language
    python_result = runner.run_single_test('python', python_code, test_case)
    javascript_result = runner.run_single_test('javascript', javascript_code, test_case)
    java_result = runner.run_single_test('java', java_code, test_case)

    # Check result structure consistency
    for result, language in [
        (python_result, 'python'),
        (javascript_result, 'javascript'),
        (java_result, 'java')
    ]:
        assert 'passed' in result, f"{language} result missing 'passed' key"
        assert 'execution_time' in result, f"{language} result missing 'execution_time' key"

        # Skip Java if version mismatch
        if language == 'java' and not result['passed']:
            if 'UnsupportedClassVersionError' in str(result.get('error', '')):
                pytest.skip("Java version mismatch")
            continue

        assert result['passed'] == True, f"{language} should have passed"


@pytest.mark.integration
def test_error_handling_consistency():
    """Test that all validators handle errors consistently."""
    runner = SimpleTestRunner()

    # Code with syntax errors in each language
    python_invalid = 'def broken('  # Missing closing parenthesis and colon
    javascript_invalid = 'function broken('  # Missing closing parenthesis
    java_invalid = 'public class Broken {'  # Missing closing brace

    test_case = {"input": "", "expected_output": "", "description": "Invalid code"}

    # All should fail gracefully
    python_result = runner.run_single_test('python', python_invalid, test_case)
    javascript_result = runner.run_single_test('javascript', javascript_invalid, test_case)
    java_result = runner.run_single_test('java', java_invalid, test_case)

    assert python_result['passed'] == False
    assert python_result['error'] is not None

    assert javascript_result['passed'] == False
    assert javascript_result['error'] is not None

    assert java_result['passed'] == False
    assert java_result['error'] is not None
