"""Base validation use case abstraction."""

import time
from abc import ABC, abstractmethod
from typing import List, Optional

from app.models.schemas import Question
from app.models.question_validation_schemas import (
    UseCaseValidationResult,
    ValidationUseCase,
    ValidationSeverity,
    ValidationIssue,
)


class BaseValidationUseCase(ABC):
    """Abstract base for a single validation strategy."""

    @property
    @abstractmethod
    def use_case(self) -> ValidationUseCase:
        pass

    @abstractmethod
    async def _execute_validation(self, question: Question) -> UseCaseValidationResult:
        pass

    async def execute(self, question: Question) -> UseCaseValidationResult:
        start_time = time.time()
        try:
            result = await self._execute_validation(question)
        except Exception as e:
            result = UseCaseValidationResult(
                use_case=self.use_case,
                passed=False,
                issues=[
                    ValidationIssue(
                        use_case=self.use_case,
                        severity=ValidationSeverity.ERROR,
                        message=f"Validation failed with error: {str(e)}",
                    )
                ],
            )
        result.execution_time_ms = (time.time() - start_time) * 1000
        return result

    def _create_issue(
        self,
        message: str,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
        field: Optional[str] = None,
        language: Optional[str] = None,
        test_case_index: Optional[int] = None,
        details: Optional[dict] = None,
    ) -> ValidationIssue:
        return ValidationIssue(
            use_case=self.use_case,
            severity=severity,
            message=message,
            field=field,
            language=language,
            test_case_index=test_case_index,
            details=details,
        )

    def _create_result(
        self, passed: bool, issues: Optional[List] = None
    ) -> UseCaseValidationResult:
        return UseCaseValidationResult(
            use_case=self.use_case, passed=passed, issues=issues or []
        )
