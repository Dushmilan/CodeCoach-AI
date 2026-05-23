import re

from .base import CodeWrapper


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
