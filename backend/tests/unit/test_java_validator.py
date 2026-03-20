"""
Unit tests for SimpleJavaValidator.
Tests cover happy paths, error scenarios, and edge cases.
"""

import pytest
from app.services.simple_validators import SimpleJavaValidator


class TestSimpleJavaValidatorHappyPath:
    """Happy path tests for SimpleJavaValidator."""

    def test_java_success(self):
        """Test successful Java validation."""
        validator = SimpleJavaValidator()

        code = '''
public class Solution {
    public static void main(String[] args) {
        System.out.println("[0, 1]");
    }
}
'''

        test_case = {
            "input": "[2,7,11,15]\n9",
            "expected_output": "[0, 1]",
            "description": "Basic two-sum case"
        }

        result = validator.validate(code, test_case)
        # Check if Java is available and compatible
        if not result['passed'] and 'UnsupportedClassVersionError' in str(result.get('error', '')):
            pytest.skip("Java version mismatch - javac and java versions are incompatible")
        assert result['passed'] == True

    def test_java_simple_output(self):
        """Test Java with simple output."""
        validator = SimpleJavaValidator()

        code = '''
public class Solution {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
'''

        test_case = {
            "input": "",
            "expected_output": "Hello, World!",
            "description": "Simple output"
        }

        result = validator.validate(code, test_case)
        if not result['passed'] and 'UnsupportedClassVersionError' in str(result.get('error', '')):
            pytest.skip("Java version mismatch - javac and java versions are incompatible")
        assert result['passed'] == True

    def test_java_numeric_output(self):
        """Test Java with numeric output."""
        validator = SimpleJavaValidator()

        code = '''
public class Solution {
    public static void main(String[] args) {
        System.out.println(42);
    }
}
'''

        test_case = {
            "input": "",
            "expected_output": "42",
            "description": "Numeric output"
        }

        result = validator.validate(code, test_case)
        if not result['passed'] and 'UnsupportedClassVersionError' in str(result.get('error', '')):
            pytest.skip("Java version mismatch - javac and java versions are incompatible")
        assert result['passed'] == True

    def test_java_with_input(self):
        """Test Java with input processing."""
        validator = SimpleJavaValidator()

        code = '''
import java.util.Scanner;
public class Solution {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        int num = scanner.nextInt();
        System.out.println(num * 2);
    }
}
'''

        test_case = {
            "input": "5",
            "expected_output": "10",
            "description": "Input processing"
        }

        result = validator.validate(code, test_case)
        if not result['passed'] and 'UnsupportedClassVersionError' in str(result.get('error', '')):
            pytest.skip("Java version mismatch - javac and java versions are incompatible")
        assert result['passed'] == True

    def test_java_array_output(self):
        """Test Java with array output."""
        validator = SimpleJavaValidator()

        code = '''
import java.util.Arrays;
public class Solution {
    public static void main(String[] args) {
        int[] arr = {1, 2, 3};
        System.out.println(Arrays.toString(arr));
    }
}
'''

        test_case = {
            "input": "",
            "expected_output": "[1, 2, 3]",
            "description": "Array output"
        }

        result = validator.validate(code, test_case)
        if not result['passed'] and 'UnsupportedClassVersionError' in str(result.get('error', '')):
            pytest.skip("Java version mismatch - javac and java versions are incompatible")
        assert result['passed'] == True


