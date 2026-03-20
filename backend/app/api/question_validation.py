"""
Question validation API endpoints.

Provides endpoints for validating questions before they are made available to users.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from functools import lru_cache

from app.models.schemas import Question
from app.models.question_validation_schemas import (
    QuestionValidationResult,
    QuestionValidationConfig,
    ValidationUseCase,
)
from app.services.question_validator import QuestionValidatorService
from app.services.piston_service import PistonService

router = APIRouter()


@lru_cache()
def get_piston_service() -> PistonService:
    """Get or create Piston service instance (cached)."""
    return PistonService()


@lru_cache()
def get_validator_service() -> QuestionValidatorService:
    """Get or create validator service instance (cached)."""
    return QuestionValidatorService(piston_service=get_piston_service())


@router.post("/validate", response_model=QuestionValidationResult)
async def validate_question(
    question: Question,
    validator: QuestionValidatorService = Depends(get_validator_service)
):
    """
    Validate a single question.
    
    Runs all validation use cases against the provided question and returns
    detailed results including any issues found.
    
    Example request body:
    {
        "id": "two-sum",
        "title": "Two Sum",
        "difficulty": "easy",
        "category": "Arrays",
        "description": "...",
        "starter": {...},
        "test_cases": [...],
        ...
    }
    """
    try:
        result = await validator.validate_question(question)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation error: {str(e)}"
        )


@router.post("/validate/quick")
async def quick_validate_question(
    question: Question,
    validator: QuestionValidatorService = Depends(get_validator_service)
):
    """
    Run quick validation on a question.
    
    Only runs fast validation use cases (structure, output format, time limits,
    function signature). Skips slower validations like solution execution.
    """
    try:
        result = await validator.quick_validate(question)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation error: {str(e)}"
        )


@router.post("/validate/use-cases")
async def validate_with_specific_use_cases(
    question: Question,
    use_cases: List[str],
    validator: QuestionValidatorService = Depends(get_validator_service)
):
    """
    Validate a question with specific use cases only.
    
    Args:
        question: The question to validate
        use_cases: List of use case names to run
        
    Valid use case names:
        - structure
        - test_cases
        - starter_code
        - solution
        - time_limits
        - function_signature
        - output_format
    """
    try:
        # Convert string use cases to enum
        use_case_enums = []
        for uc in use_cases:
            try:
                use_case_enums.append(ValidationUseCase(uc))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid use case: {uc}"
                )
        
        result = await validator.validate_question(question, use_cases=use_case_enums)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation error: {str(e)}"
        )


@router.post("/batch-validate")
async def batch_validate_questions(
    questions: List[Question],
    validator: QuestionValidatorService = Depends(get_validator_service)
):
    """
    Validate multiple questions at once.
    
    Runs full validation on each question and returns a list of results.
    """
    try:
        results = await validator.validate_batch(questions)
        return {
            "total": len(results),
            "valid_count": sum(1 for r in results if r.valid),
            "invalid_count": sum(1 for r in results if not r.valid),
            "results": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch validation error: {str(e)}"
        )


@router.get("/use-cases")
async def get_available_use_cases():
    """Get list of all available validation use cases."""
    return {
        "use_cases": [
            {
                "name": uc.value,
                "description": _get_use_case_description(uc)
            }
            for uc in ValidationUseCase
        ]
    }


@router.get("/config")
async def get_validation_config():
    """Get current validation configuration."""
    return {
        "config": {
            "test_cases": {
                "min_test_cases": 2,
                "max_test_cases": 50,
                "max_input_length": 10000,
                "max_output_length": 10000,
            },
            "time_limits": {
                "default_time_limit_ms": 3000,
                "max_time_limit_ms": 10000,
                "min_time_limit_ms": 100,
            },
            "function_signature": {
                "require_type_hints": True,
            },
            "output_format": {
                "normalize_whitespace": True,
                "case_sensitive": False,
            }
        }
    }


@router.post("/summary")
async def get_validation_summary(
    result: QuestionValidationResult,
    validator: QuestionValidatorService = Depends(get_validator_service)
):
    """
    Get a human-readable summary of validation results.
    
    This endpoint takes a validation result and returns a formatted summary
    suitable for display.
    """
    try:
        summary = validator.get_validation_summary(result)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating summary: {str(e)}"
        )


def _get_use_case_description(use_case: ValidationUseCase) -> str:
    """Get human-readable description for a use case."""
    descriptions = {
        ValidationUseCase.STRUCTURE: (
            "Validates question structure including required fields, "
            "field types, and basic data integrity."
        ),
        ValidationUseCase.TEST_CASES: (
            "Validates test cases for executability, proper format, "
            "and deterministic outputs."
        ),
        ValidationUseCase.STARTER_CODE: (
            "Validates that starter code for all languages compiles "
            "and runs without errors."
        ),
        ValidationUseCase.SOLUTION: (
            "Validates that the reference solution passes all test cases. "
            "This is the most critical validation."
        ),
        ValidationUseCase.TIME_LIMITS: (
            "Validates time complexity and time limits are reasonable "
            "for the problem difficulty."
        ),
        ValidationUseCase.FUNCTION_SIGNATURE: (
            "Validates function signatures in starter code are properly "
            "defined with correct types."
        ),
        ValidationUseCase.OUTPUT_FORMAT: (
            "Validates expected outputs have consistent formats across "
            "all test cases."
        ),
        ValidationUseCase.CONSTRAINTS: (
            "Validates problem constraints are properly defined and "
            "test cases respect them."
        ),
        ValidationUseCase.DIFFICULTY: (
            "Validates difficulty level matches problem complexity."
        ),
    }
    return descriptions.get(use_case, "No description available.")
