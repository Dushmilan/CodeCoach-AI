"""Java suite runner — generates a batch test harness."""

import json
import re
from typing import Any, Dict, List


def java_suite_runner(user_code: str, test_cases: List[Dict[str, Any]]) -> str:
    tc_json = json.dumps(
        [
            {"input": tc["input"], "expected": tc["expected_output"], "hidden": tc.get("hidden", False), "index": i + 1}
            for i, tc in enumerate(test_cases)
        ]
    )
    func_match = re.search(r"public\s+[\w<>[\]]+\s+(\w+)\s*\(", user_code)
    func_name = func_match.group(1) if func_match else "solve"

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
        '                    result = callSolution("' + func_name + '", lines[0].trim());\n'
        "                } else if (lines.length == 2) {\n"
        '                    result = callSolution("' + func_name + '", lines[0].trim(), lines[1].trim());\n'
        "                } else {\n"
        '                    result = callSolution("' + func_name + '", (Object) lines);\n'
        "                }\n"
        "                if (result == null && _lastFirstArg != null) {\n"
        "                    actual = toJson(_lastFirstArg);\n"
        "                } else {\n"
        '                    actual = toJson(result);\n'
        "                }\n"
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
        "    static Object _lastFirstArg = null;\n"
        "\n"
        '    static Object callSolution(String methodName, Object... args) throws Exception {\n'
        "        Class<?> clazz = Solution.class;\n"
        "        for (Method m : clazz.getDeclaredMethods()) {\n"
        '            if (m.getName().equals(methodName) && m.getParameterCount() == args.length) {\n'
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
        '        throw new NoSuchMethodException(methodName);\n'
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
        "        if (obj instanceof int[]) {\n"
        "            int[] arr = (int[]) obj;\n"
        '            StringBuilder sb = new StringBuilder("[");\n'
        "            for (int i = 0; i < arr.length; i++) {\n"
        "                if (i > 0) sb.append(\",\");\n"
        "                sb.append(arr[i]);\n"
        "            }\n"
        '            return sb.append("]").toString();\n'
        "        }\n"
        "        if (obj instanceof boolean[]) {\n"
        "            boolean[] arr = (boolean[]) obj;\n"
        '            StringBuilder sb = new StringBuilder("[");\n'
        "            for (int i = 0; i < arr.length; i++) {\n"
        "                if (i > 0) sb.append(\",\");\n"
        "                sb.append(arr[i]);\n"
        "            }\n"
        '            return sb.append("]").toString();\n'
        "        }\n"
        "        if (obj instanceof double[]) {\n"
        "            double[] arr = (double[]) obj;\n"
        '            StringBuilder sb = new StringBuilder("[");\n'
        "            for (int i = 0; i < arr.length; i++) {\n"
        "                if (i > 0) sb.append(\",\");\n"
        "                sb.append(arr[i]);\n"
        "            }\n"
        '            return sb.append("]").toString();\n'
        "        }\n"
        "        if (obj instanceof Object[]) {\n"
        "            Object[] arr = (Object[]) obj;\n"
        '            StringBuilder sb = new StringBuilder("[");\n'
        "            for (int i = 0; i < arr.length; i++) {\n"
        "                if (i > 0) sb.append(\",\");\n"
        "                sb.append(toJson(arr[i]));\n"
        "            }\n"
        '            return sb.append("]").toString();\n'
        "        }\n"
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
