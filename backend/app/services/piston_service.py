"""Piston code execution — single deep module.

Encapsulates code wrapping per language, execution via Piston API,
result formatting, and static validation.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

import httpx
from fastapi import HTTPException

from app.ports.code_executor import CodeExecutor, ExecutionResult, TestCaseResult

logger = logging.getLogger(__name__)


# ── Code Wrappers (per-language) ────────────────────────────────────────

class CodeWrapper(ABC):
    @abstractmethod
    def wrap(self, code: str) -> str: ...


class PythonCodeWrapper(CodeWrapper):
    def wrap(self, code: str) -> str:
        if "input(" in code or "sys.stdin" in code or "print(" in code:
            return code
        # Strip 'self' from the first parameter if present
        code = re.sub(r'(\(\s*)self\s*,?\s*', r'\1', code)
        
        func_match = re.search(r"def\s+(\w+)\s*\(", code)
        if not func_match:
            return code
        func_name = func_match.group(1)
        runner = f"""
import sys
import json

{code}

try:
    line = sys.stdin.read().strip()
    if line:
        try:
            parsed_line = json.loads(line)
        except:
            parsed_line = line
        result = {func_name}(parsed_line)
    else:
        result = {func_name}("")
    if isinstance(result, list):
        print(json.dumps(result))
    elif isinstance(result, bool):
        print(str(result).lower())
    elif isinstance(result, str):
        print(result)
    else:
        print(result)
except Exception as e:
    print(str(e), file=sys.stderr)
    sys.exit(1)
"""
        return runner.strip()


class JavaScriptCodeWrapper(CodeWrapper):
    def wrap(self, code: str) -> str:
        if "process.stdin" in code or "readFileSync" in code or "console.log" in code:
            return code
        func_match = re.search(r"function\s+(\w+)\s*\(", code)
        if not func_match:
            func_match = re.search(r"(?:const|let|var)\s+(\w+)\s*=\s*(?:function|\(.*\)\s*=>)", code)
        if not func_match:
            return code
        func_name = func_match.group(1)
        runner = f"""
const fs = require('fs');

{code}

