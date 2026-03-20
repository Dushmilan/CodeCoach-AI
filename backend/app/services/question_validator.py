"""
Question Validator Service.

Orchestrates all validation use cases to provide comprehensive question validation.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from app.models.schemas import Question
from app.models.question_validation_schemas import (
    QuestionValidationResult,
    QuestionValidationConfig,
    UseCaseValidationResult,
    ValidationUseCase,
    ValidationSeverity,
)
from app.use_cases.validate_structure import StructureValidationUseCase
from app.use_cases.validate_test_cases import TestCaseValidationUseCase
from app.use_cases.validate_starter_code import StarterCodeValidationUseCase
from app.use_cases.validate_solution import SolutionValidationUseCase
from app.use_cases.validate_time_limits import TimeLimitValidationUseCase
from app.use_cases.validate_function_signature import FunctionSignatureValidationUseCase
from app.use_cases.validate_output_format import OutputFormatValidationUseCase

logger = logging.getLogger(__name__)


class QuestionValidatorService:
    """
    Service for validating questions before they are made available to users.
    
    This service orchestrates all validation use cases and provides a single
    entry point for question validation.
    """
    
    def __init__(
        self,
        piston_service: Optional[Any] = None,
        config: Optional[QuestionValidationConfig] = None
    ):
        """
        Initialize the question validator service.
        
        Args:
            piston_service: Piston service for code execution
            config: Validation configuration
        """
        self.piston_service = piston_service
        self.config = config or QuestionValidationConfig()
        
        # Initialize use cases
        self._init_use_cases()
    
    def _init_use_cases(self):
        """Initialize all validation use cases."""
        self.use_cases: Dict[ValidationUseCase, Any] = {
            ValidationUseCase.STRUCTURE: StructureValidationUseCase(),
            ValidationUseCase.TEST_CASES: TestCaseValidationUseCase(
                piston_service=self.piston_service,
                config=self.config.test_cases
            ),
            ValidationUseCase.STARTER_CODE: StarterCodeValidationUseCase(
                piston_service=self.piston_service
            ),
            ValidationUseCase.SOLUTION: SolutionValidationUseCase(
                piston_service=self.piston_service
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
        self, 
        question: Question,
        use_cases: Optional[List[ValidationUseCase]] = None
    ) -> QuestionValidationResult:
        """
        Validate a question using all or specified use cases.
        
        Args:
            question: The question to validate
            use_cases: Specific use cases to run (None = all)
            
        Returns:
            QuestionValidationResult with complete validation outcome
        """
        # Determine which use cases to run
        use_cases_to_run = use_cases or list(self.use_cases.keys())
        
        # Filter out skipped use cases
        use_cases_to_run = [
            uc for uc in use_cases_to_run 
            if uc not in self.config.skip_use_cases
        ]
        
        # Run each use case
        results: Dict[ValidationUseCase, UseCaseValidationResult] = {}
        
        for use_case_enum in use_cases_to_run:
            use_case = self.use_cases.get(use_case_enum)
            
            if use_case is None:
                logger.warning(f"Unknown use case: {use_case_enum}")
                continue
            
            try:
                result = await use_case.execute(question)
                results[use_case_enum] = result
            except Exception as e:
                logger.error(f"Error running {use_case_enum}: {e}")
                results[use_case_enum] = UseCaseValidationResult(
                    use_case=use_case_enum,
                    passed=False,
                    issues=[]
                )
        
        # Calculate totals
        total_issues = sum(len(r.issues) for r in results.values())
        error_count = sum(
            1 for r in results.values() 
            for issue in r.issues 
            if issue.severity == ValidationSeverity.ERROR
        )
        warning_count = sum(
            1 for r in results.values() 
            for issue in r.issues 
            if issue.severity == ValidationSeverity.WARNING
        )
        
        # Determine overall validity
        valid = error_count == 0
        
        # If fail_on_warnings is True, also check warnings
        if self.config.fail_on_warnings and warning_count > 0:
            valid = False
        
        return QuestionValidationResult(
            question_id=question.id,
            valid=valid,
            results=results,
            total_issues=total_issues,
            error_count=error_count,
            warning_count=warning_count,
            validated_at=datetime.utcnow()
        )
    
    async def validate_batch(
        self, 
        questions: List[Question]
    ) -> List[QuestionValidationResult]:
        """
        Validate multiple questions.
        
        Args:
            questions: List of questions to validate
            
        Returns:
            List of validation results
        """
        results = []
        
        for question in questions:
            result = await self.validate_question(question)
            results.append(result)
        
        return results
    
    def get_use_case_order(self) -> List[ValidationUseCase]:
        """
        Get the recommended order for running use cases.
        
        Use cases are ordered from fastest to slowest, and from
        basic to complex checks.
        """
        return [
            ValidationUseCase.STRUCTURE,      # Fast, basic checks
            ValidationUseCase.OUTPUT_FORMAT,  # Fast, format checks
            ValidationUseCase.TIME_LIMITS,    # Fast, complexity checks
            ValidationUseCase.FUNCTION_SIGNATURE,  # Fast, signature checks
            ValidationUseCase.TEST_CASES,     # Medium, may use Piston
            ValidationUseCase.STARTER_CODE,   # Slower, uses Piston
            ValidationUseCase.SOLUTION,       # Slowest, runs all tests
        ]
    
    async def quick_validate(self, question: Question) -> QuestionValidationResult:
        """
        Run a quick validation with only fast use cases.
        
        This is useful for initial checks before running full validation.
        
        Args:
            question: The question to validate
            
        Returns:
            QuestionValidationResult from quick validation
        """
        quick_use_cases = [
            ValidationUseCase.STRUCTURE,
            ValidationUseCase.OUTPUT_FORMAT,
            ValidationUseCase.TIME_LIMITS,
            ValidationUseCase.FUNCTION_SIGNATURE,
        ]
        
        return await self.validate_question(question, use_cases=quick_use_cases)
    
    async def full_validate(self, question: Question) -> QuestionValidationResult:
        """
        Run full validation including all use cases.
        
        This includes slow validations like solution execution.
        
        Args:
            question: The question to validate
            
        Returns:
            QuestionValidationResult from full validation
        """
        return await self.validate_question(question)
    
    def get_validation_summary(
        self, 
        result: QuestionValidationResult
    ) -> Dict[str, Any]:
        """
        Get a summary of validation results.
        
        Args:
            result: The validation result
            
        Returns:
            Dictionary with validation summary
        """
        summary = {
            "question_id": result.question_id,
            "valid": result.valid,
            "total_issues": result.total_issues,
            "error_count": result.error_count,
            "warning_count": result.warning_count,
            "use_cases_run": len(result.results),
            "use_cases_passed": sum(1 for r in result.results.values() if r.passed),
            "issues_by_use_case": {},
        }
        
        # Group issues by use case
        for use_case, uc_result in result.results.items():
            issues = []
            for issue in uc_result.issues:
                issues.append({
                    "severity": issue.severity.value,
                    "message": issue.message,
                    "field": issue.field,
                })
            
            summary["issues_by_use_case"][use_case.value] = {
                "passed": uc_result.passed,
                "issue_count": len(issues),
                "issues": issues,
            }
        
        return summary
