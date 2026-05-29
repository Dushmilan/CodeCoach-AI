"""Time limit validation use case."""

import math
import re
from typing import List, Optional

from app.models.schemas import Question
from app.models.question_validation_schemas import (
    UseCaseValidationResult,
    ValidationUseCase,
    ValidationSeverity,
    TimeLimitConfig,
)

from .base import BaseValidationUseCase


class TimeLimitValidationUseCase(BaseValidationUseCase):
    COMPLEXITY_THRESHOLDS = {
        "easy": {"max_complexity": "O(n)", "warning_complexity": "O(n log n)"},
        "medium": {"max_complexity": "O(n log n)", "warning_complexity": "O(n^2)"},
        "hard": {"max_complexity": "O(n^2)", "warning_complexity": "O(n^3)"},
    }
    COMPLEXITY_ORDER = ["O(1)", "O(log n)", "O(n)", "O(n log n)", "O(n^2)", "O(n^3)", "O(2^n)", "O(n!)"]

    def __init__(self, config: Optional[TimeLimitConfig] = None):
        self.config = config or TimeLimitConfig()

    @property
    def use_case(self) -> ValidationUseCase:
        return ValidationUseCase.TIME_LIMITS

    async def _execute_validation(self, question: Question) -> UseCaseValidationResult:
        issues: List = []
        if not question.time_complexity:
            issues.append(self._create_issue(message="Time complexity should be specified", field="time_complexity", severity=ValidationSeverity.WARNING))
        else:
            issues.extend(self._validate_time_complexity(question))
        issues.extend(self._validate_constraints_for_time(question))
        passed = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        return self._create_result(passed=passed, issues=issues)

    def _get_complexity_level(self, complexity: str) -> int:
        if not complexity:
            return 0
        complexity = complexity.strip()
        for i, c in enumerate(self.COMPLEXITY_ORDER):
            if complexity == c:
                return i
        cl = complexity.lower()
        if "1" in cl or "constant" in cl:
            return 0
        elif "log" in cl:
            return 1
        elif "n!" in cl:
            return len(self.COMPLEXITY_ORDER) - 1
        elif "2^n" in cl or "2**n" in cl:
            return len(self.COMPLEXITY_ORDER) - 2
        elif "n^3" in cl or "n³" in cl:
            return 5
        elif "n^2" in cl or "n²" in cl:
            return 4
        elif "n log" in cl:
            return 3
        elif "n" in cl:
            return 2
        return 2

    def _estimate_operations(self, complexity: str, n: int) -> float:
        cl = complexity.lower()
        if "1" in cl:
            return 1
        elif "log" in cl and "n log" not in cl:
            return math.log2(n) if n > 0 else 1
        elif cl == "o(n)":
            return n
        elif "n log" in cl:
            return n * math.log2(n) if n > 0 else 1
        elif "n^2" in cl or "n²" in cl:
            return n * n
        elif "n^3" in cl or "n³" in cl:
            return n * n * n
        elif "2^n" in cl or "2**n" in cl:
            return 2 ** min(n, 30)
        elif "n!" in cl:
            return math.factorial(min(n, 20))
        return n

    def _validate_time_complexity(self, question: Question) -> List:
        issues = []
        complexity = question.time_complexity.strip()
        if not re.match(r"^O\([^)]+\)$", complexity):
            issues.append(self._create_issue(message=f"Time complexity '{complexity}' is not in standard Big O notation", field="time_complexity", severity=ValidationSeverity.WARNING, details={"complexity": complexity}))
        complexity_level = self._get_complexity_level(complexity)
        difficulty = question.difficulty.value
        thresholds = self.COMPLEXITY_THRESHOLDS.get(difficulty, {})
        if thresholds:
            max_level = self._get_complexity_level(thresholds.get("max_complexity"))
            warning_level = self._get_complexity_level(thresholds.get("warning_complexity"))
            if complexity_level > max_level:
                issues.append(self._create_issue(message=f"Time complexity {complexity} may be too high for {difficulty} problem", field="time_complexity", severity=ValidationSeverity.WARNING, details={"complexity": complexity, "difficulty": difficulty, "recommended_max": thresholds["max_complexity"]}))
            elif complexity_level > warning_level:
                issues.append(self._create_issue(message=f"Time complexity {complexity} is acceptable but challenging for {difficulty} problem", field="time_complexity", severity=ValidationSeverity.INFO, details={"complexity": complexity, "difficulty": difficulty, "recommended": thresholds["warning_complexity"]}))
        return issues

    def _validate_constraints_for_time(self, question: Question) -> List:
        issues = []
        if not question.constraints:
            return issues
        max_input_size = None
        for constraint in question.constraints:
            match = re.search(r"(\d+)\s*(?:<=|<)\s*(?:n|nums\.length|s\.length)", constraint)
            if match:
                max_input_size = int(match.group(1))
                break
            match = re.search(r"(?:n|nums\.length|s\.length)\s*(?:<=|<)\s*(\d+)", constraint)
            if match:
                max_input_size = int(match.group(1))
                break
            match = re.search(r"10\^(\d+)", constraint)
            if match:
                max_input_size = 10 ** int(match.group(1))
                break
        if max_input_size and question.time_complexity:
            estimated_ops = self._estimate_operations(question.time_complexity.strip(), max_input_size)
            if estimated_ops > 10**9:
                issues.append(self._create_issue(message=f"Estimated {estimated_ops:.2e} operations may exceed time limit", field="time_complexity", severity=ValidationSeverity.WARNING, details={"complexity": question.time_complexity, "max_input_size": max_input_size, "estimated_operations": estimated_ops}))
        return issues