try {{
    const input = fs.readFileSync(0, 'utf-8').trim();
    const lines = input.split('\\n');
    const args = lines.map(line => {{
        try {{ return JSON.parse(line); }} catch {{ return line; }}
    }});
    const result = {func_name}(...args);
    if (typeof result === 'boolean') {{
        console.log(String(result));
    }} else if (typeof result === 'object') {{
        console.log(JSON.stringify(result));
    }} else {{
        console.log(result);
    }}
}} catch (e) {{
    console.error(e.message);
    process.exit(1);
}}
"""
        return runner.strip()


class JavaCodeWrapper(CodeWrapper):
    def wrap(self, code: str) -> str:
        if "public static void main" in code:
            return code
        method_pattern = r'public\s+static\s+([\w<>[\],\s?]+)\s+(\w+)\s*\(([^)]*)\)'
        method_match = re.search(method_pattern, code)
        if not method_match:
            return code
        method_name = method_match.group(2)
        return_type = method_match.group(1).strip()
        params_str = method_match.group(3).strip()
        param_count = len([p for p in params_str.split(",") if p.strip()])
        first_param_type = params_str.split(",")[0].strip().split(" ")[0] if params_str else ""
        is_single_string = param_count == 1 and first_param_type == "String"

        if is_single_string:
            main_code = self._build_single_string_main(method_name, return_type)
            helper_code = ""
        else:
            main_code = self._build_multi_param_main(method_name)
            helper_code = self._helper_code()

        insertion = "\n" + main_code + "\n" + (helper_code + "\n" if not is_single_string else "")
        class_match = re.search(r"(public\s+class\s+\w+\s*\{)", code)
        if not class_match:
            return code
        insertion_point = class_match.end(1)
        return code[:insertion_point] + insertion + code[insertion_point:]

    def _build_single_string_main(self, method_name: str, return_type: str) -> str:
        output_line = ('System.out.println(String.valueOf(result).toLowerCase());' if return_type == "boolean" else 'System.out.println(result);')
        return "\n".join([
            "    public static void main(String[] args) throws Exception {",
            "        java.io.BufferedReader reader = new java.io.BufferedReader(new java.io.InputStreamReader(System.in));",
            "        StringBuilder sb = new StringBuilder();",
            "        String line;",
            "        while ((line = reader.readLine()) != null) {",
            '            if (sb.length() > 0) sb.append("\\n");',
            "            sb.append(line);",
            "        }",
            "        String input = sb.toString().trim();",
            '        if (input.startsWith("\\"") && input.endsWith("\\"") && input.length() >= 2) {',
            "            input = input.substring(1, input.length() - 1);",
            "        }",
            f"        {return_type} result = {method_name}(input);",
            f"        {output_line}",
            "    }",
        ])

    def _build_multi_param_main(self, method_name: str) -> str:
        return "\n".join([
            "    public static void main(String[] args) throws Exception {",
            "        java.io.BufferedReader reader = new java.io.BufferedReader(new java.io.InputStreamReader(System.in));",
            "        StringBuilder sb = new StringBuilder();",
            "        String line;",
            "        while ((line = reader.readLine()) != null) {",
            '            if (sb.length() > 0) sb.append("\\n");',
            "            sb.append(line);",
            "        }",
            "        String input = sb.toString().trim();",
            '        String[] lines = input.isEmpty() ? new String[]{""} : input.split("\\n", -1);',
            "        java.util.List<Object> parsedArgs = new java.util.ArrayList<>();",
            "        for (String l : lines) {",
            "            l = l.trim();",
            "            if (l.isEmpty()) { parsedArgs.add(\"\"); }",
            "            else {",
            "                try { parsedArgs.add(__JsonParser.parse(l)); }",
            "                catch (Exception e) { parsedArgs.add(l); }",
            "            }",
            "        }",
            "        java.lang.reflect.Method method = null;",
            "        for (java.lang.reflect.Method m : Solution.class.getDeclaredMethods()) {",
            f'            if (m.getName().equals("{method_name}")) {{ method = m; break; }}',
            "        }",
            "        if (method == null) throw new NoSuchMethodException(\"" + method_name + "\");",
            "        java.lang.reflect.Parameter[] paramTypes = method.getParameters();",
            "        Object[] callArgs = new Object[parsedArgs.size()];",
            "        for (int i = 0; i < parsedArgs.size() && i < paramTypes.length; i++) {",
            "            callArgs[i] = __convertArg(parsedArgs.get(i), paramTypes[i].getType());",
            "        }",
            "        Object result = method.invoke(null, callArgs);",
            "        if (result instanceof Boolean) { System.out.println(String.valueOf(result).toLowerCase()); }",
            "        else if (result instanceof String) { System.out.println(result); }",
            "        else { System.out.println(__toJson(result)); }",
            "    }",
        ])

    def _helper_code(self) -> str:
        return """
    private static Object __convertArg(Object arg, Class<?> targetType) {
        if (arg == null) return null;
        if (targetType == String.class) return String.valueOf(arg);
        if (targetType == int.class || targetType == Integer.class) {
            if (arg instanceof Number) return ((Number) arg).intValue();
            return Integer.parseInt(arg.toString());
        }
        if (targetType == double.class || targetType == Double.class) {
            if (arg instanceof Number) return ((Number) arg).doubleValue();
            return Double.parseDouble(arg.toString());
        }
        if (targetType == boolean.class || targetType == Boolean.class) {
            if (arg instanceof Boolean) return arg;
            return Boolean.parseBoolean(arg.toString());
        }
        if (targetType == long.class || targetType == Long.class) {
            if (arg instanceof Number) return ((Number) arg).longValue();
            return Long.parseLong(arg.toString());
        }
        return arg;
    }
    private static String __toJson(Object obj) {
        if (obj == null) return "null";
        if (obj instanceof Boolean) return String.valueOf(obj).toLowerCase();
        if (obj instanceof Number) return String.valueOf(obj);
        if (obj instanceof String) return "\\"" + ((String) obj).replace("\\\\", "\\\\\\\\").replace("\\"", "\\\\\\"") + "\\"";
        if (obj instanceof java.util.List) {
            java.util.List<?> list = (java.util.List<?>) obj;
            StringBuilder sb = new StringBuilder("["); for (int i = 0; i < list.size(); i++) { if (i > 0) sb.append(", "); sb.append(__toJson(list.get(i))); } sb.append("]");
            return sb.toString();
        }
        return String.valueOf(obj);
    }
    private static class __JsonParser {
        private String json; private int pos;
        __JsonParser(String json) { this.json = json; this.pos = 0; }
        Object parse() {
            skipWs(); if (pos >= json.length()) return null;
            char c = json.charAt(pos);
            if (c == '"') return parseStr();
            if (c == '{') return parseObj();
            if (c == '[') return parseArr();
            if (c == 't' || c == 'f') { boolean v = json.startsWith("true", pos); pos += v ? 4 : 5; return v; }
            if (c == 'n') { pos += 4; return null; }
            return parseNum();
        }
        String parseStr() { pos++; StringBuilder sb = new StringBuilder(); while (pos < json.length()) { char c = json.charAt(pos); if (c == '"') { pos++; break; } if (c == '\\\\' && pos + 1 < json.length()) { pos++; char n = json.charAt(pos); if (n == '"') sb.append('"'); else if (n == '\\\\') sb.append('\\\\'); else if (n == 'n') sb.append('\\n'); else if (n == 'r') sb.append('\\r'); else if (n == 't') sb.append('\\t'); else sb.append(n); } else { sb.append(c); } pos++; } return sb.toString(); }
        Number parseNum() {
            int start = pos; if (pos < json.length() && json.charAt(pos) == '-') pos++;
            while (pos < json.length() && Character.isDigit(json.charAt(pos))) pos++;
            boolean isDbl = false;
            if (pos < json.length() && json.charAt(pos) == '.') { isDbl = true; pos++; while (pos < json.length() && Character.isDigit(json.charAt(pos))) pos++; }
            if (pos < json.length() && (json.charAt(pos) == 'e' || json.charAt(pos) == 'E')) { isDbl = true; pos++; if (pos < json.length() && (json.charAt(pos) == '+' || json.charAt(pos) == '-')) pos++; while (pos < json.length() && Character.isDigit(json.charAt(pos))) pos++; }
            String ns = json.substring(start, pos);
            if (isDbl) return Double.parseDouble(ns);
            long v = Long.parseLong(ns); return (v >= Integer.MIN_VALUE && v <= Integer.MAX_VALUE) ? (int) v : v;
        }
        java.util.List<Object> parseArr() { pos++; java.util.List<Object> list = new java.util.ArrayList<>(); skipWs(); if (pos < json.length() && json.charAt(pos) == ']') { pos++; return list; } while (pos < json.length()) { list.add(parse()); skipWs(); if (pos < json.length() && json.charAt(pos) == ']') { pos++; break; } if (pos < json.length() && json.charAt(pos) == ',') { pos++; skipWs(); } } return list; }
        java.util.Map<String, Object> parseObj() { pos++; java.util.Map<String, Object> map = new java.util.LinkedHashMap<>(); skipWs(); if (pos < json.length() && json.charAt(pos) == '}') { pos++; return map; } while (pos < json.length()) { skipWs(); String key = (String) parse(); skipWs(); if (pos < json.length() && json.charAt(pos) == ':') pos++; skipWs(); map.put(key, parse()); skipWs(); if (pos < json.length() && json.charAt(pos) == '}') { pos++; break; } if (pos < json.length() && json.charAt(pos) == ',') { pos++; skipWs(); } } return map; }
        void skipWs() { while (pos < json.length() && Character.isWhitespace(json.charAt(pos))) pos++; }
        static Object parse(String s) { return new __JsonParser(s).parse(); }
    }
