"""
Base class for validation use cases.

This module provides the abstract base class that all validation use cases
must inherit from, ensuring consistent interface and behavior.
"""

from abc import ABC, abstractmethod
from typing import Optional
import time

from app.models.schemas import Question
from app.models.question_validation_schemas import (
    UseCaseValidationResult,
    ValidationUseCase,
    ValidationIssue,
    ValidationSeverity,
)


class BaseValidationUseCase(ABC):
    """
    Abstract base class for question validation use cases.
    
    Each use case validates a specific aspect of a question:
    - Structure: Required fields, types, and basic validity
    - Test Cases: Executability and correctness of test cases
    - Starter Code: Compiles/runs without errors
    - Solution: Reference solution passes all tests
    - Time Limits: Reasonable time complexity and limits
    - Function Signature: Proper function definitions
    - Output Format: Consistent output formats
    """
    
    @property
    @abstractmethod
    def use_case(self) -> ValidationUseCase:
        """Return the validation use case type."""
        pass
    
    @abstractmethod
    async def _execute_validation(
        self, 
        question: Question
    ) -> UseCaseValidationResult:
        """
        Execute the actual validation logic.
        
        Args:
            question: The question to validate
            
        Returns:
            UseCaseValidationResult with validation outcome
        """
        pass
    
    async def execute(self, question: Question) -> UseCaseValidationResult:
        """
        Execute validation with timing and error handling.
        
        Args:
            question: The question to validate
            
        Returns:
            UseCaseValidationResult with validation outcome
        """
        start_time = time.time()
        
        try:
            result = await self._execute_validation(question)
        except Exception as e:
            # Handle unexpected errors
            result = UseCaseValidationResult(
                use_case=self.use_case,
                passed=False,
                issues=[
                    ValidationIssue(
                        use_case=self.use_case,
                        severity=ValidationSeverity.ERROR,
                        message=f"Validation failed with error: {str(e)}"
                    )
                ]
            )
        
        # Record execution time
        execution_time_ms = (time.time() - start_time) * 1000
        result.execution_time_ms = execution_time_ms
        
        return result
    
    def _create_issue(
        self,
        message: str,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
        field: Optional[str] = None,
        language: Optional[str] = None,
        test_case_index: Optional[int] = None,
        details: Optional[dict] = None
    ) -> ValidationIssue:
        """
        Helper method to create a validation issue.
        
        Args:
            message: Human-readable description
            severity: Issue severity level
            field: The field with the issue
            language: Language if applicable
            test_case_index: Test case index if applicable
            details: Additional details
            
        Returns:
            ValidationIssue instance
        """
        return ValidationIssue(
            use_case=self.use_case,
            severity=severity,
            message=message,
            field=field,
            language=language,
            test_case_index=test_case_index,
            details=details
        )
    
    def _create_result(
        self,
        passed: bool,
        issues: list = None
    ) -> UseCaseValidationResult:
        """
        Helper method to create a validation result.
        
        Args:
            passed: Whether validation passed
            issues: List of validation issues
            
        Returns:
            UseCaseValidationResult instance
        """
        return UseCaseValidationResult(
            use_case=self.use_case,
            passed=passed,
            issues=issues or []
        )
