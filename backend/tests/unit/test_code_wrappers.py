import pytest
from app.adapters.code_wrappers import get_wrapper, CodeWrapper


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
        assert "result = add(line)" in result or 'result = add("")' in result
        assert "json.dumps(result" in result

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
        assert "json.dumps(result" in result

    def test_exception_handling_in_runner(self):
        wrapper = get_wrapper("python")
        code = "def fail():\n    raise ValueError('bad')"
        result = wrapper.wrap(code)
        assert "except Exception as e" in result
        assert "sys.exit(1)" in result

    def test_none_return_in_place_mutation(self):
        wrapper = get_wrapper("python")
        code = "def rotate(matrix):\n    matrix.reverse()"
        result = wrapper.wrap(code)
        assert "result is None" in result
        assert "parsed_line" in result
        assert "separators" in result
        assert "json.dumps" in result

    def test_self_stripping_removes_self(self):
        wrapper = get_wrapper("python")
        variants = [
            ("def foo(self):\n    pass", "def foo():"),
            ("def foo(self, x):\n    return x", "def foo(x):"),
            ("def foo(self , x):\n    return x", "def foo(x):"),
            (
                "def foo( self ):\n    pass",
                "def foo(",
            ),  # regex keeps space before ), but strips self
        ]
        for code, expected_sig in variants:
            result = wrapper.wrap(code)
            assert expected_sig in result, f"sig {expected_sig} not found for {code!r}"
            assert "self" not in result.replace("self.", ""), (
                f"self param not stripped for {code!r}"
            )

    def test_string_output_path(self):
        wrapper = get_wrapper("python")
        code = "def greet(n):\n    return 'hi'"
        result = wrapper.wrap(code)
        assert "result = greet(" in result
        assert "print(result)" in result

    def test_number_output_path(self):
        wrapper = get_wrapper("python")
        code = "def answer():\n    return 42"
        result = wrapper.wrap(code)
        assert "result = answer(" in result
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
        assert "require('fs').readFileSync(0, 'utf-8')" in result
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
        assert "require('fs').readFileSync(0, 'utf-8')" in result
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
        assert "require('fs').readFileSync(0, 'utf-8')" in result

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

    def test_undefined_return_in_place_mutation(self):
        wrapper = get_wrapper("javascript")
        code = "function rotate(matrix) {\n  matrix.reverse();\n}"
        result = wrapper.wrap(code)
        assert "result === undefined" in result
        assert "args[0]" in result


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
        code = 'public static String greet(String name) {\n  return "hi";\n}'
        result = wrapper.wrap(code)
        assert "public class Solution {" in result
        assert "greet" in result
        assert "main(String[] args)" in result

    def test_no_class_fallback_with_imports(self):
        wrapper = get_wrapper("java")
        code = 'import java.util.*;\npublic static String greet(String name) {\n  return "hi";\n}'
        result = wrapper.wrap(code)
        assert result.startswith("import java.util.*;")
        assert "public class Solution {" in result
        assert "greet" in result
        assert "main(String[] args)" in result

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

    def test_toJson_compact_no_spaces(self):
        wrapper = get_wrapper("java")
        code = """public class Solution {
    public static int[] getArray() {
        return new int[]{1, 2, 3};
    }
}"""
        result = wrapper.wrap(code)
        assert "__toJson" in result
        assert 'sb.append(",")' in result
        assert 'sb.append(", ")' not in result

    def test_toJson_handles_int_array(self):
        wrapper = get_wrapper("java")
        code = """public class Solution {
    public static int[] getArray() {
        return new int[]{1, 2, 3};
    }
}"""
        result = wrapper.wrap(code)
        assert "obj instanceof int[]" in result
        assert "sb.append(arr[i])" in result

    def test_toJson_handles_boolean_array(self):
        wrapper = get_wrapper("java")
        code = """public class Solution {
    public static boolean[] getFlags() {
        return new boolean[]{true, false};
    }
}"""
        result = wrapper.wrap(code)
        assert "obj instanceof boolean[]" in result

    def test_toJson_handles_double_array(self):
        wrapper = get_wrapper("java")
        code = """public class Solution {
    public static double[] getValues() {
        return new double[]{1.5, 2.5};
    }
}"""
        result = wrapper.wrap(code)
        assert "obj instanceof double[]" in result

    def test_toJson_handles_object_array(self):
        wrapper = get_wrapper("java")
        code = """public class Solution {
    public static String[] getStrings() {
        return new String[]{"a", "b"};
    }
}"""
        result = wrapper.wrap(code)
        assert "obj instanceof Object[]" in result

    def test_toJson_handles_map(self):
        wrapper = get_wrapper("java")
        code = """public class Solution {
    public static int sum(int a, int b) {
        return a + b;
    }
}"""
        result = wrapper.wrap(code)
        # __helper_code() is injected for multi-param methods — verify Map branch exists
        assert "obj instanceof java.util.Map" in result

    def test_toJson_handles_collection(self):
        wrapper = get_wrapper("java")
        code = """public class Solution {
    public static int sum(int a, int b) {
        return a + b;
    }
}"""
        result = wrapper.wrap(code)
        # __helper_code() is injected for multi-param methods — verify Collection branch exists
        assert "obj instanceof java.util.Collection" in result

    def test_void_return_in_place_mutation(self):
        wrapper = get_wrapper("java")
        code = """public class Solution {
    public static void rotate(int[][] matrix) {
        for (int i = 0; i < matrix.length; i++)
            for (int j = i + 1; j < matrix[i].length; j++) {
                int tmp = matrix[i][j];
                matrix[i][j] = matrix[j][i];
                matrix[j][i] = tmp;
            }
    }
}"""
        result = wrapper.wrap(code)
        assert "method.getReturnType() == void.class" in result
        assert "callArgs[0]" in result
        assert "__toJson(callArgs[0])" in result


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


