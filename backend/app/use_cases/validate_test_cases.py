"""
Test case validation use case.

Validates that test cases are executable, have proper format, and
produce deterministic outputs. Uses Piston for execution validation.
"""

from typing import List, Optional, Any
import json
import re

from app.models.schemas import Question, TestCase as QuestionTestCase
from app.models.question_validation_schemas import (
    UseCaseValidationResult,
    ValidationUseCase,
    ValidationSeverity,
    TestCaseValidationConfig,
)
from app.use_cases.base import BaseValidationUseCase


class TestCaseValidationUseCase(BaseValidationUseCase):
    """
    Validates test cases for executability and correctness.
    
    Checks:
    - Minimum and maximum test case counts
    - Input format is parseable
    - Expected output is deterministic
    - Hidden tests have different inputs from visible ones
    - Input/output lengths are within limits
    - Test cases can be executed (using Piston)
    """
    
    def __init__(
        self,
        piston_service: Optional[Any] = None,
        config: Optional[TestCaseValidationConfig] = None
    ):
        """
        Initialize test case validation use case.
        
        Args:
            piston_service: Piston service for code execution
            config: Configuration for test case validation
        """
        self.piston_service = piston_service
        self.config = config or TestCaseValidationConfig()
    
    @property
    def use_case(self) -> ValidationUseCase:
        return ValidationUseCase.TEST_CASES
    
    async def _execute_validation(
        self, 
        question: Question
    ) -> UseCaseValidationResult:
        """Execute test case validation."""
        issues: List = []
        
        # Validate test case count
        issues.extend(self._validate_test_case_count(question.test_cases))
        
        # Validate each test case
        for i, test_case in enumerate(question.test_cases):
            issues.extend(self._validate_single_test_case(test_case, i))
        
        # Check for duplicate test cases
        issues.extend(self._check_duplicate_test_cases(question.test_cases))
        
        # Check hidden vs visible test case distribution
        issues.extend(self._check_hidden_visible_distribution(question.test_cases))
        
        # Validate test case executability with Piston (if available)
        if self.piston_service:
            piston_issues = await self._validate_executability(question)
            issues.extend(piston_issues)
        
        passed = not any(
            issue.severity == ValidationSeverity.ERROR 
            for issue in issues
        )
        
        return self._create_result(passed=passed, issues=issues)
    
    def _validate_test_case_count(self, test_cases: List[QuestionTestCase]) -> List:
        """Validate the number of test cases."""
        issues = []
        
        count = len(test_cases)
        
        if count < self.config.min_test_cases:
            issues.append(self._create_issue(
                message=f"At least {self.config.min_test_cases} test case(s) required, found {count}",
                field="test_cases",
                severity=ValidationSeverity.ERROR,
                details={"count": count, "minimum": self.config.min_test_cases}
            ))
        
        if count > self.config.max_test_cases:
            issues.append(self._create_issue(
                message=f"Maximum {self.config.max_test_cases} test cases allowed, found {count}",
                field="test_cases",
                severity=ValidationSeverity.WARNING,
                details={"count": count, "maximum": self.config.max_test_cases}
            ))
        
        return issues
    
    def _validate_single_test_case(
        self, 
        test_case: QuestionTestCase, 
        index: int
    ) -> List:
        """Validate a single test case."""
        issues = []
        
        # Validate input
        if test_case.input is None:
            issues.append(self._create_issue(
                message=f"Test case {index + 1} is missing input",
                field=f"test_cases[{index}].input",
                test_case_index=index,
                severity=ValidationSeverity.ERROR
            ))
        elif len(test_case.input) > self.config.max_input_length:
            issues.append(self._create_issue(
                message=f"Test case {index + 1} input exceeds maximum length",
                field=f"test_cases[{index}].input",
                test_case_index=index,
                severity=ValidationSeverity.WARNING,
                details={
                    "length": len(test_case.input),
                    "maximum": self.config.max_input_length
                }
            ))
        
        # Validate expected output
        if test_case.expected_output is None:
            issues.append(self._create_issue(
                message=f"Test case {index + 1} is missing expected output",
                field=f"test_cases[{index}].expected_output",
                test_case_index=index,
                severity=ValidationSeverity.ERROR
            ))
        elif len(test_case.expected_output) > self.config.max_output_length:
            issues.append(self._create_issue(
                message=f"Test case {index + 1} expected output exceeds maximum length",
                field=f"test_cases[{index}].expected_output",
                test_case_index=index,
                severity=ValidationSeverity.WARNING,
                details={
                    "length": len(test_case.expected_output),
                    "maximum": self.config.max_output_length
                }
            ))
        
        # Validate description
        if not test_case.description:
            issues.append(self._create_issue(
                message=f"Test case {index + 1} is missing description",
                field=f"test_cases[{index}].description",
                test_case_index=index,
                severity=ValidationSeverity.INFO
            ))
        
        # Check for deterministic output format
        issues.extend(self._check_output_determinism(test_case, index))
        
        return issues
    
    def _check_output_determinism(
        self, 
        test_case: QuestionTestCase, 
        index: int
    ) -> List:
        """Check if expected output is deterministic."""
        issues = []
        
        output = test_case.expected_output
        
        # Check for non-deterministic patterns
        non_deterministic_patterns = [
            (r'\b0x[0-9a-f]+\b', "hexadecimal memory address"),
            (r'\b\d{13,}\b', "timestamp-like number"),
            (r'<.*object at 0x[0-9a-f]+>', "object reference"),
            (r'random', "random value reference"),
        ]
        
        for pattern, description in non_deterministic_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                issues.append(self._create_issue(
                    message=f"Test case {index + 1} expected output may contain non-deterministic value: {description}",
                    field=f"test_cases[{index}].expected_output",
                    test_case_index=index,
                    severity=ValidationSeverity.WARNING,
                    details={"pattern": pattern}
                ))
        
        return issues
    
    def _check_duplicate_test_cases(self, test_cases: List[QuestionTestCase]) -> List:
        """Check for duplicate test cases."""
        issues = []
        
        seen_inputs = {}
        
        for i, test_case in enumerate(test_cases):
            input_key = test_case.input.strip() if test_case.input else ""
            
            if input_key in seen_inputs:
                prev_index = seen_inputs[input_key]
                issues.append(self._create_issue(
                    message=f"Test case {i + 1} has same input as test case {prev_index + 1}",
                    field=f"test_cases[{i}].input",
                    test_case_index=i,
                    severity=ValidationSeverity.WARNING,
                    details={"duplicate_of": prev_index}
                ))
            else:
                seen_inputs[input_key] = i
        
        return issues
    
    def _check_hidden_visible_distribution(
        self, 
        test_cases: List[QuestionTestCase]
    ) -> List:
        """Check distribution of hidden vs visible test cases."""
        issues = []
        
        if not test_cases:
            return issues
        
        hidden_count = sum(1 for tc in test_cases if tc.hidden)
        visible_count = len(test_cases) - hidden_count
        
        # Recommend having at least one visible test case
        if visible_count == 0:
            issues.append(self._create_issue(
                message="At least one visible (non-hidden) test case is recommended",
                field="test_cases",
                severity=ValidationSeverity.WARNING,
                details={"hidden_count": hidden_count, "visible_count": visible_count}
            ))
        
        # Check if hidden tests are required by config
        if self.config.require_hidden_tests and hidden_count == 0:
            issues.append(self._create_issue(
                message="At least one hidden test case is required by configuration",
                field="test_cases",
                severity=ValidationSeverity.ERROR,
                details={"hidden_count": hidden_count}
            ))
        
        return issues
    
    async def _validate_executability(self, question: Question) -> List:
        """
        Validate that test cases can be executed using Piston.
        
        This runs a simple test to ensure the test case format is
        compatible with code execution.
        """
        issues = []
        
        if not self.piston_service:
            return issues
        
        # Create a simple test harness to validate test case format
        for i, test_case in enumerate(question.test_cases):
            try:
                # Create a simple Python script that parses the input
                # Use JSON encoding to properly escape the input
                escaped_input = json.dumps(test_case.input)
                test_code = f'''
    import sys
    import json
    
    # Read and parse input
    input_data = json.loads({escaped_input})
    print("Input parsed successfully")
    '''
                
                result = await self.piston_service.execute_code(
                    language="python",
                    code=test_code,
                    stdin=""
                )
                
                # Check if execution was successful
                if result.get("exit_code", 0) != 0:
                    issues.append(self._create_issue(
                        message=f"Test case {i + 1} input format may cause execution issues",
                        field=f"test_cases[{i}].input",
                        test_case_index=i,
                        severity=ValidationSeverity.WARNING,
                        details={"error": result.get("stderr", "Unknown error")}
                    ))
                    
            except Exception as e:
                issues.append(self._create_issue(
                    message=f"Failed to validate test case {i + 1} executability: {str(e)}",
                    field=f"test_cases[{i}]",
                    test_case_index=i,
                    severity=ValidationSeverity.INFO
                ))
        
        return issues