""".lstrip("\n")


_WRAPPERS: Dict[str, CodeWrapper] = {
    "python": PythonCodeWrapper(),
    "javascript": JavaScriptCodeWrapper(),
    "java": JavaCodeWrapper(),
}


def get_wrapper(language: str) -> Optional[CodeWrapper]:
    return _WRAPPERS.get(language)


# ── Execution Result Formatter ─────────────────────────────────────────

class ExecutionResultFormatter:
    def format(self, result: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.info(f"Piston API response: {json.dumps(result, indent=2)}")
        except Exception as e:
            logger.warning(f"Could not log full response: {e}")

        run_info = result.get("run", {})
        processed = {
            "stdout": run_info.get("stdout", ""),
            "stderr": run_info.get("stderr", ""),
            "exit_code": run_info.get("code", 1),
            "signal": run_info.get("signal", None),
            "execution_time": run_info.get("wall_time", run_info.get("time", None)),
            "memory_usage": run_info.get("memory", None),
            "language": result.get("language", ""),
            "version": result.get("version", ""),
        }

        try:
            stdout_preview = processed["stdout"][:100] if processed["stdout"] else ""
            logger.info(f"Processed execution result: stdout='{stdout_preview}...', exit_code={processed['exit_code']}")
        except Exception as e:
            logger.warning(f"Could not log processed result: {e}")

        stderr = processed["stderr"]
        if stderr:
            lines = stderr.split("\n")
            filtered_lines = [line for line in lines if not any(
                warning in line.lower() for warning in ["warning", "deprecated", "note:", "#warning"]
            )]
            processed["stderr"] = "\n".join(filtered_lines).strip()

        return processed


# ── Static Code Validator ──────────────────────────────────────────────

class StaticCodeValidator:
    def validate(self, language: str, code: str) -> dict:
        warnings = []
        if language == "python":
            if "input(" in code and "import sys" not in code:
                warnings.append("Consider using sys.stdin for better compatibility")
            if "print(" in code and not code.strip().endswith(")"):
                warnings.append("Check for unclosed parentheses")
        elif language == "javascript":
            if "console.log(" in code and not code.strip().endswith(")"):
                warnings.append("Check for unclosed parentheses")
        return {"valid": True, "warnings": warnings, "errors": []}


# ── File Extension Lookup ──────────────────────────────────────────────

_FILE_EXTENSIONS = {
    "python": "py", "javascript": "js", "java": "java",
    "cpp": "cpp", "c": "c", "go": "go", "rust": "rs", "typescript": "ts",
}


def _get_file_extension(language: str) -> str:
    return _FILE_EXTENSIONS.get(language, "txt")


# ── Piston Service ─────────────────────────────────────────────────────

class PistonService(CodeExecutor):
    """Executes code via Piston (Docker) sandbox. This is the deep module
    — wrapping, formatting, and validation are internal details."""

    # Piston API uses different language names than our internal names
    _PISTON_LANGUAGE_MAP = {
        "c": "gcc",
    }

    def __init__(self):
        self.base_url = os.environ.get("PISTON_API_URL", "http://localhost:2000/api/v2")
        self.timeout = 30.0
        self.formatter = ExecutionResultFormatter()
        self.validator = StaticCodeValidator()
        self.languages = {
            "python": {"version": "3.10.0", "aliases": ["py", "python3"]},
            "javascript": {"version": "18.15.0", "aliases": ["js", "node"]},
            "java": {"version": "15.0.2", "aliases": ["java"]},
            "cpp": {"version": "10.2.0", "aliases": ["c++", "cpp"]},
            "c": {"version": "10.2.0", "aliases": ["c"]},
            "go": {"version": "1.16.2", "aliases": ["golang"]},
            "rust": {"version": "1.68.2", "aliases": ["rs", "rust"]},
            "typescript": {"version": "5.0.2", "aliases": ["ts", "typescript"]},
        }

    async def execute(
        self, language: str, code: str, stdin: str = "", version: Optional[str] = None
    ) -> ExecutionResult:
        if language not in self.languages:
            raise HTTPException(status_code=400, detail=f"Unsupported language: {language}. Supported: {list(self.languages.keys())}")

        lang_config = self.languages[language]
        version_to_use = version or lang_config["version"]
        wrapper = get_wrapper(language)
        code_to_run = wrapper.wrap(code) if wrapper else code

        piston_language = self._PISTON_LANGUAGE_MAP.get(language, language)

        payload = {
            "language": piston_language,
            "version": version_to_use,
            "files": [{"name": f"main.{_get_file_extension(language)}", "content": code_to_run}],
            "stdin": stdin, "args": [],
            "compile_timeout": 10000, "run_timeout": 3000,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/execute", json=payload, headers={"Content-Type": "application/json"})
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail=f"Piston API error: {response.text}")
                raw = response.json()
                processed = self.formatter.format(raw)
                return ExecutionResult(**processed)
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Code execution timeout")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error executing code: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Internal server error during code execution: {str(e)}")

    async def get_runtimes(self) -> List[dict]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/runtimes")
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail="Failed to fetch runtimes")
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching runtimes: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch available runtimes")

    # ── Batch Test Suite Execution ────────────────────────────────────────

    async def evaluate_suite(
        self,
        language: str,
        code: str,
        test_cases: List[dict],
    ) -> List[TestCaseResult]:
        """Execute all test cases in a single Piston request using a generated runner."""
        if language not in self.languages:
            raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")
        if not test_cases:
            return []

        runner_code = self._build_suite_runner(language, code, test_cases)
        exec_result = await self.execute(
            language=language,
            code=runner_code,
            stdin="",
        )

        return self._parse_suite_output(exec_result, test_cases)

    def _build_suite_runner(
        self, language: str, user_code: str, test_cases: List[dict]
    ) -> str:
        if language == "python":
            return self._python_suite_runner(user_code, test_cases)
        elif language == "javascript":
            return self._javascript_suite_runner(user_code, test_cases)
        elif language == "java":
            return self._java_suite_runner(user_code, test_cases)
        # Fallback: run individually (shouldn't normally reach here)
        return user_code

    # ── Python suite runner ───────────────────────────────────────────────

    def _python_suite_runner(self, user_code: str, test_cases: List[dict]) -> str:
        # Strip 'self' from the first parameter if present
        user_code = re.sub(r'(\(\s*)self\s*,?\s*', r'\1', user_code)

        tc_clean = [
            {"input": tc["input"], "expected": tc["expected_output"], "index": i + 1}
            for i, tc in enumerate(test_cases)
        ]
        tc_repr = repr(tc_clean)
        
        func_match = re.search(r"def\s+(\w+)\s*\(", user_code)
        func_name = func_match.group(1) if func_match else "solve"
        
        return f"""import sys, json

