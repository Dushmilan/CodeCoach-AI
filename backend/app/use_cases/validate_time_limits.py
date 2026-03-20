"""
Time limit validation use case.

Validates that time complexity and time limits are reasonable for the problem.
"""

from typing import List, Optional
import re

from app.models.schemas import Question
from app.models.question_validation_schemas import (
    UseCaseValidationResult,
    ValidationUseCase,
    ValidationSeverity,
    TimeLimitConfig,
)
from app.use_cases.base import BaseValidationUseCase


class TimeLimitValidationUseCase(BaseValidationUseCase):
    """
    Validates time limits and complexity for questions.
    
    Checks:
    - Time complexity is specified
    - Time complexity is reasonable for problem difficulty
    - Expected execution time is within limits
    """
    
    # Complexity thresholds by difficulty
    COMPLEXITY_THRESHOLDS = {
        "easy": {
            "max_complexity": "O(n)",
            "warning_complexity": "O(n log n)",
        },
        "medium": {
            "max_complexity": "O(n log n)",
            "warning_complexity": "O(n^2)",
        },
        "hard": {
            "max_complexity": "O(n^2)",
            "warning_complexity": "O(n^3)",
        }
    }
    
    # Complexity order for comparison
    COMPLEXITY_ORDER = [
        "O(1)",
        "O(log n)",
        "O(n)",
        "O(n log n)",
        "O(n^2)",
        "O(n^3)",
        "O(2^n)",
        "O(n!)",
    ]
    
    def __init__(
        self,
        config: Optional[TimeLimitConfig] = None
    ):
        """
        Initialize time limit validation use case.
        
        Args:
            config: Configuration for time limit validation
        """
        self.config = config or TimeLimitConfig()
    
    @property
    def use_case(self) -> ValidationUseCase:
        return ValidationUseCase.TIME_LIMITS
    
    async def _execute_validation(
        self, 
        question: Question
    ) -> UseCaseValidationResult:
        """Execute time limit validation."""
        issues: List = []
        
        # Check if time complexity is specified
        if not question.time_complexity:
            issues.append(self._create_issue(
                message="Time complexity should be specified",
                field="time_complexity",
                severity=ValidationSeverity.WARNING
            ))
        else:
            # Validate time complexity format and reasonableness
            issues.extend(self._validate_time_complexity(question))
        
        # Check constraints for input size implications
        issues.extend(self._validate_constraints_for_time(question))
        
        passed = not any(
            issue.severity == ValidationSeverity.ERROR 
            for issue in issues
        )
        
        return self._create_result(passed=passed, issues=issues)
    
    def _validate_time_complexity(self, question: Question) -> List:
        """Validate time complexity specification."""
        issues = []
        
        complexity = question.time_complexity.strip()
        
        # Check format
        if not re.match(r'^O\([^)]+\)$', complexity):
            issues.append(self._create_issue(
                message=f"Time complexity '{complexity}' is not in standard Big O notation",
                field="time_complexity",
                severity=ValidationSeverity.WARNING,
                details={"complexity": complexity}
            ))
        
        # Get complexity level
        complexity_level = self._get_complexity_level(complexity)
        
        # Check against difficulty expectations
        difficulty = question.difficulty.value
        thresholds = self.COMPLEXITY_THRESHOLDS.get(difficulty, {})
        
        if thresholds:
            max_complexity = thresholds.get("max_complexity")
            warning_complexity = thresholds.get("warning_complexity")
            
            max_level = self._get_complexity_level(max_complexity)
            warning_level = self._get_complexity_level(warning_complexity)
            
            if complexity_level > max_level:
                issues.append(self._create_issue(
                    message=f"Time complexity {complexity} may be too high for {difficulty} problem",
                    field="time_complexity",
                    severity=ValidationSeverity.WARNING,
                    details={
                        "complexity": complexity,
                        "difficulty": difficulty,
                        "recommended_max": max_complexity
                    }
                ))
            elif complexity_level > warning_level:
                issues.append(self._create_issue(
                    message=f"Time complexity {complexity} is acceptable but challenging for {difficulty} problem",
                    field="time_complexity",
                    severity=ValidationSeverity.INFO,
                    details={
                        "complexity": complexity,
                        "difficulty": difficulty,
                        "recommended": warning_complexity
                    }
                ))
        
        return issues
    
    def _validate_constraints_for_time(self, question: Question) -> List:
        """Validate that constraints allow for the specified time complexity."""
        issues = []
        
        if not question.constraints:
            return issues
        
        # Look for input size constraints
        max_input_size = None
        
        for constraint in question.constraints:
            # Try to extract maximum input size from constraints
            # Common patterns: "n <= 10^5", "1 <= n <= 100000"
            match = re.search(r'(\d+)\s*(?:<=|<)\s*(?:n|nums\.length|s\.length)', constraint)
            if match:
                max_input_size = int(match.group(1))
                break
            
            match = re.search(r'(?:n|nums\.length|s\.length)\s*(?:<=|<)\s*(\d+)', constraint)
            if match:
                max_input_size = int(match.group(1))
                break
            
            # Handle scientific notation
            match = re.search(r'10\^(\d+)', constraint)
            if match:
                max_input_size = 10 ** int(match.group(1))
                break
        
        if max_input_size and question.time_complexity:
            complexity = question.time_complexity.strip()
            complexity_level = self._get_complexity_level(complexity)
            
            # Estimate operations based on complexity and input size
            estimated_ops = self._estimate_operations(complexity, max_input_size)
            
            # Warn if estimated operations are too high
            # Assuming ~10^8 operations per second is reasonable
            if estimated_ops > 10**9:
                issues.append(self._create_issue(
                    message=f"Estimated {estimated_ops:.2e} operations may exceed time limit",
                    field="time_complexity",
                    severity=ValidationSeverity.WARNING,
                    details={
                        "complexity": complexity,
                        "max_input_size": max_input_size,
                        "estimated_operations": estimated_ops
                    }
                ))
        
        return issues
    
    def _get_complexity_level(self, complexity: str) -> int:
        """
        Get the complexity level for comparison.
        
        Higher level = worse complexity.
        """
        if not complexity:
            return 0
        
        complexity = complexity.strip()
        
        # Try exact match first
        for i, c in enumerate(self.COMPLEXITY_ORDER):
            if complexity == c:
                return i
        
        # Handle variations
        complexity_lower = complexity.lower()
        
        if "1" in complexity_lower or "constant" in complexity_lower:
            return 0
        elif "log" in complexity_lower:
            return 1
        elif "n!" in complexity_lower:
            return len(self.COMPLEXITY_ORDER) - 1
        elif "2^n" in complexity_lower or "2**n" in complexity_lower:
            return len(self.COMPLEXITY_ORDER) - 2
        elif "n^3" in complexity_lower or "n³" in complexity_lower:
            return 5
        elif "n^2" in complexity_lower or "n²" in complexity_lower:
            return 4
        elif "n log" in complexity_lower:
            return 3
        elif "n" in complexity_lower:
            return 2
        
        return 2  # Default to O(n)
    
    def _estimate_operations(self, complexity: str, n: int) -> float:
        """
        Estimate number of operations for given complexity and input size.
        """
        complexity_lower = complexity.lower()
        
        if "1" in complexity_lower:
            return 1
        elif "log" in complexity_lower and "n log" not in complexity_lower:
            import math
            return math.log2(n) if n > 0 else 1
        elif complexity_lower == "o(n)":
            return n
        elif "n log" in complexity_lower:
            import math
            return n * math.log2(n) if n > 0 else 1
        elif "n^2" in complexity_lower or "n²" in complexity_lower:
            return n * n
        elif "n^3" in complexity_lower or "n³" in complexity_lower:
            return n * n * n
        elif "2^n" in complexity_lower or "2**n" in complexity_lower:
            return 2 ** min(n, 30)  # Cap to avoid overflow
        elif "n!" in complexity_lower:
            import math
            return math.factorial(min(n, 20))  # Cap to avoid overflow
        
        return n  # Default to O(n)
