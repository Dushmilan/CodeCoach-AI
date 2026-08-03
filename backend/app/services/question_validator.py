"""Question validation — facade service.

Orchestrates validation use cases that now live in
app.use_cases.question_validation.*. Re-exports use case classes here
for backward compatibility.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from app.ports.code_executor import CodeExecutor
from app.models.schemas import Question
from app.models.question_validation_schemas import (
    QuestionValidationResult,
    QuestionValidationConfig,
    UseCaseValidationResult,
    ValidationUseCase,
    ValidationSeverity,
)

from app.use_cases.question_validation import (
    BaseValidationUseCase,
    StructureValidationUseCase,
    TestCaseValidationUseCase,
    StarterCodeValidationUseCase,
    SolutionValidationUseCase,
    TimeLimitValidationUseCase,
    FunctionSignatureValidationUseCase,
    OutputFormatValidationUseCase,
)

logger = logging.getLogger(__name__)


class QuestionValidatorService:
    """Service orchestrating all validation strategies through a single interface."""

    def __init__(
        self,
        executor: Optional[CodeExecutor] = None,
        config: Optional[QuestionValidationConfig] = None,
    ):
        self.executor = executor
        self.config = config or QuestionValidationConfig()
        self._init_use_cases()

    def _init_use_cases(self):
        self.use_cases: Dict[ValidationUseCase, BaseValidationUseCase] = {
            ValidationUseCase.STRUCTURE: StructureValidationUseCase(),
            ValidationUseCase.TEST_CASES: TestCaseValidationUseCase(
                executor=self.executor, config=self.config.test_cases
            ),
            ValidationUseCase.STARTER_CODE: StarterCodeValidationUseCase(
                executor=self.executor
            ),
            ValidationUseCase.SOLUTION: SolutionValidationUseCase(
                executor=self.executor
            ),
            ValidationUseCase.TIME_LIMITS: TimeLimitValidationUseCase(
                config=self.config.time_limits
            ),
            ValidationUseCase.FUNCTION_SIGNATURE: FunctionSignatureValidationUseCase(
                config=self.config.function_signature
            ),
            ValidationUseCase.OUTPUT_FORMAT: OutputFormatValidationUseCase(
                config=self.config.output_format
            ),
        }

    async def validate_question(
        self, question: Question, use_cases: Optional[List[ValidationUseCase]] = None
    ) -> QuestionValidationResult:
        use_cases_to_run = use_cases or list(self.use_cases.keys())
        use_cases_to_run = [
            uc for uc in use_cases_to_run if uc not in self.config.skip_use_cases
        ]
        results: Dict[ValidationUseCase, UseCaseValidationResult] = {}
        for use_case_enum in use_cases_to_run:
            use_case = self.use_cases.get(use_case_enum)
            if use_case is None:
                logger.warning("Unknown use case: %s", use_case_enum)
                continue
            try:
                result = await use_case.execute(question)
                results[use_case_enum] = result
            except Exception as e:
                logger.error("Error running %s: %s", use_case_enum, e)
                results[use_case_enum] = UseCaseValidationResult(
                    use_case=use_case_enum, passed=False, issues=[]
                )
        total_issues = sum(len(r.issues) for r in results.values())
        error_count = sum(
            1
            for r in results.values()
            for issue in r.issues
            if issue.severity == ValidationSeverity.ERROR
        )
        warning_count = sum(
            1
            for r in results.values()
            for issue in r.issues
            if issue.severity == ValidationSeverity.WARNING
        )
        valid = error_count == 0
        if self.config.fail_on_warnings and warning_count > 0:
            valid = False
        return QuestionValidationResult(
            question_id=question.id,
            valid=valid,
            results=results,
            total_issues=total_issues,
            error_count=error_count,
            warning_count=warning_count,
        )

    async def validate_batch(
        self, questions: List[Question]
    ) -> List[QuestionValidationResult]:
        results = await asyncio.gather(
            *[self.validate_question(question) for question in questions]
        )
        return list(results)

    def get_use_case_order(self) -> List[ValidationUseCase]:
        return [
            ValidationUseCase.STRUCTURE,
            ValidationUseCase.OUTPUT_FORMAT,
            ValidationUseCase.TIME_LIMITS,
            ValidationUseCase.FUNCTION_SIGNATURE,
            ValidationUseCase.TEST_CASES,
            ValidationUseCase.STARTER_CODE,
            ValidationUseCase.SOLUTION,
        ]

    async def quick_validate(self, question: Question) -> QuestionValidationResult:
        return await self.validate_question(
            question,
            use_cases=[
                ValidationUseCase.STRUCTURE,
                ValidationUseCase.OUTPUT_FORMAT,
                ValidationUseCase.TIME_LIMITS,
                ValidationUseCase.FUNCTION_SIGNATURE,
            ],
        )

    async def full_validate(self, question: Question) -> QuestionValidationResult:
        return await self.validate_question(question)

    def get_validation_summary(
        self, result: QuestionValidationResult
    ) -> Dict[str, Any]:
        summary: Dict[str, Any] = {
            "question_id": result.question_id,
            "valid": result.valid,
            "total_issues": result.total_issues,
            "error_count": result.error_count,
            "warning_count": result.warning_count,
            "use_cases_run": len(result.results),
            "use_cases_passed": sum(1 for r in result.results.values() if r.passed),
            "issues_by_use_case": {},
        }
        for use_case, uc_result in result.results.items():
            issues = [
                {
                    "severity": issue.severity.value,
                    "message": issue.message,
                    "field": issue.field,
                }
                for issue in uc_result.issues
            ]
            summary["issues_by_use_case"][use_case.value] = {
                "passed": uc_result.passed,
                "issue_count": len(issues),
                "issues": issues,
            }
        return summary
