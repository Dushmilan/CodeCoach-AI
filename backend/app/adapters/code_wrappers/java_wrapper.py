import json
import re
from typing import Any, Dict, List

from .base import CodeWrapper
from .output_comparator import JAVA_OUTPUT_MATCH


class JavaCodeWrapper(CodeWrapper):
    def wrap(self, code: str) -> str:
        if "public static void main" in code:
            return code
        method_pattern = (
            r"public\s+(?:static\s+)?([\w<>[\],\s?]+)\s+(\w+)\s*\(([^)]*)\)"
        )
        method_match = re.search(method_pattern, code)
        if not method_match:
            return code
        method_name = method_match.group(2)
        return_type = method_match.group(1).strip()
        params_str = method_match.group(3).strip()
        is_static = bool(re.search(r"public\s+static", code))
        param_count = len([p for p in params_str.split(",") if p.strip()])
        first_param_type = (
            params_str.split(",")[0].strip().split(" ")[0] if params_str else ""
        )
        is_single_string = param_count == 1 and first_param_type == "String"

        if is_single_string:
            main_code = self._build_single_string_main(method_name, return_type)
            helper_code = ""
        else:
            main_code = self._build_multi_param_main(method_name, is_static)
            helper_code = self._helper_code()

        insertion = (
            "\n"
            + main_code
            + "\n"
            + (helper_code + "\n" if not is_single_string else "")
        )
        class_match = re.search(r"(public\s+class\s+\w+\s*\{)", code)
        if class_match:
            insertion_point = class_match.end(1)
            return code[:insertion_point] + insertion + code[insertion_point:]
        imports = []
        body_lines = []
        for line in code.split("\n"):
            if line.strip().startswith("import "):
                imports.append(line)
            else:
                body_lines.append(line)
        body = "\n".join(body_lines).strip()
        imports_str = "\n".join(imports)
        if imports_str:
            imports_str += "\n"
        return f"""{imports_str}public class Solution {{
{insertion}
{body}
}}"""

    def _build_single_string_main(self, method_name: str, return_type: str) -> str:
        output_line = (
            "System.out.println(String.valueOf(result).toLowerCase());"
            if return_type == "boolean"
            else "System.out.println(result);"
        )
        return "\n".join(
            [
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
            ]
        )

    def _build_multi_param_main(self, method_name: str, is_static: bool = True) -> str:
        instance_code = "null" if is_static else "new Solution()"
        return "\n".join(
            [
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
                '            if (l.isEmpty()) { parsedArgs.add(""); }',
                "            else {",
                "                try { parsedArgs.add(__JsonParser.parse(l)); }",
                "                catch (Exception e) { parsedArgs.add(l); }",
                "            }",
                "        }",
                "        java.lang.reflect.Method method = null;",
                "        for (java.lang.reflect.Method m : Solution.class.getDeclaredMethods()) {",
                f'            if (m.getName().equals("{method_name}")) {{ method = m; break; }}',
                "        }",
                '        if (method == null) throw new NoSuchMethodException("'
                + method_name
                + '");',
                "        java.lang.reflect.Parameter[] paramTypes = method.getParameters();",
                "        Object[] callArgs = new Object[parsedArgs.size()];",
                "        for (int i = 0; i < parsedArgs.size() && i < paramTypes.length; i++) {",
                "            callArgs[i] = __convertArg(parsedArgs.get(i), paramTypes[i].getType());",
                "        }",
                f"        Object result = method.invoke({instance_code}, callArgs);",
                "        if (result == null && method.getReturnType() == void.class && callArgs.length > 0) {",
                "            System.out.println(__toJson(callArgs[0]));",
                "        } else if (result instanceof Boolean) { System.out.println(String.valueOf(result).toLowerCase()); }",
                "        else if (result instanceof String) { System.out.println(result); }",
                "        else { System.out.println(__toJson(result)); }",
                "    }",
            ]
        )

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
        if (targetType == int[].class && arg instanceof java.util.List) {
            java.util.List<?> list = (java.util.List<?>) arg;
            int[] arr = new int[list.size()];
            for (int i = 0; i < list.size(); i++) {
                Object item = list.get(i);
                arr[i] = (item instanceof Number) ? ((Number) item).intValue() : Integer.parseInt(item.toString());
            }
            return arr;
        }
        if (targetType == String[].class && arg instanceof java.util.List) {
            java.util.List<?> list = (java.util.List<?>) arg;
            String[] arr = new String[list.size()];
            for (int i = 0; i < list.size(); i++) {
                arr[i] = String.valueOf(list.get(i));
            }
            return arr;
        }
        if (targetType == int[][].class && arg instanceof java.util.List) {
            java.util.List<?> list = (java.util.List<?>) arg;
            int[][] arr = new int[list.size()][];
            for (int i = 0; i < list.size(); i++) {
                java.util.List<?> row = (java.util.List<?>) list.get(i);
                arr[i] = new int[row.size()];
                for (int j = 0; j < row.size(); j++) {
                    Object item = row.get(j);
                    arr[i][j] = (item instanceof Number) ? ((Number) item).intValue() : Integer.parseInt(item.toString());
                }
            }
            return arr;
        }
        return arg;
    }
    private static String __toJson(Object obj) {
        if (obj == null) return "null";
        if (obj instanceof Boolean) return String.valueOf(obj).toLowerCase();
        if (obj instanceof Number) return String.valueOf(obj);
        if (obj instanceof String) return "\\"" + ((String) obj).replace("\\\\", "\\\\\\\\").replace("\\"", "\\\\\\"") + "\\"";
        if (obj instanceof int[]) {
            int[] arr = (int[]) obj;
            StringBuilder sb = new StringBuilder("["); for (int i = 0; i < arr.length; i++) { if (i > 0) sb.append(","); sb.append(arr[i]); } sb.append("]");
            return sb.toString();
        }
        if (obj instanceof boolean[]) {
            boolean[] arr = (boolean[]) obj;
            StringBuilder sb = new StringBuilder("["); for (int i = 0; i < arr.length; i++) { if (i > 0) sb.append(","); sb.append(arr[i]); } sb.append("]");
            return sb.toString();
        }
        if (obj instanceof double[]) {
            double[] arr = (double[]) obj;
            StringBuilder sb = new StringBuilder("["); for (int i = 0; i < arr.length; i++) { if (i > 0) sb.append(","); sb.append(arr[i]); } sb.append("]");
            return sb.toString();
        }
        if (obj instanceof Object[]) {
            Object[] arr = (Object[]) obj;
            StringBuilder sb = new StringBuilder("["); for (int i = 0; i < arr.length; i++) { if (i > 0) sb.append(","); sb.append(__toJson(arr[i])); } sb.append("]");
            return sb.toString();
        }
        if (obj instanceof java.util.List) {
            java.util.List<?> list = (java.util.List<?>) obj;
            StringBuilder sb = new StringBuilder("["); for (int i = 0; i < list.size(); i++) { if (i > 0) sb.append(","); sb.append(__toJson(list.get(i))); } sb.append("]");
            return sb.toString();
        }
        if (obj instanceof java.util.Map) {
            java.util.Map<?, ?> map = (java.util.Map<?, ?>) obj;
            StringBuilder sb = new StringBuilder("{"); boolean first = true;
            for (java.util.Map.Entry<?, ?> e : map.entrySet()) {
                if (!first) sb.append(",");
                sb.append("\\"" + e.getKey() + "\\":").append(__toJson(e.getValue()));
                first = false;
            }
            return sb.append("}").toString();
        }
        if (obj instanceof java.util.Collection) {
            java.util.Collection<?> coll = (java.util.Collection<?>) obj;
            StringBuilder sb = new StringBuilder("["); boolean first = true;
            for (Object item : coll) {
                if (!first) sb.append(",");
                sb.append(__toJson(item));
                first = false;
            }
            return sb.append("]").toString();
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

    def wrap_with_tests(self, _code: str, test_cases: List[Dict[str, Any]]) -> str:
        tc_json = json.dumps(
            [
                {
                    "input": tc["input"],
                    "expected": tc["expected_output"],
                    "hidden": tc.get("hidden", False),
                    "index": i + 1,
                }
                for i, tc in enumerate(test_cases)
            ]
        )
        func_match = re.search(r"public\s+[\w<>[\]]+\s+(\w+)\s*\(", _code)
        func_name = func_match.group(1) if func_match else "solve"

        return (
            "import java.util.*;\n"
            "import java.lang.reflect.*;\n"
            "\n"
            "public class Solution {\n" + _code + "\n"
            "\n"
            "    public static void main(String[] args) throws Exception {\n"
            '        String tcJson = "' + tc_json.replace('"', '\\"') + '";\n'
            "        List<Map<String, Object>> testCases = parseTcArray(tcJson);\n"
            "        List<Map<String, Object>> results = new ArrayList<>();\n"
            "\n"
            "        for (Map<String, Object> tc : testCases) {\n"
            '            int idx = Integer.parseInt(tc.get("index").toString());\n'
            '            String input = (String) tc.get("input");\n'
            '            String expected = (String) tc.get("expected");\n'
            '            boolean hidden = (Boolean) tc.get("hidden");\n'
            '            String actual = "";\n'
            "            boolean passed = false;\n"
            "            try {\n"
            '                String[] lines = input.isEmpty() ? new String[]{""} : input.split("\\n", -1);\n'
            "                Object result;\n"
            "                if (lines.length == 1) {\n"
            '                    result = callSolution("'
            + func_name
            + '", lines[0].trim());\n'
            "                } else if (lines.length == 2) {\n"
            '                    result = callSolution("'
            + func_name
            + '", lines[0].trim(), lines[1].trim());\n'
            "                } else {\n"
            '                    result = callSolution("'
            + func_name
            + '", (Object) lines);\n'
            "                }\n"
            "                if (result == null && _lastFirstArg != null) {\n"
            "                    actual = toJson(_lastFirstArg);\n"
            "                } else {\n"
            "                    actual = toJson(result);\n"
            "                }\n"
            "                passed = outputsMatch(actual, expected);\n"
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
            "    static Object _lastFirstArg = null;\n"
            "\n"
            + JAVA_OUTPUT_MATCH.strip("\n")
            + "\n"
            "\n"
            "    static Object callSolution(String methodName, Object... args) throws Exception {\n"
            "        Class<?> clazz = Solution.class;\n"
            "        for (Method m : clazz.getDeclaredMethods()) {\n"
            "            if (m.getName().equals(methodName) && m.getParameterCount() == args.length) {\n"
            "                Object[] converted = new Object[args.length];\n"
            "                Class<?>[] types = m.getParameterTypes();\n"
            "                for (int i = 0; i < args.length; i++) {\n"
            "                    converted[i] = convert(args[i], types[i]);\n"
            "                }\n"
            "                _lastFirstArg = converted.length > 0 ? converted[0] : null;\n"
            "                m.setAccessible(true);\n"
            "                Object obj = java.lang.reflect.Modifier.isStatic(m.getModifiers()) ? null : new Solution();\n"
            "                return m.invoke(obj, converted);\n"
            "            }\n"
            "        }\n"
            "        throw new NoSuchMethodException(methodName);\n"
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
            "        if (type == int[][].class) return parseInt2DArray(s);\n"
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
            "    static int[][] parseInt2DArray(String s) {\n"
            '        s = s.trim().replaceAll("^\\\\[\\\\[|\\\\]\\\\]$", "");\n'
            "        if (s.isEmpty()) return new int[0][0];\n"
            '        String[] rows = s.split("\\\\],\\\\[");\n'
            "        int[][] result = new int[rows.length][];\n"
            "        for (int i = 0; i < rows.length; i++) {\n"
            "            result[i] = parseIntArray(rows[i]);\n"
            "        }\n"
            "        return result;\n"
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
            '            String key = p.substring(0, colon).trim().replaceAll("\\"", "");\n'
            "            String val = p.substring(colon + 1).trim();\n"
            '            if (val.equals("true")) m.put(key, true);\n'
            '            else if (val.equals("false")) m.put(key, false);\n'
            '            else if (val.startsWith("\\"")) m.put(key, val.substring(1, val.length() - 1));\n'
            "            else m.put(key, val);\n"
            "        }\n"
            "        return m;\n"
            "    }\n"
            "\n"
            "    static String toJson(Object obj) {\n"
            '        if (obj == null) return "null";\n'
            "        if (obj instanceof Boolean || obj instanceof Number) return obj.toString();\n"
            '        if (obj instanceof String) return "\\"" + ((String) obj).replace("\\\\", "\\\\\\\\").replace("\\"", "\\\\\\"") + "\\"";\n'
            "        if (obj instanceof int[]) {\n"
            "            int[] arr = (int[]) obj;\n"
            '            StringBuilder sb = new StringBuilder("[");\n'
            "            for (int i = 0; i < arr.length; i++) {\n"
            '                if (i > 0) sb.append(",");\n'
            "                sb.append(arr[i]);\n"
            "            }\n"
            '            return sb.append("]").toString();\n'
            "        }\n"
            "        if (obj instanceof boolean[]) {\n"
            "            boolean[] arr = (boolean[]) obj;\n"
            '            StringBuilder sb = new StringBuilder("[");\n'
            "            for (int i = 0; i < arr.length; i++) {\n"
            '                if (i > 0) sb.append(",");\n'
            "                sb.append(arr[i]);\n"
            "            }\n"
            '            return sb.append("]").toString();\n'
            "        }\n"
            "        if (obj instanceof double[]) {\n"
            "            double[] arr = (double[]) obj;\n"
            '            StringBuilder sb = new StringBuilder("[");\n'
            "            for (int i = 0; i < arr.length; i++) {\n"
            '                if (i > 0) sb.append(",");\n'
            "                sb.append(arr[i]);\n"
            "            }\n"
            '            return sb.append("]").toString();\n'
            "        }\n"
            "        if (obj instanceof Object[]) {\n"
            "            Object[] arr = (Object[]) obj;\n"
            '            StringBuilder sb = new StringBuilder("[");\n'
            "            for (int i = 0; i < arr.length; i++) {\n"
            '                if (i > 0) sb.append(",");\n'
            "                sb.append(toJson(arr[i]));\n"
            "            }\n"
            '            return sb.append("]").toString();\n'
            "        }\n"
            "        if (obj instanceof Map) {\n"
            '            StringBuilder sb = new StringBuilder("{");\n'
            "            boolean first = true;\n"
            "            for (Map.Entry<?, ?> e : ((Map<?, ?>) obj).entrySet()) {\n"
            '                if (!first) sb.append(",");\n'
            '                sb.append("\\"" + e.getKey() + "\\":").append(toJson(e.getValue()));\n'
            "                first = false;\n"
            "            }\n"
            '            return sb.append("}").toString();\n'
            "        }\n"
            "        if (obj instanceof Collection) {\n"
            '            StringBuilder sb = new StringBuilder("[");\n'
            "            boolean first = true;\n"
            "            for (Object item : (Collection<?>) obj) {\n"
            '                if (!first) sb.append(",");\n'
            "                sb.append(toJson(item));\n"
            "                first = false;\n"
            "            }\n"
            '            return sb.append("]").toString();\n'
            "        }\n"
            "        return obj.toString();\n"
            "    }\n"
            "}\n"
        )