# ── Python wrap_with_tests ──────────────────────────────────────────────


class TestPythonWrapWithTests:
    def _wrap(self, code, test_cases):
        from app.adapters.code_wrappers.python_wrapper import PythonCodeWrapper

        return PythonCodeWrapper().wrap_with_tests(code, test_cases)

    def test_single_param_list_return(self):
        code = "def threeSum(nums):\n    return [[-4,-2,6],[-4,0,4]]"
        test_cases = [
            {
                "input": "[-4,-2,-2,-2,0,1,2,2,2,3,3,4,4,6,6]",
                "expected_output": "[[-4,-2,6],[-4,0,4]]",
                "hidden": False,
            },
        ]
        runner = self._wrap(code, test_cases)
        assert "def threeSum(nums):" in runner
        assert 'json.dumps(__out, separators=(",", ":"))' in runner
        assert "__out, __in_val = __run_test(__tc)" in runner
        assert "threeSum(__parsed)" in runner
        assert "hidden" not in runner

    def test_two_param_int_return(self):
        code = "def subarraySum(nums, k):\n    return 1"
        test_cases = [
            {"input": "[1]\n1", "expected_output": "1", "hidden": False},
        ]
        runner = self._wrap(code, test_cases)
        assert "subarraySum(__a, __b)" in runner
        assert "str(__out)" in runner

    def test_inplace_modification(self):
        code = "def rotate(matrix):\n    matrix[:] = [[row[i] for row in reversed(matrix)] for i in range(len(matrix[0]))]"
        test_cases = [
            {"input": "[[1]]", "expected_output": "[[1]]", "hidden": False},
        ]
        runner = self._wrap(code, test_cases)
        assert "if __out is None:" in runner
        assert "json.dumps(__in_val" in runner

    def test_self_stripping(self):
        code = "def solve(self, nums):\n    return len(nums)"
        test_cases = [
            {"input": "[1,2,3]", "expected_output": "3", "hidden": False},
        ]
        runner = self._wrap(code, test_cases)
        assert "(self, nums)" not in runner
        assert "def solve(nums):" in runner

    def test_bool_return(self):
        code = "def isEven(n):\n    return n % 2 == 0"
        test_cases = [
            {"input": "4", "expected_output": "true", "hidden": False},
        ]
        runner = self._wrap(code, test_cases)
        assert "str(__out).lower()" in runner

    def test_exception_during_run(self):
        code = "def fail(n):\n    raise ValueError('bad')"
        test_cases = [
            {"input": "1", "expected_output": "1", "hidden": False},
        ]
        runner = self._wrap(code, test_cases)
        assert "except Exception as __e:" in runner
        assert "__passed = False" in runner

    def test_empty_test_cases(self):
        runner = self._wrap("def f(x):\n    return x", [])
        assert "__test_cases = " in runner
        assert "run_suite()" in runner

    def test_multi_param_spread(self):
        code = "def bypass(a, b, c):\n    return a + b + c"
        test_cases = [
            {"input": "1\n2\n3", "expected_output": "6", "hidden": False},
        ]
        runner = self._wrap(code, test_cases)
        assert "__parsed_args = [json.loads(ln)" in runner
        assert "bypass(*__parsed_args)" in runner
        assert "__parsed_args[0]" in runner

    def test_hidden_not_in_runner(self):
        test_cases = [
            {"input": "1", "expected_output": "1", "hidden": True},
            {"input": "2", "expected_output": "2", "hidden": False},
        ]
        runner = self._wrap("def f(x):\n    return x", test_cases)
        assert '"hidden"' not in runner
        assert "True" not in runner.replace("True", "", 1)

    def test_none_return_vs_string_return(self):
        code = "def greet(name):\n    return 'hello'"
        test_cases = [
            {"input": '"world"', "expected_output": "hello", "hidden": False},
        ]
        runner = self._wrap(code, test_cases)
        assert "if __out is None:" in runner
        assert "str(__out)" in runner


