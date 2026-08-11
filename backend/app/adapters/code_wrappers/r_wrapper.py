import re
from typing import Any, Dict, List

from .base import CodeWrapper

_FUNCTION_RE = re.compile(
    r"^\s*([a-zA-Z.][a-zA-Z0-9._]*)\s*(?:<-|=)\s*function\s*\(", re.MULTILINE
)


def _r_str(value: str) -> str:
    """Escape a Python string for use as an R single-quoted string literal."""
    return (
        "'" + value.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n") + "'"
    )


def _find_function(code: str) -> str:
    """Return the last top-level function defined — the entry point.

    Content convention: helper functions are defined first, the entry function
    (which receives the raw input text) is defined last.
    """
    matches = list(_FUNCTION_RE.finditer(code))
    return matches[-1].group(1) if matches else "solve"


class RCodeWrapper(CodeWrapper):
    def wrap(self, code: str) -> str:
        # If this is already a generated suite runner, pass through untouched.
        if "run_suite <- function()" in code:
            return code
        # Plain scripts (no function definitions) are stdin/stdout scripts —
        # pass through unchanged.
        matches = list(_FUNCTION_RE.finditer(code))
        if not matches:
            return code
        # Otherwise wrap the entry function so it reads stdin and prints the
        # result — mirrors how the lesson exercise UI submits (one run per test
        # with the test input on stdin).
        func_name = matches[-1].group(1)
        return f"""{code}
.__cc_input <- readLines(file("stdin"), warn = FALSE)
.__cc_text <- if (length(.__cc_input) == 0) "" else paste(.__cc_input, collapse = "\\n")
.__cc_result <- {func_name}(.__cc_text)
cat(.__cc_result, "\\n", sep = "")
"""

    def wrap_with_tests(self, code: str, test_cases: List[Dict[str, Any]]) -> str:
        func_name = _find_function(code)
        tc_lines = []
        for i, tc in enumerate(test_cases):
            inp = _r_str(tc.get("input", ""))
            exp = _r_str(tc.get("expected_output", ""))
            tc_lines.append(
                "    list(index = %d, input = %s, expected = %s)" % (i + 1, inp, exp)
            )
        tc_block = ",\n".join(tc_lines)

        return f"""{code}

run_suite <- function() {{
    tests <- list(
{tc_block}
    )
    results <- c()
    for (t in tests) {{
        out <- tryCatch(
            {func_name}(t$input),
            error = function(e) paste("Error:", conditionMessage(e))
        )
        actual <- as.character(out)
        passed <- identical(trimws(actual), trimws(t$expected))
        actual_json <- gsub("\\\\", "\\\\\\\\", actual, fixed = TRUE)
        actual_json <- gsub('"', '\\\\"', actual_json)
        actual_json <- gsub("\\n", "\\\\n", actual_json, fixed = TRUE)
        results <- c(results, sprintf(
            '{{"index": %d, "passed": %s, "actual": "%s"}}',
            t$index, ifelse(passed, "true", "false"), actual_json
        ))
    }}
    cat("@@SUITE_RESULT@@[")
    cat(paste(results, collapse = ","))
    cat("]@@SUITE_RESULT@@\\n")
}}

run_suite()
"""
