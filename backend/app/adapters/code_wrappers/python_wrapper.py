import re

from .base import CodeWrapper


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
