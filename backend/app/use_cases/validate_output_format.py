"""
Output format validation use case.

Validates that expected outputs across test cases have consistent formats
and are properly parseable.
"""

from typing import List, Optional
import json
import re

from app.models.schemas import Question
from app.models.question_validation_schemas import (
    UseCaseValidationResult,
    ValidationUseCase,
    ValidationSeverity,
    OutputFormatConfig,
)
from app.use_cases.base import BaseValidationUseCase


class OutputFormatValidationUseCase(BaseValidationUseCase):
    """
    Validates output format consistency across test cases.
    
    Checks:
    - All expected outputs have consistent format
    - Output is parseable (JSON, number, string, boolean)
    - Output format matches problem description
    """
    
    # Output format types
    FORMAT_JSON_ARRAY = "json_array"
    FORMAT_JSON_OBJECT = "json_object"
    FORMAT_NUMBER = "number"
    FORMAT_STRING = "string"
    FORMAT_BOOLEAN = "boolean"
    FORMAT_MIXED = "mixed"
    
    def __init__(
        self,
        config: Optional[OutputFormatConfig] = None
    ):
        """
        Initialize output format validation use case.
        
        Args:
            config: Configuration for output format validation
        """
        self.config = config or OutputFormatConfig()
    
    @property
    def use_case(self) -> ValidationUseCase:
        return ValidationUseCase.OUTPUT_FORMAT
    
    async def _execute_validation(
        self, 
        question: Question
    ) -> UseCaseValidationResult:
        """Execute output format validation."""
        issues: List = []
        
        if not question.test_cases:
            issues.append(self._create_issue(
                message="No test cases to validate output format",
                field="test_cases",
                severity=ValidationSeverity.ERROR
            ))
            return self._create_result(passed=False, issues=issues)
        
        # Detect output formats for each test case
        formats = []
        for i, test_case in enumerate(question.test_cases):
            detected_format = self._detect_output_format(test_case.expected_output)
            formats.append((i, detected_format, test_case.expected_output))
        
        # Check for format consistency
        issues.extend(self._check_format_consistency(formats))
        
        # Validate each output format
        for i, test_case in enumerate(question.test_cases):
            issues.extend(self._validate_single_output(test_case.expected_output, i))
        
        # Check examples match test case format
        issues.extend(self._check_examples_consistency(question))
        
        passed = not any(
            issue.severity == ValidationSeverity.ERROR 
            for issue in issues
        )
        
        return self._create_result(passed=passed, issues=issues)
    
    def _detect_output_format(self, output: str) -> str:
        """
        Detect the format of an output string.
        
        Returns one of: json_array, json_object, number, string, boolean
        """
        output = output.strip()
        
        # Try JSON array
        if output.startswith('[') and output.endswith(']'):
            try:
                parsed = json.loads(output)
                if isinstance(parsed, list):
                    return self.FORMAT_JSON_ARRAY
            except json.JSONDecodeError:
                pass
        
        # Try JSON object
        if output.startswith('{') and output.endswith('}'):
            try:
                parsed = json.loads(output)
                if isinstance(parsed, dict):
                    return self.FORMAT_JSON_OBJECT
            except json.JSONDecodeError:
                pass
        
        # Try number
        try:
            float(output)
            return self.FORMAT_NUMBER
        except ValueError:
            pass
        
        # Try boolean
        if output.lower() in ('true', 'false'):
            return self.FORMAT_BOOLEAN
        
        # Default to string
        return self.FORMAT_STRING
    
    def _check_format_consistency(self, formats: List) -> List:
        """Check that all test cases have consistent output format."""
        issues = []
        
        # Get unique formats (excluding mixed)
        unique_formats = set(f[1] for f in formats)
        
        if len(unique_formats) > 1:
            # Check if formats are compatible
            # Numbers and strings can sometimes be compatible
            # JSON arrays and objects are not compatible
            
            incompatible_groups = {
                self.FORMAT_JSON_ARRAY,
                self.FORMAT_JSON_OBJECT,
            }
            
            if unique_formats & incompatible_groups and len(unique_formats & incompatible_groups) > 1:
                issues.append(self._create_issue(
                    message="Inconsistent output formats: mixing JSON arrays and objects",
                    field="test_cases",
                    severity=ValidationSeverity.ERROR,
                    details={
                        "formats_found": list(unique_formats),
                        "test_cases": [
                            {"index": f[0], "format": f[1], "output": f[2][:50]}
                            for f in formats
                        ]
                    }
                ))
            elif unique_formats & incompatible_groups and (unique_formats - incompatible_groups):
                issues.append(self._create_issue(
                    message="Inconsistent output formats: mixing JSON with primitive types",
                    field="test_cases",
                    severity=ValidationSeverity.ERROR,
                    details={
                        "formats_found": list(unique_formats)
                    }
                ))
            else:
                # Minor inconsistency (e.g., number vs string)
                issues.append(self._create_issue(
                    message=f"Minor output format inconsistency detected: {', '.join(unique_formats)}",
                    field="test_cases",
                    severity=ValidationSeverity.WARNING,
                    details={"formats_found": list(unique_formats)}
                ))
        
        return issues
    
    def _validate_single_output(self, output: str, index: int) -> List:
        """Validate a single output format."""
        issues = []
        
        output = output.strip()
        
        # Check for empty output
        if not output:
            issues.append(self._create_issue(
                message=f"Test case {index + 1} has empty expected output",
                field=f"test_cases[{index}].expected_output",
                test_case_index=index,
                severity=ValidationSeverity.WARNING
            ))
            return issues
        
        # Validate JSON outputs
        if output.startswith('[') or output.startswith('{'):
            try:
                parsed = json.loads(output)
                # Check for valid JSON structure
                issues.extend(self._validate_json_structure(parsed, index))
            except json.JSONDecodeError as e:
                issues.append(self._create_issue(
                    message=f"Test case {index + 1} has invalid JSON output: {str(e)}",
                    field=f"test_cases[{index}].expected_output",
                    test_case_index=index,
                    severity=ValidationSeverity.ERROR,
                    details={"error": str(e)}
                ))
        
        # Validate boolean outputs
        if output.lower() in ('true', 'false'):
            # Ensure consistent casing
            if output != output.lower():
                issues.append(self._create_issue(
                    message=f"Test case {index + 1} boolean output should be lowercase",
                    field=f"test_cases[{index}].expected_output",
                    test_case_index=index,
                    severity=ValidationSeverity.INFO,
                    details={"output": output}
                ))
        
        # Check for trailing whitespace or newlines
        if output != output.strip():
            issues.append(self._create_issue(
                message=f"Test case {index + 1} output has leading/trailing whitespace",
                field=f"test_cases[{index}].expected_output",
                test_case_index=index,
                severity=ValidationSeverity.INFO
            ))
        
        return issues
    
    def _validate_json_structure(self, parsed, index: int) -> List:
        """Validate JSON structure for common issues."""
        issues = []
        
        if isinstance(parsed, list):
            # Check for empty array
            if len(parsed) == 0:
                issues.append(self._create_issue(
                    message=f"Test case {index + 1} returns empty array - ensure this is intentional",
                    field=f"test_cases[{index}].expected_output",
                    test_case_index=index,
                    severity=ValidationSeverity.INFO
                ))
            
            # Check for inconsistent element types
            if len(parsed) > 1:
                element_types = set(type(e).__name__ for e in parsed)
                if len(element_types) > 1:
                    issues.append(self._create_issue(
                        message=f"Test case {index + 1} array has mixed element types",
                        field=f"test_cases[{index}].expected_output",
                        test_case_index=index,
                        severity=ValidationSeverity.WARNING,
                        details={"types": list(element_types)}
                    ))
        
        return issues
    
    def _check_examples_consistency(self, question: Question) -> List:
        """Check that examples have consistent output format with test cases."""
        issues = []
        
        if not question.examples:
            return issues
        
        # Get format from test cases
        if question.test_cases:
            test_case_format = self._detect_output_format(
                question.test_cases[0].expected_output
            )
            
            # Check each example
            for i, example in enumerate(question.examples):
                example_format = self._detect_output_format(example.output)
                
                if example_format != test_case_format:
                    # Check if formats are compatible
                    if self._are_formats_compatible(example_format, test_case_format):
                        issues.append(self._create_issue(
                            message=f"Example {i + 1} output format differs from test cases",
                            field=f"examples[{i}].output",
                            severity=ValidationSeverity.INFO,
                            details={
                                "example_format": example_format,
                                "test_case_format": test_case_format
                            }
                        ))
                    else:
                        issues.append(self._create_issue(
                            message=f"Example {i + 1} output format is incompatible with test cases",
                            field=f"examples[{i}].output",
                            severity=ValidationSeverity.WARNING,
                            details={
                                "example_format": example_format,
                                "test_case_format": test_case_format
                            }
                        ))
        
        return issues
    
    def _are_formats_compatible(self, format1: str, format2: str) -> bool:
        """Check if two output formats are compatible."""
        # Same format is always compatible
        if format1 == format2:
            return True
        
        # Number and string can be compatible
        number_string = {self.FORMAT_NUMBER, self.FORMAT_STRING}
        if format1 in number_string and format2 in number_string:
            return True
        
        # Boolean and string can be compatible
        boolean_string = {self.FORMAT_BOOLEAN, self.FORMAT_STRING}
        if format1 in boolean_string and format2 in boolean_string:
            return True
        
        return False
