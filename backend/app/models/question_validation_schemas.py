"""
Schemas for question validation use cases.

This module defines the models for validating questions before they are
made available to users. Each validation use case has its own result model.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class ValidationSeverity(str, Enum):
    """Severity level for validation issues."""
    ERROR = "error"      # Critical issue - question cannot be used
    WARNING = "warning"  # Non-critical issue - question can be used but should be fixed
    INFO = "info"        # Informational message


class ValidationUseCase(str, Enum):
    """Enumeration of all validation use cases."""
    STRUCTURE = "structure"
    TEST_CASES = "test_cases"
    STARTER_CODE = "starter_code"
    SOLUTION = "solution"
    TIME_LIMITS = "time_limits"
    FUNCTION_SIGNATURE = "function_signature"
    OUTPUT_FORMAT = "output_format"
    CONSTRAINTS = "constraints"
    DIFFICULTY = "difficulty"


class ValidationIssue(BaseModel):
    """A single validation issue found during validation."""
    use_case: ValidationUseCase = Field(..., description="The use case that found this issue")
    severity: ValidationSeverity = Field(..., description="Severity of the issue")
    message: str = Field(..., description="Human-readable description of the issue")
    field: Optional[str] = Field(None, description="The field that has the issue")
    language: Optional[str] = Field(None, description="Language if applicable")
    test_case_index: Optional[int] = Field(None, description="Test case index if applicable")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


class UseCaseValidationResult(BaseModel):
    """Result from a single validation use case."""
    use_case: ValidationUseCase = Field(..., description="The use case that was validated")
    passed: bool = Field(..., description="Whether the validation passed")
    issues: List[ValidationIssue] = Field(default_factory=list, description="List of issues found")
    execution_time_ms: Optional[float] = Field(None, description="Time taken to validate")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class QuestionValidationResult(BaseModel):
    """Complete validation result for a question."""
    question_id: str = Field(..., description="ID of the validated question")
    valid: bool = Field(..., description="Whether the question passed all validations")
    results: Dict[ValidationUseCase, UseCaseValidationResult] = Field(
        default_factory=dict,
        description="Results from each use case"
    )
    total_issues: int = Field(default=0, description="Total number of issues found")
    error_count: int = Field(default=0, description="Number of errors")
    warning_count: int = Field(default=0, description="Number of warnings")
    validated_at: datetime = Field(default_factory=datetime.utcnow, description="When validation occurred")
    validation_version: str = Field(default="1.0.0", description="Version of validation logic")


class QuestionValidationStatus(BaseModel):
    """Validation status for a question (stored with the question)."""
    is_validated: bool = Field(default=False, description="Whether question has been validated")
    last_validated: Optional[datetime] = Field(None, description="Last validation timestamp")
    validation_passed: Optional[bool] = Field(None, description="Whether last validation passed")
    validation_errors: List[str] = Field(default_factory=list, description="Error messages from validation")
    validation_warnings: List[str] = Field(default_factory=list, description="Warning messages from validation")


class TestCaseValidationConfig(BaseModel):
    """Configuration for test case validation."""
    max_input_length: int = Field(default=10000, description="Maximum input length in characters")
    max_output_length: int = Field(default=10000, description="Maximum output length in characters")
    min_test_cases: int = Field(default=2, description="Minimum number of test cases required")
    max_test_cases: int = Field(default=50, description="Maximum number of test cases allowed")
    require_hidden_tests: bool = Field(default=False, description="Whether hidden tests are required")


class TimeLimitConfig(BaseModel):
    """Configuration for time limit validation."""
    default_time_limit_ms: int = Field(default=3000, description="Default time limit in milliseconds")
    max_time_limit_ms: int = Field(default=10000, description="Maximum allowed time limit")
    min_time_limit_ms: int = Field(default=100, description="Minimum allowed time limit")
    language_overrides: Dict[str, int] = Field(
        default_factory=lambda: {
            "python": 3000,
            "javascript": 3000,
            "java": 5000,  # Java has JVM startup overhead
        },
        description="Language-specific time limits"
    )


class FunctionSignatureConfig(BaseModel):
    """Configuration for function signature validation."""
    require_type_hints: bool = Field(default=True, description="Whether type hints are required")
    allowed_return_types: List[str] = Field(
        default_factory=lambda: ["int", "str", "bool", "List", "Dict", "None"],
        description="Allowed return types"
    )


class OutputFormatConfig(BaseModel):
    """Configuration for output format validation."""
    allowed_formats: List[str] = Field(
        default_factory=lambda: ["json", "string", "number", "boolean"],
        description="Allowed output formats"
    )
    normalize_whitespace: bool = Field(default=True, description="Whether to normalize whitespace")
    case_sensitive: bool = Field(default=False, description="Whether comparison is case sensitive")


class QuestionValidationConfig(BaseModel):
    """Complete configuration for question validation."""
    test_cases: TestCaseValidationConfig = Field(default_factory=TestCaseValidationConfig)
    time_limits: TimeLimitConfig = Field(default_factory=TimeLimitConfig)
    function_signature: FunctionSignatureConfig = Field(default_factory=FunctionSignatureConfig)
    output_format: OutputFormatConfig = Field(default_factory=OutputFormatConfig)
    skip_use_cases: List[ValidationUseCase] = Field(
        default_factory=list,
        description="Use cases to skip (for testing or gradual rollout)"
    )
    fail_on_warnings: bool = Field(default=False, description="Whether to fail validation on warnings")
