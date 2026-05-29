import pytest
from app.services.piston_service import get_wrapper
from app.services.piston_service import CodeWrapper


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

    def test_self_stripping_removes_self(self):
        wrapper = get_wrapper("python")
        variants = [
            ("def foo(self):\n    pass", "def foo():"),
            ("def foo(self, x):\n    return x", "def foo(x):"),
            ("def foo(self , x):\n    return x", "def foo(x):"),
            ("def foo( self ):\n    pass", "def foo("),  # regex keeps space before ), but strips self
        ]
        for code, expected_sig in variants:
            result = wrapper.wrap(code)
            assert expected_sig in result, f"sig {expected_sig} not found for {code!r}"
            assert "self" not in result.replace("self.", ""), f"self param not stripped for {code!r}"

    def test_string_output_path(self):
        wrapper = get_wrapper("python")
        code = "def greet(n):\n    return 'hi'"
        result = wrapper.wrap(code)
        assert 'result = greet(' in result
        assert "print(result)" in result

    def test_number_output_path(self):
        wrapper = get_wrapper("python")
        code = "def answer():\n    return 42"
        result = wrapper.wrap(code)
        assert 'result = answer(' in result
        assert "print(result)" in result

    def test_json_loads_fallback_in_output(self):
        wrapper = get_wrapper("python")
        code = "def echo(x):\n    return x"
        result = wrapper.wrap(code)
        assert "json.loads(line)" in result
        assert "parsed_line = line" in result

    def test_multiple_function_defs(self):
        wrapper = get_wrapper("python")
        code = "def helper():\n    return 1\n\ndef main(x):\n    return x + helper()"
        result = wrapper.wrap(code)
        # Wrapper regex finds the FIRST def (helper), only wraps around it
        assert "result = helper(" in result
        assert "def helper():" in result
        assert "def main(x):" in result  # second function still preserved in output

    def test_wrapper_bypass_false_positive(self):
        wrapper = get_wrapper("python")
        # bypass triggers on any substring match (even in comments)
        code = 'def f():\n    """has print( inside"""\n    return 1'
        result = wrapper.wrap(code)
        assert result == code  # print( in docstring still bypasses


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

    def test_detects_process_stdout_write(self):
        wrapper = get_wrapper("javascript")
        code = "function f(x) {\n  process.stdout.write(x);\n}"
        result = wrapper.wrap(code)
        assert result == code

    def test_let_declaration_arrow(self):
        wrapper = get_wrapper("javascript")
        code = "let add = (a, b) => a + b;"
        result = wrapper.wrap(code)
        assert "const result = add(" in result
        assert "const fs = require('fs');" in result

    def test_let_declaration_function_expr(self):
        wrapper = get_wrapper("javascript")
        code = "let add = function(a, b) {\n  return a + b;\n};"
        result = wrapper.wrap(code)
        assert "const result = add(" in result

    def test_const_function_expression(self):
        wrapper = get_wrapper("javascript")
        code = "const add = function(a, b) {\n  return a + b;\n};"
        result = wrapper.wrap(code)
        assert "const result = add(" in result

    def test_arrow_function_block_body(self):
        wrapper = get_wrapper("javascript")
        code = "const add = (a, b) => { return a + b; };"
        result = wrapper.wrap(code)
        assert "const result = add(" in result

    def test_default_output_path(self):
        wrapper = get_wrapper("javascript")
        code = "function answer() {\n  return 42;\n}"
        result = wrapper.wrap(code)
        assert "console.log(result)" in result

    def test_runner_structures_present(self):
        wrapper = get_wrapper("javascript")
        code = "function f(x) {\n  return x;\n}"
        result = wrapper.wrap(code)
        assert "readFileSync(0" in result
        assert "split('\\n')" in result
        assert "...args" in result
        assert "process.exit(1)" in result


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

    def test_no_class_fallback(self):
        wrapper = get_wrapper("java")
        code = "public static String greet(String name) {\n  return \"hi\";\n}"
        result = wrapper.wrap(code)
        assert result == code

    def test_zero_param_method(self):
        wrapper = get_wrapper("java")
        code = """public class Solution {
    public static int getAnswer() {
        return 42;
    }
}"""
        result = wrapper.wrap(code)
        assert "java.lang.reflect.Method" in result
        assert "getAnswer" in result

    def test_single_non_string_param(self):
        wrapper = get_wrapper("java")
        code = """public class Solution {
    public static int doubleIt(int x) {
        return x * 2;
    }
}"""
        result = wrapper.wrap(code)
        assert "java.lang.reflect.Method" in result  # falls to reflection path
        assert "__convertArg" in result

    def test_multi_param_boolean_return(self):
        wrapper = get_wrapper("java")
        code = """public class Solution {
    public static boolean and(boolean a, boolean b) {
        return a && b;
    }
}"""
        result = wrapper.wrap(code)
        assert "String.valueOf(result).toLowerCase()" in result
        assert "__toJson" in result

    def test_single_string_non_boolean_return(self):
        wrapper = get_wrapper("java")
        code = """public class Solution {
    public static String greet(String name) {
        return "Hello, " + name;
    }
}"""
        result = wrapper.wrap(code)
        assert "System.out.println(result);" in result
        assert "String.valueOf(result).toLowerCase()" not in result

    def test_multi_param_string_return(self):
        wrapper = get_wrapper("java")
        code = """public class Solution {
    public static String concat(String a, String b) {
        return a + b;
    }
}"""
        result = wrapper.wrap(code)
        assert "System.out.println(result);" in result

    def test_generic_return_type(self):
        wrapper = get_wrapper("java")
        code = """public class Solution {
    public static java.util.List<String> getNames() {
        return java.util.Arrays.asList(\"a\", \"b\");
    }
}"""
        result = wrapper.wrap(code)
        # Regex doesn't match fully qualified types (java.util.List) — returns unchanged
        assert result == code

    def test_array_parameter(self):
        wrapper = get_wrapper("java")
        code = """public class Solution {
    public static int sum(int[] nums) {
        int s = 0;
        for (int n : nums) s += n;
        return s;
    }
}"""
        result = wrapper.wrap(code)
        assert "nums" in result
        assert "__convertArg" in result or "main" in result


class TestGetWrapper:
    def test_returns_python_wrapper(self):
        wrapper = get_wrapper("python")
        from app.services.piston_service import PythonCodeWrapper
        assert isinstance(wrapper, PythonCodeWrapper)

    def test_returns_javascript_wrapper(self):
        wrapper = get_wrapper("javascript")
        from app.services.piston_service import JavaScriptCodeWrapper
        assert isinstance(wrapper, JavaScriptCodeWrapper)

    def test_returns_java_wrapper(self):
        wrapper = get_wrapper("java")
        from app.services.piston_service import JavaCodeWrapper
        assert isinstance(wrapper, JavaCodeWrapper)

    def test_returns_none_for_unknown_language(self):
        wrapper = get_wrapper("brainfuck")
        assert wrapper is None

    def test_get_wrapper_handles_three_languages(self):
        for lang in ["python", "javascript", "java"]:
            assert get_wrapper(lang) is not None

    def test_case_sensitivity(self):
        assert get_wrapper("Python") is None
        assert get_wrapper("JAVA") is None
        assert get_wrapper("JavaScript") is None

    def test_none_input(self):
        assert get_wrapper(None) is None

    def test_empty_string(self):
        assert get_wrapper("") is None
