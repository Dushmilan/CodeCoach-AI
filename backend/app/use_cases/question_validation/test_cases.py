"""Test case validation use case."""

import json
import re
from typing import Dict, List, Optional

from app.ports.code_executor import CodeExecutor
from app.models.schemas import Question, TestCase as QuestionTestCase
from app.models.question_validation_schemas import (
    UseCaseValidationResult,
    ValidationUseCase,
    ValidationSeverity,
    TestCaseValidationConfig,
)

from .base import BaseValidationUseCase


class TestCaseValidationUseCase(BaseValidationUseCase):
    def __init__(
        self,
        executor: Optional[CodeExecutor] = None,
        config: Optional[TestCaseValidationConfig] = None,
    ):
        self.executor = executor
        self.config = config or TestCaseValidationConfig()

    @property
    def use_case(self) -> ValidationUseCase:
        return ValidationUseCase.TEST_CASES

    async def _execute_validation(self, question: Question) -> UseCaseValidationResult:
        issues: List = []
        issues.extend(self._validate_test_case_count(question.test_cases))
        for i, test_case in enumerate(question.test_cases):
            issues.extend(self._validate_single_test_case(test_case, i))
        issues.extend(self._check_duplicate_test_cases(question.test_cases))
        issues.extend(self._check_hidden_visible_distribution(question.test_cases))
        if self.executor:
            issues.extend(await self._validate_executability(question))
        passed = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        return self._create_result(passed=passed, issues=issues)

    def _validate_test_case_count(self, test_cases: List[QuestionTestCase]) -> List:
        issues = []
        count = len(test_cases)
        if count < self.config.min_test_cases:
            issues.append(
                self._create_issue(
                    message=f"At least {self.config.min_test_cases} test case(s) required, found {count}",
                    field="test_cases",
                    details={"count": count, "minimum": self.config.min_test_cases},
                )
            )
        if count > self.config.max_test_cases:
            issues.append(
                self._create_issue(
                    message=f"Maximum {self.config.max_test_cases} test cases allowed, found {count}",
                    field="test_cases",
                    severity=ValidationSeverity.WARNING,
                    details={"count": count, "maximum": self.config.max_test_cases},
                )
            )
        return issues

    def _validate_single_test_case(
        self, test_case: QuestionTestCase, index: int
    ) -> List:
        issues = []
        if test_case.input is None:
            issues.append(
                self._create_issue(
                    message=f"Test case {index + 1} is missing input",
                    field=f"test_cases[{index}].input",
                    test_case_index=index,
                )
            )
        elif len(test_case.input) > self.config.max_input_length:
            issues.append(
                self._create_issue(
                    message=f"Test case {index + 1} input exceeds maximum length",
                    field=f"test_cases[{index}].input",
                    test_case_index=index,
                    severity=ValidationSeverity.WARNING,
                    details={
                        "length": len(test_case.input),
                        "maximum": self.config.max_input_length,
                    },
                )
            )
        if test_case.expected_output is None:
            issues.append(
                self._create_issue(
                    message=f"Test case {index + 1} is missing expected output",
                    field=f"test_cases[{index}].expected_output",
                    test_case_index=index,
                )
            )
        elif len(test_case.expected_output) > self.config.max_output_length:
            issues.append(
                self._create_issue(
                    message=f"Test case {index + 1} expected output exceeds maximum length",
                    field=f"test_cases[{index}].expected_output",
                    test_case_index=index,
                    severity=ValidationSeverity.WARNING,
                    details={
                        "length": len(test_case.expected_output),
                        "maximum": self.config.max_output_length,
                    },
                )
            )
        if not test_case.description:
            issues.append(
                self._create_issue(
                    message=f"Test case {index + 1} is missing description",
                    field=f"test_cases[{index}].description",
                    test_case_index=index,
                    severity=ValidationSeverity.INFO,
                )
            )
        issues.extend(self._check_output_determinism(test_case, index))
        return issues

    def _check_output_determinism(
        self, test_case: QuestionTestCase, index: int
    ) -> List:
        issues = []
        patterns = [
            (r"\b0x[0-9a-f]+\b", "hexadecimal memory address"),
            (r"\b\d{13,}\b", "timestamp-like number"),
            (r"<.*object at 0x[0-9a-f]+>", "object reference"),
            (r"random", "random value reference"),
        ]
        for pattern, description in patterns:
            if re.search(pattern, test_case.expected_output, re.IGNORECASE):
                issues.append(
                    self._create_issue(
                        message=f"Test case {index + 1} expected output may contain non-deterministic value: {description}",
                        field=f"test_cases[{index}].expected_output",
                        test_case_index=index,
                        severity=ValidationSeverity.WARNING,
                        details={"pattern": pattern},
                    )
                )
        return issues

    def _check_duplicate_test_cases(self, test_cases: List[QuestionTestCase]) -> List:
        issues: List = []
        seen_inputs: Dict[str, int] = {}
        for i, test_case in enumerate(test_cases):
            input_key = test_case.input.strip() if test_case.input else ""
            if input_key in seen_inputs:
                prev_index = seen_inputs[input_key]
                issues.append(
                    self._create_issue(
                        message=f"Test case {i + 1} has same input as test case {prev_index + 1}",
                        field=f"test_cases[{i}].input",
                        test_case_index=i,
                        severity=ValidationSeverity.WARNING,
                        details={"duplicate_of": prev_index},
                    )
                )
            else:
                seen_inputs[input_key] = i
        return issues

    def _check_hidden_visible_distribution(
        self, test_cases: List[QuestionTestCase]
    ) -> List:
        issues: List = []
        if not test_cases:
            return issues
        hidden_count = sum(1 for tc in test_cases if tc.hidden)
        visible_count = len(test_cases) - hidden_count
        if visible_count == 0:
            issues.append(
                self._create_issue(
                    message="At least one visible (non-hidden) test case is recommended",
                    field="test_cases",
                    severity=ValidationSeverity.WARNING,
                    details={
                        "hidden_count": hidden_count,
                        "visible_count": visible_count,
                    },
                )
            )
        if self.config.require_hidden_tests and hidden_count == 0:
            issues.append(
                self._create_issue(
                    message="At least one hidden test case is required by configuration",
                    field="test_cases",
                    details={"hidden_count": hidden_count},
                )
            )
        return issues

    async def _validate_executability(self, question: Question) -> List:
        issues: List = []
        if not self.executor:
            return issues
        for i, test_case in enumerate(question.test_cases):
            try:
                test_code = f"""
import sys
import json
input_data = json.loads({json.dumps(test_case.input)})
print("Input parsed successfully")
"""
                result = await self.executor.execute(
                    language="python", code=test_code, stdin=""
                )
                if result.exit_code != 0:
                    issues.append(
                        self._create_issue(
                            message=f"Test case {i + 1} input format may cause execution issues",
                            field=f"test_cases[{i}].input",
                            test_case_index=i,
                            severity=ValidationSeverity.WARNING,
                            details={"error": result.stderr},
                        )
                    )
            except Exception as e:
                issues.append(
                    self._create_issue(
                        message=f"Failed to validate test case {i + 1} executability: {str(e)}",
                        field=f"test_cases[{i}]",
                        test_case_index=i,
                        severity=ValidationSeverity.INFO,
                    )
                )
        return issues
