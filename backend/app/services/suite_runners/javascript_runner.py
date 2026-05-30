"""JavaScript suite runner — generates a batch test harness."""

import json
import re
from typing import Any, Dict, List


def javascript_suite_runner(user_code: str, test_cases: List[Dict[str, Any]]) -> str:
    tc_json = json.dumps(
        [{"input": tc["input"], "expected": tc["expected_output"], "hidden": tc.get("hidden", False), "index": i + 1}
         for i, tc in enumerate(test_cases)]
    )

    func_match = re.search(r"function\s+(\w+)\s*\(", user_code)
    if not func_match:
        func_match = re.search(r"(?:const|let|var)\s+(\w+)\s*=\s*(?:function|\(.*\)\s*=>)", user_code)
    func_name = func_match.group(1) if func_match else "solve"

    return f"""{user_code}

const testCases = {tc_json};
const results = [];

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
        passed = actual.trim() === tc.expected.trim();
    }} catch (e) {{
        actual = "";
        passed = false;
    }}
    results.push({{ index: tc.index, passed, actual, hidden: tc.hidden }});
}}

process.stdout.write('@@SUITE_RESULT@@' + JSON.stringify(results) + '@@SUITE_RESULT@@');
"""
