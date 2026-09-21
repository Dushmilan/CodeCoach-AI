"""Solution validation use case."""

import json
import re
from typing import Any, Dict, List, Optional, Union

from app.ports.code_executor import CodeExecutor
from app.models.schemas import Question, StarterCode
from app.models.question_validation_schemas import (
    UseCaseValidationResult,
    ValidationUseCase,
    ValidationSeverity,
)

from .base import BaseValidationUseCase


class SolutionValidationUseCase(BaseValidationUseCase):
    def __init__(self, executor: Optional[CodeExecutor] = None):
        self.executor = executor

    @property
    def use_case(self) -> ValidationUseCase:
        return ValidationUseCase.SOLUTION

    async def _execute_validation(self, question: Question) -> UseCaseValidationResult:
        issues: List = []
        if not question.solution:
            issues.append(
                self._create_issue(
                    message="Reference solution is required for validation",
                    field="solution",
                )
            )
            return self._create_result(passed=False, issues=issues)
        if self.executor:
            issues.extend(await self._validate_solution_with_piston(question))
        else:
            issues.append(
                self._create_issue(
                    message="Cannot validate solution execution without Piston service",
                    field="solution",
                    severity=ValidationSeverity.WARNING,
                )
            )
        passed = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        return self._create_result(passed=passed, issues=issues)

    def _compare_outputs(self, actual: str, expected: str) -> bool:
        if actual == expected:
            return True
        if actual.strip() == expected.strip():
            return True
        try:
            return json.loads(actual) == json.loads(expected)
        except (json.JSONDecodeError, ValueError):
            pass
        try:
            return float(actual) == float(expected)
        except (ValueError, TypeError):
            pass
        if actual.lower() in ("true", "false") and expected.lower() in (
            "true",
            "false",
        ):
            return actual.lower() == expected.lower()
        return False

    def _create_runner(
        self, solution_code: str, func_name: str, question: Question
    ) -> str:
        return f"""
import sys
import json
from typing import List

{solution_code}

lines = sys.stdin.read().strip().split('\\n')
try:
    if len(lines) == 1:
        try:
            input_data = json.loads(lines[0])
        except:
            input_data = lines[0]
        result = {func_name}(input_data)
    elif len(lines) == 2:
        try:
            first = json.loads(lines[0])
            second = json.loads(lines[1]) if lines[1].isdigit() or lines[1].startswith('[') else int(lines[1])
            result = {func_name}(first, second)
        except:
            result = {func_name}(lines[0], lines[1])
    else:
        result = {func_name}(lines)
    if isinstance(result, list):
        print(json.dumps(result))
    elif isinstance(result, bool):
        print(str(result).lower())
    else:
        print(result)
except Exception as e:
    print(f"Error: {{e}}", file=sys.stderr)
    sys.exit(1)
"""

    def _starter_python_code(
        self, starter: Union[StarterCode, str, List, Dict[str, Any], None]
    ) -> str:
        """Coerce a union-typed starter to its Python code, if any.

        ``Question.starter`` is ``StarterCode | str | list | dict``: the
        schema's ``normalize_starter`` turns language-name strings and
        list/dict shapes into a model, but plain strings survive and
        unvalidated shapes (``model_construct``/``model_copy``) can arrive
        as list/dict. This mirrors that normalization at the narrowest
        boundary instead of crashing on attribute access: model -> .python,
        dict -> its ``python`` entry, list -> the ``python`` language entry,
        anything else (str, None, ...) -> "" (treated as absent, exactly
        like the sibling use cases' ``getattr(starter, lang, None)``).
        """
        if isinstance(starter, StarterCode):
            return starter.python or ""
        if isinstance(starter, dict):
            code = starter.get("python", "")
            return code if isinstance(code, str) else ""
        if isinstance(starter, list):
            for entry in starter:
                if (
                    isinstance(entry, dict)
                    and entry.get("language") == "python"
                    and isinstance(entry.get("code"), str)
                ):
                    return entry["code"]
            return ""
        return ""

    def _create_executable_solution(self, question: Question) -> Optional[str]:
        if question.is_interactive:
            return str(question.solution) if question.solution else None

        # The runnable artifact under test is the *reference solution*
        # (question.solution), not the starter template: executing the stub
        # and attributing the outcome to the solution produced false ERRORs
        # on every real question (prose solution + pass stub) and could mask
        # a wrong reference behind a working starter. The solution field is
        # usually prose, so fall back to the starter only when the solution
        # carries no function definition.
        candidates = []
        if question.solution:
            candidates.append(str(question.solution))
        starter_code = self._starter_python_code(question.starter)
        if starter_code:
            candidates.append(starter_code)
        for candidate in candidates:
            if not self._executable_candidate(candidate):
                continue
            func_match = re.search(r"def\s+(\w+)\s*\(", candidate)
            assert func_match is not None  # guaranteed by _executable_candidate
            return self._create_runner(candidate, func_match.group(1), question)
        return None

    def _executable_candidate(self, code: Optional[str]) -> bool:
        if not code:
            return False
        if not re.search(r"def\s+(\w+)\s*\(", code):
            return False
        return "pass" not in code or "return" in code

    def _used_starter_fallback(self, question: Question) -> bool:
        """True when the executed artifact came from the starter, not the reference.

        Interactive questions always execute the reference directly; otherwise
        the fallback fires exactly when the solution carries no executable
        function but the starter does (mirrors `_create_executable_solution`).
        """
        if question.is_interactive:
            return False
        solution_text = str(question.solution) if question.solution else ""
        if self._executable_candidate(solution_text):
            return False
        starter_python = self._starter_python_code(question.starter)
        return self._executable_candidate(starter_python)

    async def _validate_solution_with_piston(self, question: Question) -> List:
        issues = []
        solution_code = self._create_executable_solution(question)
        if not solution_code:
            # No runnable artifact exists (prose solution + stub-only
            # starter is the normal real-bank shape): this is advisory,
            # not a bank-blocking error. Genuinely executable references
            # that fail cases are still reported as ERROR below.
            issues.append(
                self._create_issue(
                    message="Could not create executable solution from reference solution",
                    field="solution",
                    severity=ValidationSeverity.WARNING,
                )
            )
            return issues
        used_fallback = self._used_starter_fallback(question)
        fallback_note = (
            " (executed via starter-code fallback; reference solution is prose)"
            if used_fallback
            else ""
        )
        passed_count = 0
        total_count = len(question.test_cases)
        for i, test_case in enumerate(question.test_cases):
            try:
                result = await self.executor.execute(
                    language="python", code=solution_code, stdin=test_case.input
                )
                if result.exit_code != 0:
                    issues.append(
                        self._create_issue(
                            message=f"Solution failed on test case {i + 1}: {result.stderr[:100]}{fallback_note}",
                            field="solution",
                            test_case_index=i,
                            details={
                                "test_case": test_case.description,
                                "error": result.stderr,
                            },
                        )
                    )
                    continue
                actual_output = result.stdout.strip()
                expected_output = test_case.expected_output.strip()
                if self._compare_outputs(actual_output, expected_output):
                    passed_count += 1
                else:
                    issues.append(
                        self._create_issue(
                            message=f"Solution output mismatch on test case {i + 1}{fallback_note}",
                            field="solution",
                            test_case_index=i,
                            details={
                                "test_case": test_case.description,
                                "expected": expected_output,
                                "actual": actual_output,
                            },
                        )
                    )
            except Exception as e:
                issues.append(
                    self._create_issue(
                        message=f"Failed to execute solution for test case {i + 1}: {str(e)}",
                        field="solution",
                        test_case_index=i,
                    )
                )
        if total_count > 0 and passed_count < total_count:
            issues.append(
                self._create_issue(
                    message=f"Solution only passed {passed_count}/{total_count} test cases",
                    field="solution",
                    details={"passed": passed_count, "total": total_count},
                )
            )
        return issues
