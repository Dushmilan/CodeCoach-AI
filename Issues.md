
# Active Issues

1. **AI Chat Layout Collapse**: AI Chat Panel forces layout collapse to full-screen when long strings are generated, effectively hiding the code editor.
2. **OBSOLETE**: Quality of Generated Test Cases: AI-generated questions frequently fail the quality gate (0/87 pass rate). *Status: Automated generation pipeline has been completely scrapped in favor of author-provided questions.*
3. Check if all the codes are taking as a string. Does Leetcode or hackerrank works like this??, Is linked list or tree also taken as a string?
4. **Curriculum Generation fails**: Generation pipeline skips crucial input parameters, resulting in incomplete curriculum structure.

6. **Piston Signal 6 crash with `repr()` + `True`/`False`**: Piston's `isolate` sandbox crashes (SIGABRT/signal 6) when the generated Python script contains `True` or `False` Python booleans in inline data via `repr()`. Root cause unclear — possibly isolate's memory tracking or cgroup interaction with Python's bool singleton. **Fix**: Removed the `hidden` boolean field from the suite runner's inline test case `repr()`. The `hidden` flag is now applied only server-side in `_parse_suite_output` using the original `test_cases` list, never embedded in the generated script.
7. **Dormant**: Test case 11 in `three-sum` had incomplete expected output — missing `[-4,-2,6]` triplet which also sums to 0 and is valid given the input's three `-2`s and two `6`s. **Fix**: Added the missing triplet to expected output.
8. **Suite Runner In-Place Bug**: In-place functions (`rotate-image`, `next-permutation`) return `None` → runner compares `"None"` to expected matrix → always fails. **Fix**: `__run_test` returns `(output, input_value)` tuple; `None` output → serialize input_value.
9. **Multi-Param AI Question Bug**: 5-param question input was a JSON dict but function expects 5 positional args → `TypeError`. **Fix**: Converted to `\n`-separated 5-line format; Python/JS runners use `*parsed_args` / `...parsedArgs` spread.
10. **JS `fs` Redeclaration Bug**: Both runner template and `JavaScriptCodeWrapper.wrap()` add `const fs = require('fs')` → `SyntaxError`. **Fix**: Removed from runner template; added `process.stdout.write` to wrapper bypass list.
11. **Java `json.dumps` Generator Bug**: `json.dumps` wrapped a bare generator expression → empty output. **Fix**: Wrapped with list comprehension `[...]`.
12. **`stdout=None` Crash**: `None` passed to string operations in `_parse_suite_output`. **Fix**: Guarded with `or ""`.

**Tests added (May 29):** 62 new tests across 5 files (32 suite_runners, +28 code_wrappers, +15 piston_service, +4 formatter, +18 submit_endpoints). Total: **462 backend tests** (356 unit + 106 integration). 4 pre-existing async errors + 6 pre-existing integration failures unchanged.

