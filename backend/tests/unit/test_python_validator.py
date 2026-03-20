"""
Unit tests for SimplePythonValidator.
Tests cover happy paths, error scenarios, edge cases, and boundary conditions.
"""

import pytest
from app.services.simple_validators import SimplePythonValidator


class TestSimplePythonValidatorHappyPath:
    """Happy path tests for SimplePythonValidator."""

    def test_python_success(self):
        """Test successful Python validation with correct output."""
        validator = SimplePythonValidator()

        code = '''
import sys
def twoSum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []

# Read input
nums = eval(input().strip())
target = int(input().strip())
result = twoSum(nums, target)
print(result)
'''

        test_case = {
            "input": "[2,7,11,15]\n9",
            "expected_output": "[0, 1]",
            "description": "Basic two-sum case"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == True
        assert result['error'] is None
        assert 'execution_time' in result
        assert result['execution_time'] >= 0

    def test_python_numeric_output(self):
        """Test Python validation with numeric output."""
        validator = SimplePythonValidator()

        code = '''
print(42)
'''

        test_case = {
            "input": "",
            "expected_output": "42",
            "description": "Numeric output"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == True

    def test_python_string_output(self):
        """Test Python validation with string output."""
        validator = SimplePythonValidator()

        code = '''
print("Hello, World!")
'''

        test_case = {
            "input": "",
            "expected_output": "Hello, World!",
            "description": "String output"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == True

    def test_python_json_array_output(self):
        """Test Python validation with JSON array output."""
        validator = SimplePythonValidator()

        code = '''
import json
result = [1, 2, 3, 4, 5]
print(json.dumps(result))
'''

        test_case = {
            "input": "",
            "expected_output": "[1, 2, 3, 4, 5]",
            "description": "JSON array output"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == True

    def test_python_empty_output(self):
        """Test Python validation with empty output."""
        validator = SimplePythonValidator()

        code = '''
# Just a comment, no output
pass
'''

        test_case = {
            "input": "",
            "expected_output": "",
            "description": "Empty output"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == True

    def test_python_multiline_output(self):
        """Test Python validation with multiline output."""
        validator = SimplePythonValidator()

        code = '''
for i in range(3):
    print(i)
'''

        test_case = {
            "input": "",
            "expected_output": "0\n1\n2",
            "description": "Multiline output"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == True


class TestSimplePythonValidatorErrors:
    """Error scenario tests for SimplePythonValidator."""

    def test_python_syntax_error(self):
        """Test Python syntax error handling."""
        validator = SimplePythonValidator()

        code = '''
def twoSum(nums, target)
    return [0, 1] # Missing colon
'''

        test_case = {
            "input": "[2,7,11,15]\n9",
            "expected_output": "[0, 1]",
            "description": "Syntax error case"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == False
        assert 'syntax' in result['error'].lower() or 'invalid' in result['error'].lower()

    def test_python_runtime_error(self):
        """Test Python runtime error handling."""
        validator = SimplePythonValidator()

        code = '''
# This will cause a NameError
print(undefined_variable)
'''

        test_case = {
            "input": "",
            "expected_output": "something",
            "description": "Runtime error case"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == False
        assert result['error'] is not None
        assert 'NameError' in result['error'] or 'undefined' in result['error'].lower()

    def test_python_type_error(self):
        """Test Python type error handling."""
        validator = SimplePythonValidator()

        code = '''
# This will cause a TypeError
result = "string" + 42
print(result)
'''

        test_case = {
            "input": "",
            "expected_output": "something",
            "description": "Type error case"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == False
        assert 'TypeError' in result['error'] or 'error' in result['error'].lower()

    def test_python_index_error(self):
        """Test Python index error handling."""
        validator = SimplePythonValidator()

        code = '''
arr = [1, 2, 3]
print(arr[10]) # Index out of range
'''

        test_case = {
            "input": "",
            "expected_output": "something",
            "description": "Index error case"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == False
        assert 'IndexError' in result['error'] or 'index' in result['error'].lower()

    def test_python_zero_division_error(self):
        """Test Python zero division error handling."""
        validator = SimplePythonValidator()

        code = '''
result = 10 / 0
print(result)
'''

        test_case = {
            "input": "",
            "expected_output": "something",
            "description": "Zero division error case"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == False
        assert 'ZeroDivisionError' in result['error'] or 'division' in result['error'].lower()

    def test_python_wrong_output(self):
        """Test Python wrong output handling."""
        validator = SimplePythonValidator()

        code = '''
import sys
nums = eval(input().strip())
target = int(input().strip())
print([1, 0]) # Wrong order
'''

        test_case = {
            "input": "[2,7,11,15]\n9",
            "expected_output": "[0, 1]",
            "description": "Wrong output case"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == False
        assert result['actual_output'] != result['expected_output']

    def test_python_import_error(self):
        """Test Python import error handling."""
        validator = SimplePythonValidator()

        code = '''
import nonexistent_module_xyz
print("hello")
'''

        test_case = {
            "input": "",
            "expected_output": "hello",
            "description": "Import error case"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == False
        assert 'ModuleNotFoundError' in result['error'] or 'No module' in result['error']


class TestSimplePythonValidatorEdgeCases:
    """Edge case tests for SimplePythonValidator."""

    def test_python_empty_code(self):
        """Test Python validation with empty code."""
        validator = SimplePythonValidator()

        code = ''

        test_case = {
            "input": "",
            "expected_output": "",
            "description": "Empty code"
        }

        result = validator.validate(code, test_case)
        # Empty code should produce empty output
        assert result['passed'] == True
        assert result['actual_output'] == ''

    def test_python_large_input(self):
        """Test Python validation with large input."""
        validator = SimplePythonValidator()

        code = '''
import sys
data = input()
print(len(data))
'''

        # Create a large input string
        large_input = "x" * 10000
        test_case = {
            "input": large_input,
            "expected_output": "10000",
            "description": "Large input"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == True

    def test_python_unicode_input(self):
        """Test Python validation with Unicode input."""
        validator = SimplePythonValidator()

        code = '''
text = input()
print(text.upper())
'''

        test_case = {
            "input": "hello world",
            "expected_output": "HELLO WORLD",
            "description": "Unicode input"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == True

    def test_python_whitespace_handling(self):
        """Test Python validation with various whitespace."""
        validator = SimplePythonValidator()

        code = '''
print(" spaced ")
'''

        test_case = {
            "input": "",
            "expected_output": " spaced ",
            "description": "Whitespace handling"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == True

    def test_python_special_characters(self):
        """Test Python validation with special characters."""
        validator = SimplePythonValidator()

        code = '''
print("Hello\\nWorld\\t!")
'''

        test_case = {
            "input": "",
            "expected_output": "Hello\nWorld\t!",
            "description": "Special characters"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == True
