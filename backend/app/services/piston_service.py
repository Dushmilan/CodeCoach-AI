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

from app.ports.code_executor import CodeExecutor, ExecutionResult

logger = logging.getLogger(__name__)


# ── Code Wrappers (per-language) ────────────────────────────────────────

class CodeWrapper(ABC):
    @abstractmethod
    def wrap(self, code: str) -> str: ...


class PythonCodeWrapper(CodeWrapper):
    def wrap(self, code: str) -> str:
        if "input(" in code or "sys.stdin" in code or "print(" in code:
            return code
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
        result = {func_name}(line)
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
            "compile_memory_limit": -1, "run_memory_limit": -1,
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

    def validate_code(self, language: str, code: str) -> dict:
        return self.validator.validate(language, code)
