import re

from .base import CodeWrapper


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
        output_line = (
            'System.out.println(String.valueOf(result).toLowerCase());'
            if return_type == "boolean"
            else 'System.out.println(result);'
        )
        main_lines = [
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
        return "\n".join(main_lines)

    def _build_multi_param_main(self, method_name: str) -> str:
        main_lines = [
            "    public static void main(String[] args) throws Exception {",
            "        java.io.BufferedReader reader = new java.io.BufferedReader(new java.io.InputStreamReader(System.in));",
            "        StringBuilder sb = new StringBuilder();",
            "        String line;",
            "        while ((line = reader.readLine()) != null) {",
            '            if (sb.length() > 0) sb.append("\\n");',
            "            sb.append(line);",
            "        }",
            "        String input = sb.toString().trim();",
            "",
            '        String[] lines = input.isEmpty() ? new String[]{""} : input.split("\\n", -1);',
            "        java.util.List<Object> parsedArgs = new java.util.ArrayList<>();",
            "        for (String l : lines) {",
            "            l = l.trim();",
            "            if (l.isEmpty()) {",
            '                parsedArgs.add("");',
            "            } else {",
            "                try {",
            "                    Object parsed = __JsonParser.parse(l);",
            "                    parsedArgs.add(parsed);",
            "                } catch (Exception e) {",
            "                    parsedArgs.add(l);",
            "                }",
            "            }",
            "        }",
            "",
            "        java.lang.reflect.Method method = null;",
            "        for (java.lang.reflect.Method m : Solution.class.getDeclaredMethods()) {",
            f'            if (m.getName().equals("{method_name}")) {{',
            "                method = m;",
            "                break;",
            "            }",
            "        }",
            "        if (method == null) {",
            f'            throw new NoSuchMethodException("{method_name}");',
            "        }",
            "",
            "        java.lang.reflect.Parameter[] paramTypes = method.getParameters();",
            "        Object[] callArgs = new Object[parsedArgs.size()];",
            "        for (int i = 0; i < parsedArgs.size() && i < paramTypes.length; i++) {",
            "            callArgs[i] = __convertArg(parsedArgs.get(i), paramTypes[i].getType());",
            "        }",
            "",
            "        Object result = method.invoke(null, callArgs);",
            "        if (result instanceof Boolean) {",
            '            System.out.println(String.valueOf(result).toLowerCase());',
            "        } else if (result instanceof String) {",
            "            System.out.println(result);",
            "        } else {",
            "            System.out.println(__toJson(result));",
            "        }",
            "    }",
        ]
        return "\n".join(main_lines)

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
            StringBuilder sb = new StringBuilder("[");
            for (int i = 0; i < list.size(); i++) {
                if (i > 0) sb.append(", ");
                sb.append(__toJson(list.get(i)));
            }
            sb.append("]");
            return sb.toString();
        }
        if (obj instanceof java.util.Map) {
            java.util.Map<?, ?> map = (java.util.Map<?, ?>) obj;
            StringBuilder sb = new StringBuilder("{");
            boolean first = true;
            for (java.util.Map.Entry<?, ?> e : map.entrySet()) {
                if (!first) sb.append(", ");
                sb.append(__toJson(e.getKey()));
                sb.append(": ");
                sb.append(__toJson(e.getValue()));
                first = false;
            }
            sb.append("}");
            return sb.toString();
        }
        return String.valueOf(obj);
    }

    private static class __JsonParser {
        private String json;
        private int pos;
        __JsonParser(String json) { this.json = json; this.pos = 0; }

        Object parse() {
            skipWs();
            if (pos >= json.length()) return null;
            char c = json.charAt(pos);
            if (c == '"') return parseStr();
            if (c == '{') return parseObj();
            if (c == '[') return parseArr();
            if (c == 't' || c == 'f') { boolean v = json.startsWith("true", pos); pos += v ? 4 : 5; return v; }
            if (c == 'n') { pos += 4; return null; }
            return parseNum();
        }

        String parseStr() {
            pos++;
            StringBuilder sb = new StringBuilder();
            while (pos < json.length()) {
                char c = json.charAt(pos);
                if (c == '"') { pos++; break; }
                if (c == '\\\\' && pos + 1 < json.length()) {
                    pos++; char n = json.charAt(pos);
                    if (n == '"') sb.append('"'); else if (n == '\\\\') sb.append('\\\\'); else if (n == 'n') sb.append('\\n'); else if (n == 'r') sb.append('\\r'); else if (n == 't') sb.append('\\t'); else sb.append(n);
                } else { sb.append(c); }
                pos++;
            }
            return sb.toString();
        }

        Number parseNum() {
            int start = pos;
            if (pos < json.length() && json.charAt(pos) == '-') pos++;
            while (pos < json.length() && Character.isDigit(json.charAt(pos))) pos++;
            boolean isDbl = false;
            if (pos < json.length() && json.charAt(pos) == '.') { isDbl = true; pos++; while (pos < json.length() && Character.isDigit(json.charAt(pos))) pos++; }
            if (pos < json.length() && (json.charAt(pos) == 'e' || json.charAt(pos) == 'E')) { isDbl = true; pos++; if (pos < json.length() && (json.charAt(pos) == '+' || json.charAt(pos) == '-')) pos++; while (pos < json.length() && Character.isDigit(json.charAt(pos))) pos++; }
            String ns = json.substring(start, pos);
            if (isDbl) return Double.parseDouble(ns);
            long v = Long.parseLong(ns);
            return (v >= Integer.MIN_VALUE && v <= Integer.MAX_VALUE) ? (int) v : v;
        }

        java.util.List<Object> parseArr() {
            pos++;
            java.util.List<Object> list = new java.util.ArrayList<>();
            skipWs();
            if (pos < json.length() && json.charAt(pos) == ']') { pos++; return list; }
            while (pos < json.length()) { list.add(parse()); skipWs(); if (pos < json.length() && json.charAt(pos) == ']') { pos++; break; } if (pos < json.length() && json.charAt(pos) == ',') { pos++; skipWs(); } }
            return list;
        }

        java.util.Map<String, Object> parseObj() {
            pos++;
            java.util.Map<String, Object> map = new java.util.LinkedHashMap<>();
            skipWs();
            if (pos < json.length() && json.charAt(pos) == '}') { pos++; return map; }
            while (pos < json.length()) { skipWs(); String key = (String) parse(); skipWs(); if (pos < json.length() && json.charAt(pos) == ':') pos++; skipWs(); map.put(key, parse()); skipWs(); if (pos < json.length() && json.charAt(pos) == '}') { pos++; break; } if (pos < json.length() && json.charAt(pos) == ',') { pos++; skipWs(); } }
            return map;
        }

        void skipWs() { while (pos < json.length() && Character.isWhitespace(json.charAt(pos))) pos++; }

        static Object parse(String s) { return new __JsonParser(s).parse(); }
    }
""".lstrip("\n")