class TestSimpleJavaValidatorErrors:
    """Error scenario tests for SimpleJavaValidator."""

    def test_java_compilation_error(self):
        """Test Java compilation error handling."""
        validator = SimpleJavaValidator()

        code = '''
public class Solution {
    public static void main(String[] args) {
        System.out.println([0, 1]) // Invalid array printing
    }
}
'''

        test_case = {
            "input": "[2,7,11,15]\n9",
            "expected_output": "[0,1]",
            "description": "Compilation error case"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == False
        assert 'compilation' in result['error'].lower() or 'error' in result['error'].lower()

    def test_java_missing_semicolon(self):
        """Test Java missing semicolon error."""
        validator = SimpleJavaValidator()

        code = '''
public class Solution {
    public static void main(String[] args) {
        System.out.println("hello") // Missing semicolon
    }
}
'''

        test_case = {
            "input": "",
            "expected_output": "hello",
            "description": "Missing semicolon"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == False
        assert 'compilation' in result['error'].lower() or 'error' in result['error'].lower()

    def test_java_missing_class(self):
        """Test Java missing class error."""
        validator = SimpleJavaValidator()

        code = '''
public static void main(String[] args) {
    System.out.println("hello");
}
'''

        test_case = {
            "input": "",
            "expected_output": "hello",
            "description": "Missing class"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == False

    def test_java_wrong_class_name(self):
        """Test Java with wrong class name."""
        validator = SimpleJavaValidator()

        code = '''
public class WrongName {
    public static void main(String[] args) {
        System.out.println("hello");
    }
}
'''

        test_case = {
            "input": "",
            "expected_output": "hello",
            "description": "Wrong class name"
        }

        result = validator.validate(code, test_case)
        # This should fail because the file is named Solution.java
        assert result['passed'] == False

    def test_java_runtime_exception(self):
        """Test Java runtime exception handling."""
        validator = SimpleJavaValidator()

        code = '''
public class Solution {
    public static void main(String[] args) {
        int[] arr = new int[5];
        System.out.println(arr[10]); // ArrayIndexOutOfBoundsException
    }
}
'''

        test_case = {
            "input": "",
            "expected_output": "something",
            "description": "Runtime exception"
        }

        result = validator.validate(code, test_case)
        if not result['passed'] and 'UnsupportedClassVersionError' in str(result.get('error', '')):
            pytest.skip("Java version mismatch - javac and java versions are incompatible")
        assert result['passed'] == False
        assert 'ArrayIndexOutOfBoundsException' in result['error'] or 'Exception' in result['error']

    def test_java_wrong_output(self):
        """Test Java wrong output handling."""
        validator = SimpleJavaValidator()

        code = '''
public class Solution {
    public static void main(String[] args) {
        System.out.println("wrong output");
    }
}
'''

        test_case = {
            "input": "",
            "expected_output": "expected output",
            "description": "Wrong output"
        }

        result = validator.validate(code, test_case)
        if not result['passed'] and 'UnsupportedClassVersionError' in str(result.get('error', '')):
            pytest.skip("Java version mismatch - javac and java versions are incompatible")
        assert result['passed'] == False
        assert result['actual_output'] == 'wrong output'


class TestSimpleJavaValidatorEdgeCases:
    """Edge case tests for SimpleJavaValidator."""

    def test_java_empty_code(self):
        """Test Java validation with empty code."""
        validator = SimpleJavaValidator()

        code = ''

        test_case = {
            "input": "",
            "expected_output": "",
            "description": "Empty code"
        }

        result = validator.validate(code, test_case)
        assert result['passed'] == False
        assert 'compilation' in result['error'].lower() or 'error' in result['error'].lower()

    def test_java_multiline_output(self):
        """Test Java with multiline output."""
        validator = SimpleJavaValidator()

        code = '''
public class Solution {
    public static void main(String[] args) {
        System.out.println("line1");
        System.out.println("line2");
        System.out.println("line3");
    }
}
'''

        test_case = {
            "input": "",
            "expected_output": "line1\nline2\nline3",
            "description": "Multiline output"
        }

        result = validator.validate(code, test_case)
        if not result['passed'] and 'UnsupportedClassVersionError' in str(result.get('error', '')):
            pytest.skip("Java version mismatch - javac and java versions are incompatible")
        assert result['passed'] == True

    def test_java_special_characters(self):
        """Test Java with special characters."""
        validator = SimpleJavaValidator()

        code = '''
public class Solution {
    public static void main(String[] args) {
        System.out.println("Hello\\nWorld\\t!");
    }
}
'''

        test_case = {
            "input": "",
            "expected_output": "Hello\nWorld\t!",
            "description": "Special characters"
        }

        result = validator.validate(code, test_case)
        if not result['passed'] and 'UnsupportedClassVersionError' in str(result.get('error', '')):
            pytest.skip("Java version mismatch - javac and java versions are incompatible")
        assert result['passed'] == True