# ── JavaScript wrap_with_tests ──────────────────────────────────────────


class TestJavaScriptWrapWithTests:
    def _wrap(self, code, test_cases):
        from app.adapters.code_wrappers.javascript_wrapper import JavaScriptCodeWrapper

        return JavaScriptCodeWrapper().wrap_with_tests(code, test_cases)

    def test_single_param(self):
        code = "function threeSum(nums) { return [[-4,-2,6],[-4,0,4]]; }"
        test_cases = [
            {
                "input": "[-4,-2,-2,-2,0,1,2,2,2,3,3,4,4,6,6]",
                "expected_output": "[[-4,-2,6],[-4,0,4]]",
                "hidden": False,
            },
        ]
        runner = self._wrap(code, test_cases)
        assert "threeSum(parsed)" in runner
        assert "inVal = parsed" in runner

    def test_multi_param_spread(self):
        code = "function add(a, b, c) { return a + b + c; }"
        test_cases = [
            {"input": "1\n2\n3", "expected_output": "6", "hidden": False},
        ]
        runner = self._wrap(code, test_cases)
        assert "parsedArgs = lines.map" in runner
        assert "add(...parsedArgs)" in runner

    def test_inplace_modification(self):
        code = "function rotate(matrix) { matrix.reverse(); }"
        test_cases = [
            {
                "input": "[[1,2],[3,4]]",
                "expected_output": "[[3,4],[1,2]]",
                "hidden": False,
            },
        ]
        runner = self._wrap(code, test_cases)
        assert "out == null" in runner
        assert "inVal = parsed" in runner

    def test_bool_return(self):
        code = "function isEven(n) { return n % 2 === 0; }"
        test_cases = [
            {"input": "4", "expected_output": "true", "hidden": False},
        ]
        runner = self._wrap(code, test_cases)
        assert "typeof out === 'boolean'" in runner
        assert "String(out)" in runner

    def test_arrow_function(self):
        code = "const threeSum = (nums) => { return []; }"
        test_cases = [
            {"input": "[]", "expected_output": "[]", "hidden": False},
        ]
        runner = self._wrap(code, test_cases)
        assert "threeSum(parsed)" in runner

    def test_no_fs_require(self):
        code = "function f(x) { return x; }"
        test_cases = [{"input": "1", "expected_output": "1", "hidden": False}]
        runner = self._wrap(code, test_cases)
        assert "require('fs')" not in runner
        assert 'require("fs")' not in runner

    def test_uses_process_stdout_write(self):
        code = "function f(x) { return x; }"
        test_cases = [{"input": "1", "expected_output": "1", "hidden": False}]
        runner = self._wrap(code, test_cases)
        assert "process.stdout.write" in runner


# ── Java wrap_with_tests ────────────────────────────────────────────────


