
# Active Issues

1. **AI Chat Layout Collapse**: AI Chat Panel forces layout collapse to full-screen when long strings are generated, effectively hiding the code editor.
2. **OBSOLETE**: Quality of Generated Test Cases: AI-generated questions frequently fail the quality gate (0/87 pass rate). *Status: Automated generation pipeline has been completely scrapped in favor of author-provided questions.*
3. Check if all the codes are taking as a string. Does Leetcode or hackerrank works like this??, Is linked list or tree also taken as a string?
4. **Curriculum Generation fails**: Generation pipeline skips crucial input parameters, resulting in incomplete curriculum structure.

6. **Piston Signal 6 crash with `repr()` + `True`/`False`**: Piston's `isolate` sandbox crashes (SIGABRT/signal 6) when the generated Python script contains `True` or `False` Python booleans in inline data via `repr()`. Root cause unclear — possibly isolate's memory tracking or cgroup interaction with Python's bool singleton. **Fix**: Removed the `hidden` boolean field from the suite runner's inline test case `repr()`. The `hidden` flag is now applied only server-side in `_parse_suite_output` using the original `test_cases` list, never embedded in the generated script.
7. **Dormant**: Test case 11 in `three-sum` had incomplete expected output — missing `[-4,-2,6]` triplet which also sums to 0 and is valid given the input's three `-2`s and two `6`s. **Fix**: Added the missing triplet to expected output.

