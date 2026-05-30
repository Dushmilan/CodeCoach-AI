import json
import re

from .base import CodeWrapper


class PythonCodeWrapper(CodeWrapper):
    def wrap(self, code: str) -> str:
        if "input(" in code or "sys.stdin" in code or "print(" in code:
            return code
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
    if result is None and isinstance(parsed_line, (list, dict)):
        print(json.dumps(parsed_line, separators=(",", ":")))
    elif isinstance(result, list):
        print(json.dumps(result, separators=(",", ":")))
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
