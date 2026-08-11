import base64
from typing import Any, Dict, List

from .base import CodeWrapper

_EOF = "CODEACH_SOLUTION_EOF_9x7"


class BashCodeWrapper(CodeWrapper):
    def wrap(self, code: str) -> str:
        # Bash exercises are stdin/stdout scripts — pass through unchanged.
        return code

    def wrap_with_tests(self, code: str, test_cases: List[Dict[str, Any]]) -> str:
        in_b64 = [base64.b64encode(tc.get("input", "").encode()).decode() for tc in test_cases]
        exp_b64 = [base64.b64encode(tc.get("expected_output", "").encode()).decode() for tc in test_cases]
        total = len(test_cases)

        return f"""#!/bin/bash
cat > /tmp/solution.sh <<'{_EOF}'
{code}
{_EOF}

TOTAL={total}
IN_B64=({ ' '.join(in_b64) })
EXP_B64=({ ' '.join(exp_b64) })

json_escape() {{
    printf '%s' "$1" | sed -e 's/\\\\/\\\\\\\\/g' -e 's/"/\\\\"/g' -e ':a' -e 'N' -e '$!ba' -e 's/\\n/\\\\n/g'
}}

run_suite() {{
    results=()
    for ((i=0; i<TOTAL; i++)); do
        input=$(printf '%s' "${{IN_B64[$i]}}" | base64 -d)
        expected=$(printf '%s' "${{EXP_B64[$i]}}" | base64 -d)
        out=$(printf '%s' "$input" | bash /tmp/solution.sh 2>&1)
        if [ "$out" == "$expected" ]; then passed=true; else passed=false; fi
        act=$(json_escape "$out")
        results+=("{{\\"index\\": $((i+1)), \\"passed\\": $passed, \\"actual\\": \\"$act\\"}}")
    done
    printf '@@SUITE_RESULT@@['
    joined=$(IFS=,; echo "${{results[*]}}")
    printf '%s' "$joined"
    printf ']@@SUITE_RESULT@@\\n'
}}

run_suite
"""