{user_code}

def run_suite():
    __test_cases = {tc_repr}
    __results = []
    
    def __run_test(__tc):
        __inp = __tc["input"]
        try:
            __lines = __inp.split("\\n") if __inp else [""]
            if len(__lines) == 1:
                try:
                    __parsed = json.loads(__lines[0])
                except Exception:
                    __parsed = __lines[0]
                return {func_name}(__parsed)
            elif len(__lines) == 2:
                try:
                    __a = json.loads(__lines[0])
                    __b = json.loads(__lines[1]) if (__lines[1].strip().lstrip("-").isdigit() or __lines[1].strip().startswith("[")) else __lines[1]
                except Exception:
                    __a, __b = __lines[0], __lines[1]
                return {func_name}(__a, __b)
            else:
                return {func_name}(__lines)
        except Exception as e:
            raise e

    for __tc in __test_cases:
        __idx = __tc["index"]
        __exp = __tc["expected"]
        try:
            __out = __run_test(__tc)
            if isinstance(__out, list):
                __actual = json.dumps(__out, separators=(",", ":"))
            elif isinstance(__out, bool):
                __actual = str(__out).lower()
            else:
                __actual = str(__out)
            __passed = __actual.strip() == __exp.strip()
        except Exception as __e:
            __actual = str(__e)
            __passed = False
        __results.append({{"index": __idx, "passed": __passed, "actual": __actual}})

    print("@@SUITE_RESULT@@" + json.dumps(__results, separators=(",", ":")) + "@@SUITE_RESULT@@")
    sys.stdout.flush()