class TestJavaWrapWithTests:
    def _wrap(self, code, test_cases):
        from app.adapters.code_wrappers.java_wrapper import JavaCodeWrapper

        return JavaCodeWrapper().wrap_with_tests(code, test_cases)

    def test_single_string_param(self):
        code = """public class Solution {
    public static String greet(String name) {
        return "Hello, " + name;
    }
}"""
        test_cases = [
            {"input": '"world"', "expected_output": "Hello, world", "hidden": False},
        ]
        runner = self._wrap(code, test_cases)
        assert "import java.util.*" in runner
        assert "import java.lang.reflect.*" in runner
        assert "public class Solution" in runner

    def test_generates_valid_structure(self):
        code = """public class Solution {
    public static int add(int a, int b) {
        return a + b;
    }
}"""
        test_cases = [
            {"input": "1\n2", "expected_output": "3", "hidden": False},
        ]
        runner = self._wrap(code, test_cases)
        assert "@@SUITE_RESULT@@" in runner
        assert "parseTcArray" in runner
        assert "toJson(results)" in runner

    def test_uses_toJson_instead_of_arrays_tostring(self):
        code = """public class Solution {
    public static int[] searchRange(int[] nums, int target) {
        return new int[]{-1, -1};
    }
}"""
        test_cases = [
            {"input": "[]\n0", "expected_output": "[-1,-1]", "hidden": False},
        ]
        runner = self._wrap(code, test_cases)
        assert "actual = toJson(result)" in runner
        assert "Arrays.toString" not in runner

    def test_toJson_handles_int_array(self):
        code = """public class Solution {
    public static int[] nums(int[] a) { return a; }
}"""
        test_cases = [{"input": "[1,2,3]", "expected_output": "[1,2,3]"}]
        runner = self._wrap(code, test_cases)
        assert "instanceof int[]" in runner
        assert "sb.append(arr[i])" in runner
        assert 'sb.append(",")' in runner

    def test_toJson_handles_boolean_array(self):
        code = """public class Solution {
    public static boolean[] bools(boolean[] a) { return a; }
}"""
        test_cases = [{"input": "[true,false]", "expected_output": "[true,false]"}]
        runner = self._wrap(code, test_cases)
        assert "instanceof boolean[]" in runner

    def test_toJson_handles_double_array(self):
        code = """public class Solution {
    public static double[] doubles(double[] a) { return a; }
}"""
        test_cases = [{"input": "[1.5,2.5]", "expected_output": "[1.5,2.5]"}]
        runner = self._wrap(code, test_cases)
        assert "instanceof double[]" in runner

    def test_toJson_handles_object_array(self):
        code = """public class Solution {
    public static String[] strs(String[] a) { return a; }
}"""
        test_cases = [{"input": '"a"\n"b"', "expected_output": '["a","b"]'}]
        runner = self._wrap(code, test_cases)
        assert "instanceof Object[]" in runner
        assert "toJson(arr[i])" in runner


class TestRCodeWrapper:
    def _wrap(self, code, test_cases):
        wrapper = get_wrapper("r")
        return wrapper.wrap_with_tests(code, test_cases)

    def test_wrap_passes_script_through(self):
        wrapper = get_wrapper("r")
        code = "x <- 1\ncat(x)\n"
        assert wrapper.wrap(code) == code

    def test_suite_runner_embeds_test_cases(self):
        code = "solve <- function(input) {\n    as.character(nchar(input))\n}"
        test_cases = [
            {"input": "hello", "expected_output": "5"},
            {"input": "R\nis\nfun", "expected_output": "8"},
        ]
        runner = self._wrap(code, test_cases)
        assert "solve <- function(input) {" in runner
        assert "run_suite <- function()" in runner
        assert "index = 1" in runner
        assert "index = 2" in runner
        assert "expected = '5'" in runner
        assert "@@SUITE_RESULT@@" in runner

    def test_suite_runner_escapes_input(self):
        code = "solve <- function(input) input"
        test_cases = [{"input": "it's \"quoted\"", "expected_output": "ok"}]
        runner = self._wrap(code, test_cases)
        assert "\\\\'" in runner or "it\\'s" in runner
        assert "run_suite <- function()" in runner

    def test_suite_runner_uses_last_function_as_entry(self):
        code = """helper <- function(x) { x * 2 }
main <- function(input) {
    as.character(helper(as.numeric(input)))
}"""
        test_cases = [{"input": "21", "expected_output": "42"}]
        runner = self._wrap(code, test_cases)
        assert "main(t$input)" in runner
        assert "helper(t$input)" not in runner


class TestBashCodeWrapper:
    def _wrap(self, code, test_cases):
        wrapper = get_wrapper("bash")
        return wrapper.wrap_with_tests(code, test_cases)

    def test_wrap_passes_script_through(self):
        wrapper = get_wrapper("bash")
        code = "echo hello\n"
        assert wrapper.wrap(code) == code

    def test_suite_runner_embeds_solution_and_cases(self):
        code = "echo hello"
        test_cases = [{"input": "", "expected_output": "hello"}]
        runner = self._wrap(code, test_cases)
        assert "cat > /tmp/solution.sh" in runner
        assert "CODEACH_SOLUTION_EOF_9x7" in runner
        assert "@@SUITE_RESULT@@" in runner
        assert "TOTAL=1" in runner

    def test_suite_runner_base64_encodes_inputs(self):
        code = "cat"
        test_cases = [{"input": "multi\nline\ninput", "expected_output": "multi"}]
        runner = self._wrap(code, test_cases)
        assert "IN_B64=(" in runner
        assert "base64 -d" in runner
