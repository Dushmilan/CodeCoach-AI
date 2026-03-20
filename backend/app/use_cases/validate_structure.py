"""
Structure validation use case.

Validates that a question has all required fields with valid types and values.
This is the first validation that should run as it checks basic data integrity.
"""

from typing import List
import re

from app.models.schemas import Question, StarterCode
from app.models.question_validation_schemas import (
    UseCaseValidationResult,
    ValidationUseCase,
    ValidationSeverity,
)
from app.use_cases.base import BaseValidationUseCase


class StructureValidationUseCase(BaseValidationUseCase):
    """
    Validates the structure and required fields of a question.
    
    Checks:
    - ID: Non-empty, unique format
    - Title: Minimum and maximum length
    - Description: Minimum length for clarity
    - Difficulty: Valid enum value
    - Category: Non-empty string
    - Starter code: All three languages present
    - Test cases: Minimum count
    - Examples: At least one example
    """
    
    # Validation constants
    MIN_TITLE_LENGTH = 5
    MAX_TITLE_LENGTH = 200
    MIN_DESCRIPTION_LENGTH = 50
    MIN_TEST_CASES = 1
    MIN_EXAMPLES = 1
    REQUIRED_LANGUAGES = ["python", "javascript", "java"]
    
    @property
    def use_case(self) -> ValidationUseCase:
        return ValidationUseCase.STRUCTURE
    
    async def _execute_validation(
        self, 
        question: Question
    ) -> UseCaseValidationResult:
        """Execute structure validation."""
        issues: List = []
        
        # Validate ID
        issues.extend(self._validate_id(question.id))
        
        # Validate title
        issues.extend(self._validate_title(question.title))
        
        # Validate description
        issues.extend(self._validate_description(question.description))
        
        # Validate category
        issues.extend(self._validate_category(question.category))
        
        # Validate starter code
        issues.extend(self._validate_starter_code(question.starter))
        
        # Validate test cases
        issues.extend(self._validate_test_cases(question.test_cases))
        
        # Validate examples
        issues.extend(self._validate_examples(question.examples))
        
        # Validate difficulty
        issues.extend(self._validate_difficulty(question.difficulty))
        
        passed = not any(
            issue.severity == ValidationSeverity.ERROR 
            for issue in issues
        )
        
        return self._create_result(passed=passed, issues=issues)
    
    def _validate_id(self, id: str) -> List:
        """Validate question ID."""
        issues = []
        
        if not id or not id.strip():
            issues.append(self._create_issue(
                message="Question ID cannot be empty",
                field="id",
                severity=ValidationSeverity.ERROR
            ))
        elif not re.match(r'^[a-z0-9-]+$', id.lower()):
            issues.append(self._create_issue(
                message="Question ID must contain only lowercase letters, numbers, and hyphens",
                field="id",
                severity=ValidationSeverity.ERROR
            ))
        
        return issues
    
    def _validate_title(self, title: str) -> List:
        """Validate question title."""
        issues = []
        
        if not title or not title.strip():
            issues.append(self._create_issue(
                message="Question title cannot be empty",
                field="title",
                severity=ValidationSeverity.ERROR
            ))
        elif len(title) < self.MIN_TITLE_LENGTH:
            issues.append(self._create_issue(
                message=f"Question title must be at least {self.MIN_TITLE_LENGTH} characters",
                field="title",
                severity=ValidationSeverity.ERROR,
                details={"actual_length": len(title)}
            ))
        elif len(title) > self.MAX_TITLE_LENGTH:
            issues.append(self._create_issue(
                message=f"Question title must be at most {self.MAX_TITLE_LENGTH} characters",
                field="title",
                severity=ValidationSeverity.WARNING,
                details={"actual_length": len(title)}
            ))
        
        return issues
    
    def _validate_description(self, description: str) -> List:
        """Validate question description."""
        issues = []
        
        if not description or not description.strip():
            issues.append(self._create_issue(
                message="Question description cannot be empty",
                field="description",
                severity=ValidationSeverity.ERROR
            ))
        elif len(description) < self.MIN_DESCRIPTION_LENGTH:
            issues.append(self._create_issue(
                message=f"Question description must be at least {self.MIN_DESCRIPTION_LENGTH} characters for clarity",
                field="description",
                severity=ValidationSeverity.ERROR,
                details={"actual_length": len(description)}
            ))
        
        return issues
    
    def _validate_category(self, category: str) -> List:
        """Validate question category."""
        issues = []
        
        if not category or not category.strip():
            issues.append(self._create_issue(
                message="Question category cannot be empty",
                field="category",
                severity=ValidationSeverity.ERROR
            ))
        
        return issues
    
    def _validate_starter_code(self, starter: StarterCode) -> List:
        """Validate starter code for all languages."""
        issues = []
        
        for language in self.REQUIRED_LANGUAGES:
            code = getattr(starter, language, None)
            
            if not code or not code.strip():
                issues.append(self._create_issue(
                    message=f"Starter code for {language} is missing or empty",
                    field=f"starter.{language}",
                    language=language,
                    severity=ValidationSeverity.ERROR
                ))
            elif len(code.strip()) < 10:
                issues.append(self._create_issue(
                    message=f"Starter code for {language} is too short",
                    field=f"starter.{language}",
                    language=language,
                    severity=ValidationSeverity.WARNING,
                    details={"code_length": len(code)}
                ))
        
        return issues
    
    def _validate_test_cases(self, test_cases: List) -> List:
        """Validate test cases."""
        issues = []
        
        if not test_cases:
            issues.append(self._create_issue(
                message="At least one test case is required",
                field="test_cases",
                severity=ValidationSeverity.ERROR
            ))
        elif len(test_cases) < self.MIN_TEST_CASES:
            issues.append(self._create_issue(
                message=f"At least {self.MIN_TEST_CASES} test case(s) required",
                field="test_cases",
                severity=ValidationSeverity.ERROR,
                details={"actual_count": len(test_cases)}
            ))
        else:
            # Validate each test case structure
            for i, tc in enumerate(test_cases):
                if not tc.input and tc.input != "":
                    issues.append(self._create_issue(
                        message=f"Test case {i+1} is missing input",
                        field=f"test_cases[{i}].input",
                        test_case_index=i,
                        severity=ValidationSeverity.ERROR
                    ))
                if not tc.expected_output and tc.expected_output != "":
                    issues.append(self._create_issue(
                        message=f"Test case {i+1} is missing expected output",
                        field=f"test_cases[{i}].expected_output",
                        test_case_index=i,
                        severity=ValidationSeverity.ERROR
                    ))
        
        return issues
    
    def _validate_examples(self, examples: List) -> List:
        """Validate examples."""
        issues = []
        
        if not examples:
            issues.append(self._create_issue(
                message="At least one example is recommended",
                field="examples",
                severity=ValidationSeverity.WARNING
            ))
        elif len(examples) < self.MIN_EXAMPLES:
            issues.append(self._create_issue(
                message=f"At least {self.MIN_EXAMPLES} example(s) recommended",
                field="examples",
                severity=ValidationSeverity.WARNING,
                details={"actual_count": len(examples)}
            ))
        
        return issues
    
    def _validate_difficulty(self, difficulty) -> List:
        """Validate difficulty level."""
        issues = []
        
        # Difficulty is already validated by Pydantic enum
        # Just check it exists
        if difficulty is None:
            issues.append(self._create_issue(
                message="Difficulty level is required",
                field="difficulty",
                severity=ValidationSeverity.ERROR
            ))
        
        return issues