if __name__ == "__main__":
    run_suite()
"""

    # ── JavaScript suite runner ───────────────────────────────────────────

    def _javascript_suite_runner(self, user_code: str, test_cases: List[dict]) -> str:
        tc_json = json.dumps(
            [{"input": tc["input"], "expected": tc["expected_output"], "hidden": tc.get("hidden", False), "index": i + 1}
             for i, tc in enumerate(test_cases)]
        )
        
        # Extract function name
        func_match = re.search(r"function\s+(\w+)\s*\(", user_code)
        if not func_match:
            func_match = re.search(r"(?:const|let|var)\s+(\w+)\s*=\s*(?:function|\(.*\)\s*=>)", user_code)
        func_name = func_match.group(1) if func_match else "solve"
        
        return f"""const fs = require('fs');

{user_code}

const testCases = {tc_json};
const results = [];

for (const tc of testCases) {{
    let actual = "";
    let passed = false;
    try {{
        const lines = tc.input ? tc.input.split('\\n') : [""];
        let out;
        if (lines.length === 1) {{
            let parsed;
            try {{ parsed = JSON.parse(lines[0]); }} catch {{ parsed = lines[0]; }}
            out = {func_name}(parsed);
        }} else if (lines.length === 2) {{
            let a, b;
            try {{ a = JSON.parse(lines[0]); }} catch {{ a = lines[0]; }}
            try {{ b = JSON.parse(lines[1]); }} catch {{ b = lines[1]; }}
            out = {func_name}(a, b);
        }} else {{
            out = {func_name}(lines);
        }}
        if (typeof out === 'boolean') {{
            actual = String(out);
        }} else if (typeof out === 'object') {{
            actual = JSON.stringify(out);
        }} else {{
            actual = String(out);
        }}
        passed = actual.trim() === tc.expected.trim();
    }} catch (e) {{
        actual = "";
        passed = false;
    }}
    results.push({{ index: tc.index, passed, actual, hidden: tc.hidden }});
}}

