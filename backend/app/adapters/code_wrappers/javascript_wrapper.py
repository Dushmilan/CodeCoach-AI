import json
import re
from typing import Any, Dict, List

from .base import CodeWrapper
from .output_comparator import JS_OUTPUT_MATCH


class JavaScriptCodeWrapper(CodeWrapper):
    def wrap(self, code: str) -> str:
        if (
            "process.stdin" in code
            or "readFileSync" in code
            or "console.log" in code
            or "process.stdout.write" in code
            or "require('fs')" in code
        ):
            return code
        func_match = re.search(r"function\s+(\w+)\s*\(", code)
        if not func_match:
            func_match = re.search(
                r"(?:const|let|var)\s+(\w+)\s*=\s*(?:function|\(.*\)\s*=>)", code
            )
        if not func_match:
            return code
        func_name = func_match.group(1)
        runner = f"""
{code}

try {{
    const input = require('fs').readFileSync(0, 'utf-8').trim();
    const lines = input.split('\\n');
    const args = lines.map(line => {{
        try {{ return JSON.parse(line); }} catch {{ return line; }}
    }});
    const result = {func_name}(...args);
    if (result === undefined && args.length > 0 && typeof args[0] === 'object') {{
        console.log(JSON.stringify(args[0]));
    }} else if (typeof result === 'boolean') {{
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

    def wrap_with_tests(self, code: str, test_cases: List[Dict[str, Any]]) -> str:
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
        func_match = re.search(r"function\s+(\w+)\s*\(", code)
        if not func_match:
            func_match = re.search(
                r"(?:const|let|var)\s+(\w+)\s*=\s*(?:function|\(.*\)\s*=>)", code
            )
        func_name = func_match.group(1) if func_match else "solve"

        return f"""{code}

const testCases = {tc_json};
const results = [];

{JS_OUTPUT_MATCH}

for (const tc of testCases) {{
    let actual = "";
    let passed = false;
    try {{
        const lines = tc.input ? tc.input.split('\\n') : [""];
        let out, inVal;
        if (lines.length === 1) {{
            let parsed;
            try {{ parsed = JSON.parse(lines[0]); }} catch {{ parsed = lines[0]; }}
            out = {func_name}(parsed);
            inVal = parsed;
        }} else if (lines.length === 2) {{
            let a, b;
            try {{ a = JSON.parse(lines[0]); }} catch {{ a = lines[0]; }}
            try {{ b = JSON.parse(lines[1]); }} catch {{ b = lines[1]; }}
            out = {func_name}(a, b);
            inVal = a;
        }} else {{
            const parsedArgs = lines.map(l => {{ try {{ return JSON.parse(l); }} catch {{ return l; }} }});
            out = {func_name}(...parsedArgs);
            inVal = parsedArgs[0];
        }}
        if (out == null) {{
            actual = typeof inVal === 'object' ? JSON.stringify(inVal) : String(inVal);
        }} else if (typeof out === 'boolean') {{
            actual = String(out);
        }} else if (typeof out === 'object') {{
            actual = JSON.stringify(out);
        }} else {{
            actual = String(out);
        }}
        passed = outputsMatch(actual, tc.expected);
    }} catch (e) {{
        actual = "";
        passed = false;
    }}
    results.push({{ index: tc.index, passed, actual, hidden: tc.hidden }});
}}

process.stdout.write('@@SUITE_RESULT@@' + JSON.stringify(results) + '@@SUITE_RESULT@@');
"""
