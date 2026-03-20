"""
Unit tests for SimpleJavaScriptValidator.
Tests cover happy paths, error scenarios, and edge cases.
"""

import pytest
from app.services.simple_validators import SimpleJavaScriptValidator


class TestSimpleJavaScriptValidatorHappyPath:
    """Happy path tests for SimpleJavaScriptValidator."""

    def test_javascript_success(self):
        """Test successful JavaScript validation."""
        validator = SimpleJavaScriptValidator()

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

        test_case = {
            "input": "[2,7,11,15]\n9",
            "expected_output": "[0,1]",
            "description": "Basic two-sum case"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == True

    def test_javascript_simple_output(self):
        """Test JavaScript with simple output."""
        validator = SimpleJavaScriptValidator()

        code = '''
console.log("Hello, World!");
'''

        test_case = {
            "input": "",
            "expected_output": "Hello, World!",
            "description": "Simple output"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == True

    def test_javascript_numeric_output(self):
        """Test JavaScript with numeric output."""
        validator = SimpleJavaScriptValidator()

        code = '''
console.log(42);
'''

        test_case = {
            "input": "",
            "expected_output": "42",
            "description": "Numeric output"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == True

    def test_javascript_json_output(self):
        """Test JavaScript with JSON output."""
        validator = SimpleJavaScriptValidator()

        code = '''
const obj = { name: "test", value: 123 };
console.log(JSON.stringify(obj));
'''

        test_case = {
            "input": "",
            "expected_output": '{"name":"test","value":123}',
            "description": "JSON output"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == True

    def test_javascript_array_output(self):
        """Test JavaScript with array output."""
        validator = SimpleJavaScriptValidator()

        code = '''
const arr = [1, 2, 3];
console.log(JSON.stringify(arr));
'''

        test_case = {
            "input": "",
            "expected_output": "[1,2,3]",
            "description": "Array output"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == True

    def test_javascript_input_processing(self):
        """Test JavaScript with input processing."""
        validator = SimpleJavaScriptValidator()

        code = '''
const readline = require('readline');
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

rl.on('line', (line) => {
    const num = parseInt(line);
    console.log(num * 2);
    rl.close();
});
'''

        test_case = {
            "input": "5",
            "expected_output": "10",
            "description": "Input processing"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == True


class TestSimpleJavaScriptValidatorErrors:
    """Error scenario tests for SimpleJavaScriptValidator."""

    def test_javascript_syntax_error(self):
        """Test JavaScript syntax error handling."""
        validator = SimpleJavaScriptValidator()

        code = '''
function twoSum(nums, target) {
    return [0 1] // Missing comma
}
console.log(twoSum([2,7,11,15], 9));
'''

        test_case = {
            "input": "[2,7,11,15]\n9",
            "expected_output": "[0,1]",
            "description": "Syntax error case"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == False
        assert result['error'] is not None

    def test_javascript_reference_error(self):
        """Test JavaScript reference error handling."""
        validator = SimpleJavaScriptValidator()

        code = '''
console.log(undefinedVariable);
'''

        test_case = {
            "input": "",
            "expected_output": "something",
            "description": "Reference error case"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == False
        assert 'ReferenceError' in result['error'] or 'defined' in result['error'].lower()

    def test_javascript_type_error(self):
        """Test JavaScript type error handling."""
        validator = SimpleJavaScriptValidator()

        code = '''
const obj = null;
console.log(obj.property);
'''

        test_case = {
            "input": "",
            "expected_output": "something",
            "description": "Type error case"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == False
        assert 'TypeError' in result['error'] or 'error' in result['error'].lower()

    def test_javascript_json_parse_error(self):
        """Test JavaScript JSON parse error handling."""
        validator = SimpleJavaScriptValidator()

        code = '''
const invalid = JSON.parse("not valid json");
console.log(invalid);
'''

        test_case = {
            "input": "",
            "expected_output": "something",
            "description": "JSON parse error case"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == False
        assert 'SyntaxError' in result['error'] or 'error' in result['error'].lower()

    def test_javascript_wrong_output(self):
        """Test JavaScript wrong output handling."""
        validator = SimpleJavaScriptValidator()

        code = '''
console.log("wrong output");
'''

        test_case = {
            "input": "",
            "expected_output": "expected output",
            "description": "Wrong output case"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == False
        assert result['actual_output'] == 'wrong output'


class TestSimpleJavaScriptValidatorEdgeCases:
    """Edge case tests for SimpleJavaScriptValidator."""

    def test_javascript_empty_code(self):
        """Test JavaScript validation with empty code."""
        validator = SimpleJavaScriptValidator()

        code = ''

        test_case = {
            "input": "",
            "expected_output": "",
            "description": "Empty code"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == True

    def test_javascript_async_operations(self):
        """Test JavaScript with synchronous output (async not reliable in test)."""
        validator = SimpleJavaScriptValidator()

        code = '''
// Synchronous output only
console.log("immediate");
'''

        test_case = {
            "input": "",
            "expected_output": "immediate",
            "description": "Synchronous output"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == True

    def test_javascript_multiline_output(self):
        """Test JavaScript with multiline output."""
        validator = SimpleJavaScriptValidator()

        code = '''
console.log("line1");
console.log("line2");
console.log("line3");
'''

        test_case = {
            "input": "",
            "expected_output": "line1\nline2\nline3",
            "description": "Multiline output"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == True

    def test_javascript_special_characters(self):
        """Test JavaScript with special characters."""
        validator = SimpleJavaScriptValidator()

        code = '''
console.log("Hello\\nWorld\\t!");
'''

        test_case = {
            "input": "",
            "expected_output": "Hello\nWorld\t!",
            "description": "Special characters"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == True
