"""Python suite runner — generates a batch test harness."""

import json
import re
from typing import Any, Dict, List


def python_suite_runner(user_code: str, test_cases: List[Dict[str, Any]]) -> str:
    user_code = re.sub(r'(\(\s*)self\s*,?\s*', r'\1', user_code)

    tc_clean = [
        {"input": tc["input"], "expected": tc["expected_output"], "index": i + 1}
        for i, tc in enumerate(test_cases)
    ]
    tc_repr = repr(tc_clean)

    func_match = re.search(r"def\s+(\w+)\s*\(", user_code)
    func_name = func_match.group(1) if func_match else "solve"

    return f"""import sys, json

{user_code}

def run_suite():
    __test_cases = {tc_repr}
    __results = []
    
    def __run_test(__tc):
        __inp = __tc["input"]
        try:
            __lines = __inp.split("\\n") if __inp else [""]
            if len(__lines) == 1:
                try:
                    __parsed = json.loads(__lines[0])
                except Exception:
                    __parsed = __lines[0]
                __result = {func_name}(__parsed)
                return __result, __parsed
            elif len(__lines) == 2:
                try:
                    __a = json.loads(__lines[0])
                    __b = json.loads(__lines[1]) if (__lines[1].strip().lstrip("-").isdigit() or __lines[1].strip().startswith("[")) else __lines[1]
                except Exception:
                    __a, __b = __lines[0], __lines[1]
                __result = {func_name}(__a, __b)
                return __result, __a
            else:
                __parsed_args = [json.loads(ln) if ln.strip() else ln for ln in __lines]
                __result = {func_name}(*__parsed_args)
                return __result, __parsed_args[0]
        except Exception as e:
            raise e

    for __tc in __test_cases:
        __idx = __tc["index"]
        __exp = __tc["expected"]
        try:
            __out, __in_val = __run_test(__tc)
            if __out is None:
                __actual = json.dumps(__in_val, separators=(",", ":")) if isinstance(__in_val, (list, dict)) else str(__in_val)
            elif isinstance(__out, list):
                __actual = json.dumps(__out, separators=(",", ":"))
            elif isinstance(__out, bool):
                __actual = str(__out).lower()
            else:
                __actual = str(__out)
            __passed = __actual.strip() == __exp.strip()
        except Exception as __e:
            __actual = str(__e)
            __passed = False
        __results.append({{"index": __idx, "passed": __passed, "actual": __actual}})

    print("@@SUITE_RESULT@@" + json.dumps(__results, separators=(",", ":")) + "@@SUITE_RESULT@@")
    sys.stdout.flush()

if __name__ == "__main__":
    run_suite()
"""