process.stdout.write('@@SUITE_RESULT@@' + JSON.stringify(results) + '@@SUITE_RESULT@@');
"""

    # ── Java suite runner ─────────────────────────────────────────────────

    def _java_suite_runner(self, user_code: str, test_cases: List[dict]) -> str:
        tc_json = json.dumps(
            [{"input": tc["input"], "expected": tc["expected_output"], "hidden": tc.get("hidden", False), "index": i + 1}]
            for i, tc in enumerate(test_cases)
        )
        return (
            "import java.util.*;\n"
            "import java.lang.reflect.*;\n"
            "\n"
            "public class Solution {\n"
            + user_code + "\n"
            "\n"
            "    public static void main(String[] args) throws Exception {\n"
            '        String tcJson = "' + tc_json.replace('"', '\\"') + '";\n'
            "        List<Map<String, Object>> testCases = parseTcArray(tcJson);\n"
            "        List<Map<String, Object>> results = new ArrayList<>();\n"
            "\n"
            "        for (Map<String, Object> tc : testCases) {\n"
            '            int idx = ((Number) tc.get("index")).intValue();\n'
            '            String input = (String) tc.get("input");\n'
            '            String expected = (String) tc.get("expected");\n'
            '            boolean hidden = (Boolean) tc.get("hidden");\n'
            '            String actual = "";\n'
            "            boolean passed = false;\n"
            "            try {\n"
            '                String[] lines = input.isEmpty() ? new String[]{""} : input.split("\\n", -1);\n'
            "                Object result;\n"
            "                if (lines.length == 1) {\n"
            "                    result = callSolution(lines[0].trim());\n"
            "                } else if (lines.length == 2) {\n"
            "                    result = callSolution(lines[0].trim(), lines[1].trim());\n"
            "                } else {\n"
            "                    result = callSolution(lines);\n"
            "                }\n"
            '                actual = result == null ? "null" : result.toString();\n'
            "                if (result instanceof boolean[]) actual = Arrays.toString((boolean[]) result);\n"
            "                else if (result instanceof int[]) actual = Arrays.toString((int[]) result);\n"
            "                else if (result instanceof double[]) actual = Arrays.toString((double[]) result);\n"
            "                else if (result instanceof Object[]) actual = Arrays.toString((Object[]) result);\n"
            "                passed = actual.trim().equals(expected.trim());\n"
            "            } catch (Exception e) {\n"
            '                actual = "";\n'
            "                passed = false;\n"
            "            }\n"
            "            Map<String, Object> r = new LinkedHashMap<>();\n"
            '            r.put("index", idx); r.put("passed", passed); r.put("actual", actual); r.put("hidden", hidden);\n'
            "            results.add(r);\n"
            "        }\n"
            '        System.out.print("@@SUITE_RESULT@@" + toJson(results) + "@@SUITE_RESULT@@");\n'
            "    }\n"
            "\n"
            "    static Object callSolution(Object... args) throws Exception {\n"
            "        Class<?> clazz = Solution.class;\n"
            "        for (Method m : clazz.getDeclaredMethods()) {\n"
            '            if (m.getName().equals("solve") && m.getParameterCount() == args.length) {\n'
            "                Object[] converted = new Object[args.length];\n"
            "                Class<?>[] types = m.getParameterTypes();\n"
            "                for (int i = 0; i < args.length; i++) {\n"
            "                    converted[i] = convert(args[i], types[i]);\n"
            "                }\n"
            "                m.setAccessible(true);\n"
            "                return m.invoke(null, converted);\n"
            "            }\n"
            "        }\n"
            '        throw new NoSuchMethodException("solve");\n'
            "    }\n"
            "\n"
            "    static Object convert(Object arg, Class<?> type) {\n"
            "        if (arg == null) return null;\n"
            "        String s = arg.toString();\n"
            "        if (type == int.class || type == Integer.class) return Integer.parseInt(s);\n"
            "        if (type == double.class || type == Double.class) return Double.parseDouble(s);\n"
            "        if (type == boolean.class || type == Boolean.class) return Boolean.parseBoolean(s);\n"
            "        if (type == long.class || type == Long.class) return Long.parseLong(s);\n"
            "        if (type == String.class) return s;\n"
            "        if (type == int[].class) return parseIntArray(s);\n"
            "        if (type == String[].class) return parseStringArray(s);\n"
            "        return s;\n"
            "    }\n"
            "\n"
            "    static int[] parseIntArray(String s) {\n"
            '        s = s.replaceAll("[\\\\[\\\\]\\\\s]", "");\n'
            "        if (s.isEmpty()) return new int[0];\n"
            '        String[] parts = s.split(",");\n'
            "        int[] arr = new int[parts.length];\n"
            "        for (int i = 0; i < parts.length; i++) arr[i] = Integer.parseInt(parts[i].trim());\n"
            "        return arr;\n"
            "    }\n"
            "\n"
            "    static String[] parseStringArray(String s) {\n"
            '        s = s.replaceAll("^\\\\[|\\\\]$", "");\n'
            "        if (s.isEmpty()) return new String[0];\n"
            '        return s.split(",\\\\s*");\n'
            "    }\n"
            "\n"
            "    static List<Map<String, Object>> parseTcArray(String json) {\n"
            "        List<Map<String, Object>> list = new ArrayList<>();\n"
            "        json = json.trim();\n"
            '        if (json.startsWith("[")) json = json.substring(1);\n'
            '        if (json.endsWith("]")) json = json.substring(0, json.length() - 1);\n'
            "        int depth = 0; int start = -1;\n"
            "        for (int i = 0; i < json.length(); i++) {\n"
            "            char c = json.charAt(i);\n"
            "            if (c == '{') { if (depth == 0) start = i; depth++; }\n"
            "            else if (c == '}') { depth--; if (depth == 0) { list.add(parseTcObj(json.substring(start, i + 1))); start = -1; } }\n"
            "        }\n"
            "        return list;\n"
            "    }\n"
            "\n"
            "    static Map<String, Object> parseTcObj(String json) {\n"
            "        Map<String, Object> m = new LinkedHashMap<>();\n"
            '        json = json.trim().replaceAll("^\\\\{|\\\\}$", "");\n'
            '        String[] pairs = json.split(",(?=\\\\s*\\"[\\\\w]+\\")");\n'
            "        for (String p : pairs) {\n"
            "            int colon = p.indexOf(':');\n"
            "            if (colon < 0) continue;\n"
            '            String key = p.substring(0, colon).trim().replaceAll("\\\"", "");\n'
            "            String val = p.substring(colon + 1).trim();\n"
            '            if (val.equals("true")) m.put(key, true);\n'
            '            else if (val.equals("false")) m.put(key, false);\n'
            '            else if (val.startsWith("\\\"")) m.put(key, val.substring(1, val.length() - 1));\n'
            "            else m.put(key, val);\n"
            "        }\n"
            "        return m;\n"
            "    }\n"
            "\n"
            "    static String toJson(Object obj) {\n"
            '        if (obj == null) return "null";\n'
            "        if (obj instanceof Boolean || obj instanceof Number) return obj.toString();\n"
            '        if (obj instanceof String) return "\\"" + ((String) obj).replace("\\\\", "\\\\\\\\").replace("\\\"", "\\\\\\"") + "\\"";\n'
            "        if (obj instanceof Map) {\n"
            '            StringBuilder sb = new StringBuilder("{");\n'
            "            boolean first = true;\n"
            "            for (Map.Entry<?, ?> e : ((Map<?, ?>) obj).entrySet()) {\n"
            "                if (!first) sb.append(\",\");\n"
            '                sb.append("\\"" + e.getKey() + "\\":").append(toJson(e.getValue()));\n'
            "                first = false;\n"
            "            }\n"
            '            return sb.append("}").toString();\n'
            "        }\n"
            "        if (obj instanceof Collection) {\n"
            '            StringBuilder sb = new StringBuilder("[");\n'
            "            boolean first = true;\n"
            "            for (Object item : (Collection<?>) obj) {\n"
            "                if (!first) sb.append(\",\");\n"
            "                sb.append(toJson(item));\n"
            "                first = false;\n"
            "            }\n"
            '            return sb.append("]").toString();\n'
            "        }\n"
            "        return obj.toString();\n"
            "    }\n"
            "}\n"
        )

    def _parse_suite_output(
        self, exec_result: ExecutionResult, test_cases: List[dict]
    ) -> List[TestCaseResult]:
        """Parse the delimited JSON output from a suite runner."""
        stdout = exec_result.stdout
        # Extract JSON between delimiters
        marker = "@@SUITE_RESULT@@"
        start = stdout.find(marker)
        end = stdout.rfind(marker)
        if start == -1 or end == -1 or start == end:
            # Runner failed — mark all as failed and show stderr
            stderr = exec_result.stderr[:200]
            return [
                TestCaseResult(
                    index=i + 1,
                    passed=False,
                    input="" if tc.get("hidden") else tc["input"],
                    expected="" if tc.get("hidden") else tc["expected_output"],
                    actual=f"Execution Error: {stderr}",
                    hidden=tc.get("hidden", False),
                )
                for i, tc in enumerate(test_cases)
            ]

        json_str = stdout[start + len(marker) : end].strip()
        try:
            results = json.loads(json_str)
        except json.JSONDecodeError:
            return [
                TestCaseResult(
                    index=i + 1,
                    passed=False,
                    input="" if tc.get("hidden") else tc["input"],
                    expected="" if tc.get("hidden") else tc["expected_output"],
                    actual="",
                    hidden=tc.get("hidden", False),
                )
                for i, tc in enumerate(test_cases)
            ]

        # Map runner results back to TestCaseResult objects
        result_map = {r["index"]: r for r in results}
        out: List[TestCaseResult] = []
        for i, tc in enumerate(test_cases):
            idx = i + 1
            r = result_map.get(idx, {})
            hidden = tc.get("hidden", False)
            out.append(
                TestCaseResult(
                    index=idx,
                    passed=r.get("passed", False),
                    input="" if hidden else tc["input"],
                    expected="" if hidden else tc["expected_output"],
                    actual="" if hidden else r.get("actual", ""),
                    hidden=hidden,
                )
            )
        return out

    def validate_code(self, language: str, code: str) -> dict:
        return self.validator.validate(language, code)
