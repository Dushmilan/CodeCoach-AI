"""Output format validation use case."""

import json
from typing import List, Optional

from app.models.schemas import Question
from app.models.question_validation_schemas import (
    UseCaseValidationResult,
    ValidationUseCase,
    ValidationSeverity,
    OutputFormatConfig,
)

from .base import BaseValidationUseCase


class OutputFormatValidationUseCase(BaseValidationUseCase):
    FORMAT_JSON_ARRAY = "json_array"
    FORMAT_JSON_OBJECT = "json_object"
    FORMAT_NUMBER = "number"
    FORMAT_STRING = "string"
    FORMAT_BOOLEAN = "boolean"
    FORMAT_MIXED = "mixed"

    def __init__(self, config: Optional[OutputFormatConfig] = None):
        self.config = config or OutputFormatConfig()

    @property
    def use_case(self) -> ValidationUseCase:
        return ValidationUseCase.OUTPUT_FORMAT

    async def _execute_validation(self, question: Question) -> UseCaseValidationResult:
        issues: List = []
        if not question.test_cases:
            issues.append(self._create_issue(message="No test cases to validate output format", field="test_cases"))
            return self._create_result(passed=False, issues=issues)
        formats = []
        for i, test_case in enumerate(question.test_cases):
            formats.append((i, self._detect_output_format(test_case.expected_output), test_case.expected_output))
        issues.extend(self._check_format_consistency(formats))
        for i, test_case in enumerate(question.test_cases):
            issues.extend(self._validate_single_output(test_case.expected_output, i))
        issues.extend(self._check_examples_consistency(question))
        passed = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        return self._create_result(passed=passed, issues=issues)

    def _detect_output_format(self, output: str) -> str:
        output = output.strip()
        if output.startswith("[") and output.endswith("]"):
            try:
                if isinstance(json.loads(output), list):
                    return self.FORMAT_JSON_ARRAY
            except json.JSONDecodeError:
                pass
        if output.startswith("{") and output.endswith("}"):
            try:
                if isinstance(json.loads(output), dict):
                    return self.FORMAT_JSON_OBJECT
            except json.JSONDecodeError:
                pass
        try:
            float(output)
            return self.FORMAT_NUMBER
        except ValueError:
            pass
        if output.lower() in ("true", "false"):
            return self.FORMAT_BOOLEAN
        return self.FORMAT_STRING

    def _are_formats_compatible(self, format1: str, format2: str) -> bool:
        if format1 == format2:
            return True
        ns = {self.FORMAT_NUMBER, self.FORMAT_STRING}
        if format1 in ns and format2 in ns:
            return True
        bs = {self.FORMAT_BOOLEAN, self.FORMAT_STRING}
        if format1 in bs and format2 in bs:
            return True
        return False

    def _check_format_consistency(self, formats: List) -> List:
        issues = []
        unique_formats = set(f[1] for f in formats)
        if len(unique_formats) > 1:
            incompatible = {self.FORMAT_JSON_ARRAY, self.FORMAT_JSON_OBJECT}
            if unique_formats & incompatible and len(unique_formats & incompatible) > 1:
                issues.append(self._create_issue(message="Inconsistent output formats: mixing JSON arrays and objects", field="test_cases", details={"formats_found": list(unique_formats), "test_cases": [{"index": f[0], "format": f[1], "output": f[2][:50]} for f in formats]}))
            elif unique_formats & incompatible and (unique_formats - incompatible):
                issues.append(self._create_issue(message="Inconsistent output formats: mixing JSON with primitive types", field="test_cases", details={"formats_found": list(unique_formats)}))
            else:
                issues.append(self._create_issue(message=f"Minor output format inconsistency detected: {', '.join(unique_formats)}", field="test_cases", severity=ValidationSeverity.WARNING, details={"formats_found": list(unique_formats)}))
        return issues

    def _validate_single_output(self, output: str, index: int) -> List:
        issues = []
        output = output.strip()
        if not output:
            issues.append(self._create_issue(message=f"Test case {index + 1} has empty expected output", field=f"test_cases[{index}].expected_output", test_case_index=index, severity=ValidationSeverity.WARNING))
            return issues
        if output.startswith("[") or output.startswith("{"):
            try:
                parsed = json.loads(output)
                if isinstance(parsed, list) and len(parsed) == 0:
                    issues.append(self._create_issue(message=f"Test case {index + 1} returns empty array - ensure this is intentional", field=f"test_cases[{index}].expected_output", test_case_index=index, severity=ValidationSeverity.INFO))
                if isinstance(parsed, list) and len(parsed) > 1:
                    element_types = set(type(e).__name__ for e in parsed)
                    if len(element_types) > 1:
                        issues.append(self._create_issue(message=f"Test case {index + 1} array has mixed element types", field=f"test_cases[{index}].expected_output", test_case_index=index, severity=ValidationSeverity.WARNING, details={"types": list(element_types)}))
            except json.JSONDecodeError as e:
                issues.append(self._create_issue(message=f"Test case {index + 1} has invalid JSON output: {str(e)}", field=f"test_cases[{index}].expected_output", test_case_index=index, details={"error": str(e)}))
        if output.lower() in ("true", "false") and output != output.lower():
            issues.append(self._create_issue(message=f"Test case {index + 1} boolean output should be lowercase", field=f"test_cases[{index}].expected_output", test_case_index=index, severity=ValidationSeverity.INFO, details={"output": output}))
        if output != output.strip():
            issues.append(self._create_issue(message=f"Test case {index + 1} output has leading/trailing whitespace", field=f"test_cases[{index}].expected_output", test_case_index=index, severity=ValidationSeverity.INFO))
        return issues

    def _check_examples_consistency(self, question: Question) -> List:
        issues = []
        if not question.examples or not question.test_cases:
            return issues
        test_case_format = self._detect_output_format(question.test_cases[0].expected_output)
        for i, example in enumerate(question.examples):
            example_format = self._detect_output_format(example.output)
            if example_format != test_case_format:
                if self._are_formats_compatible(example_format, test_case_format):
                    issues.append(self._create_issue(message=f"Example {i + 1} output format differs from test cases", field=f"examples[{i}].output", severity=ValidationSeverity.INFO, details={"example_format": example_format, "test_case_format": test_case_format}))
                else:
                    issues.append(self._create_issue(message=f"Example {i + 1} output format is incompatible with test cases", field=f"examples[{i}].output", severity=ValidationSeverity.WARNING, details={"example_format": example_format, "test_case_format": test_case_format}))
        return issues
