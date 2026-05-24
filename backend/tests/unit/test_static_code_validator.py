import pytest
from app.services.piston_service import StaticCodeValidator


@pytest.fixture
def validator():
    return StaticCodeValidator()


class TestStaticCodeValidator:
    def test_python_clean_code(self, validator):
        result = validator.validate("python", "def add(a, b):\n    return a + b")
        assert result["valid"] is True
        assert result["warnings"] == []
        assert result["errors"] == []

    def test_python_with_input_but_no_sys_stdin(self, validator):
        result = validator.validate("python", "def read():\n    return input()")
        assert len(result["warnings"]) == 1
        assert "sys.stdin" in result["warnings"][0]

    def test_python_with_input_and_sys_stdin_no_warning(self, validator):
        result = validator.validate("python", "import sys\ndef read():\n    return sys.stdin.read()")
        assert result["warnings"] == []

    def test_python_unclosed_parentheses(self, validator):
        result = validator.validate("python", "def hello():\n    print(\n    return 1")
        assert len(result["warnings"]) == 1
        assert "parentheses" in result["warnings"][0]

    def test_javascript_unclosed_parentheses(self, validator):
        result = validator.validate("javascript", "function hello() {\n  console.log(\n  return 1;\n}")
        assert len(result["warnings"]) == 1
        assert "parentheses" in result["warnings"][0]

    def test_javascript_clean_code(self, validator):
        result = validator.validate("javascript", "function add(a, b) {\n  return a + b;\n}")
        assert result["valid"] is True
        assert result["warnings"] == []

    def test_javascript_unclosed_parentheses(self, validator):
        result = validator.validate("javascript", "function hello() {\n  console.log(\n  return 1;\n}")
        assert len(result["warnings"]) == 1
        assert "parentheses" in result["warnings"][0]

    def test_unknown_language_no_warnings(self, validator):
        result = validator.validate("rust", "fn main() {\n    println!(\"hi\");\n}")
        assert result["valid"] is True
        assert result["warnings"] == []

    def test_python_with_print_and_closed_parens_no_warning(self, validator):
        result = validator.validate("python", "def f():\n    print('hello')")
        assert result["warnings"] == []

    def test_javascript_with_closed_console_log_no_warning(self, validator):
        result = validator.validate("javascript", "console.log('hello')")
        assert result["warnings"] == []

    def test_always_returns_valid_true(self, validator):
        result = validator.validate("python", "any code here")
        assert result["valid"] is True
