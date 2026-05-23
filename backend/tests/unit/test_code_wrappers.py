import pytest
from app.adapters.code_wrappers import get_wrapper, WRAPPERS
from app.adapters.code_wrappers.base import CodeWrapper


class TestCodeWrapperABC:
    def test_code_wrapper_is_abstract(self):
        with pytest.raises(TypeError):
            CodeWrapper()


class TestPythonCodeWrapper:
    def test_wraps_bare_function_def(self):
        wrapper = get_wrapper("python")
        code = "def add(a, b):\n    return a + b"
        result = wrapper.wrap(code)
        assert "def add(a, b):" in result
        assert "import sys" in result
        assert "import json" in result
        assert 'result = add(line)' in result or 'result = add("")' in result
        assert "json.dumps(result)" in result

    def test_detects_existing_input(self):
        wrapper = get_wrapper("python")
        code = "def add():\n    return input()"
        result = wrapper.wrap(code)
        assert result == code

    def test_detects_existing_print(self):
        wrapper = get_wrapper("python")
        code = "def add():\n    print(1)"
        result = wrapper.wrap(code)
        assert result == code

    def test_detects_sys_stdin(self):
        wrapper = get_wrapper("python")
        code = "def add():\n    import sys\n    return sys.stdin.read()"
        result = wrapper.wrap(code)
        assert result == code

    def test_returns_code_as_is_when_no_function_match(self):
        wrapper = get_wrapper("python")
        code = "x = 42"
        result = wrapper.wrap(code)
        assert result == code

    def test_bool_output_uses_lowercase(self):
        wrapper = get_wrapper("python")
        code = "def is_even(n):\n    return n % 2 == 0"
        result = wrapper.wrap(code)
        assert "str(result).lower()" in result

    def test_list_output_uses_json(self):
        wrapper = get_wrapper("python")
        code = "def get_items():\n    return [1, 2, 3]"
        result = wrapper.wrap(code)
        assert "json.dumps(result)" in result

    def test_exception_handling_in_runner(self):
        wrapper = get_wrapper("python")
        code = "def fail():\n    raise ValueError('bad')"
        result = wrapper.wrap(code)
        assert "except Exception as e" in result
        assert "sys.exit(1)" in result


class TestJavaScriptCodeWrapper:
    def test_wraps_bare_function(self):
        wrapper = get_wrapper("javascript")
        code = "function add(a, b) {\n  return a + b;\n}"
        result = wrapper.wrap(code)
        assert "const fs = require('fs');" in result
        assert "const result = add(" in result
        assert "console.error(e.message)" in result

    def test_detects_process_stdin(self):
        wrapper = get_wrapper("javascript")
        code = "function add() {\n  return process.stdin.read();\n}"
        result = wrapper.wrap(code)
        assert result == code

    def test_detects_readFileSync(self):
        wrapper = get_wrapper("javascript")
        code = "function add() {\n  return require('fs').readFileSync();\n}"
        result = wrapper.wrap(code)
        assert result == code

    def test_detects_console_log(self):
        wrapper = get_wrapper("javascript")
        code = "function add() {\n  console.log(1);\n}"
        result = wrapper.wrap(code)
        assert result == code

    def test_arrow_function_detection(self):
        wrapper = get_wrapper("javascript")
        code = "const add = (a, b) => a + b;"
        result = wrapper.wrap(code)
        assert "const fs = require('fs');" in result
        assert "const result = add(" in result

    def test_var_function_detection(self):
        wrapper = get_wrapper("javascript")
        code = "var add = function(a, b) {\n  return a + b;\n};"
        result = wrapper.wrap(code)
        assert "const result = add(" in result

    def test_returns_code_as_is_when_no_function_match(self):
        wrapper = get_wrapper("javascript")
        code = "const x = 42;"
        result = wrapper.wrap(code)
        assert result == code

    def test_bool_output(self):
        wrapper = get_wrapper("javascript")
        code = "function isEven(n) {\n  return n % 2 === 0;\n}"
        result = wrapper.wrap(code)
        assert "String(result)" in result

    def test_object_output_uses_json_stringify(self):
        wrapper = get_wrapper("javascript")
        code = "function getItems() {\n  return [1, 2, 3];\n}"
        result = wrapper.wrap(code)
        assert "JSON.stringify(result)" in result


class TestJavaCodeWrapper:
    def test_single_string_param_main(self):
        wrapper = get_wrapper("java")
        code = """public class Solution {
    public static String greet(String name) {
        return "Hello, " + name;
    }
}"""
        result = wrapper.wrap(code)
        assert "public static void main(String[] args)" in result
        assert "String input = sb.toString().trim();" in result
        assert "greet(input)" in result

    def test_multi_param_reflection_main(self):
        wrapper = get_wrapper("java")
        code = """public class Solution {
    public static int add(int a, int b) {
        return a + b;
    }
}"""
        result = wrapper.wrap(code)
        assert "java.lang.reflect.Method" in result
        assert "__convertArg" in result
        assert "__toJson" in result
        assert "__JsonParser" in result

    def test_boolean_return_single_string(self):
        wrapper = get_wrapper("java")
        code = """public class Solution {
    public static boolean isPalindrome(String s) {
        return true;
    }
}"""
        result = wrapper.wrap(code)
        assert "String.valueOf(result).toLowerCase()" in result

    def test_detects_existing_main(self):
        wrapper = get_wrapper("java")
        code = """public class Solution {
    public static void main(String[] args) {
        System.out.println("Hello");
    }
}"""
        result = wrapper.wrap(code)
        assert result == code

    def test_returns_code_as_is_when_no_method_match(self):
        wrapper = get_wrapper("java")
        code = """public class Solution {
    public int x = 42;
}"""
        result = wrapper.wrap(code)
        assert result == code

    def test_helper_code_generated_for_multi_param(self):
        wrapper = get_wrapper("java")
        code = """public class Solution {
    public static int multiply(int a, int b) {
        return a * b;
    }
}"""
        result = wrapper.wrap(code)
        assert "private static Object __convertArg" in result
        assert "private static String __toJson" in result
        assert "private static class __JsonParser" in result


class TestGetWrapper:
    def test_returns_python_wrapper(self):
        wrapper = get_wrapper("python")
        from app.adapters.code_wrappers.python_wrapper import PythonCodeWrapper
        assert isinstance(wrapper, PythonCodeWrapper)

    def test_returns_javascript_wrapper(self):
        wrapper = get_wrapper("javascript")
        from app.adapters.code_wrappers.javascript_wrapper import JavaScriptCodeWrapper
        assert isinstance(wrapper, JavaScriptCodeWrapper)

    def test_returns_java_wrapper(self):
        wrapper = get_wrapper("java")
        from app.adapters.code_wrappers.java_wrapper import JavaCodeWrapper
        assert isinstance(wrapper, JavaCodeWrapper)

    def test_returns_none_for_unknown_language(self):
        wrapper = get_wrapper("brainfuck")
        assert wrapper is None

    def test_wrappers_registry_contains_three_languages(self):
        assert set(WRAPPERS.keys()) == {"python", "javascript", "java"}
