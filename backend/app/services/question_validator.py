"""Question validation — single deep module.

Validates question quality across structure, test cases, starter code,
solution, time limits, function signatures, and output formats.
"""

import asyncio
import json
import math
import re
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from app.models.schemas import Question, StarterCode, TestCase as QuestionTestCase
from app.models.question_validation_schemas import (
    QuestionValidationResult,
    QuestionValidationConfig,
    UseCaseValidationResult,
    ValidationUseCase,
    ValidationSeverity,
    ValidationIssue,
    TestCaseValidationConfig,
    TimeLimitConfig,
    FunctionSignatureConfig,
    OutputFormatConfig,
)

logger = logging.getLogger(__name__)


# ── Base Validation ───────────────────────────────────────────────────

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


# ── Structure Validation ──────────────────────────────────────────────

class StructureValidationUseCase(BaseValidationUseCase):
    MIN_TITLE_LENGTH = 5
    MAX_TITLE_LENGTH = 200
    MIN_DESCRIPTION_LENGTH = 50
    MIN_TEST_CASES = 1
    MIN_EXAMPLES = 1
    REQUIRED_LANGUAGES = ["python", "javascript", "java"]

    @property
    def use_case(self) -> ValidationUseCase:
        return ValidationUseCase.STRUCTURE

    async def _execute_validation(self, question: Question) -> UseCaseValidationResult:
        issues: List = []
        issues.extend(self._validate_id(question.id))
        issues.extend(self._validate_title(question.title))
        issues.extend(self._validate_description(question.description))
        issues.extend(self._validate_category(question.category))
        issues.extend(self._validate_starter_code(question.starter))
        issues.extend(self._validate_test_cases(question.test_cases))
        issues.extend(self._validate_examples(question.examples))
        issues.extend(self._validate_difficulty(question.difficulty))
        passed = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        return self._create_result(passed=passed, issues=issues)

    def _validate_id(self, id: str) -> List:
        issues = []
        if not id or not id.strip():
            issues.append(self._create_issue(message="Question ID cannot be empty", field="id"))
        elif not re.match(r"^[a-z0-9-]+$", id.lower()):
            issues.append(self._create_issue(message="Question ID must contain only lowercase letters, numbers, and hyphens", field="id"))
        return issues

    def _validate_title(self, title: str) -> List:
        issues = []
        if not title or not title.strip():
            issues.append(self._create_issue(message="Question title cannot be empty", field="title"))
        elif len(title) < self.MIN_TITLE_LENGTH:
            issues.append(self._create_issue(message=f"Question title must be at least {self.MIN_TITLE_LENGTH} characters", field="title", severity=ValidationSeverity.ERROR, details={"actual_length": len(title)}))
        elif len(title) > self.MAX_TITLE_LENGTH:
            issues.append(self._create_issue(message=f"Question title must be at most {self.MAX_TITLE_LENGTH} characters", field="title", severity=ValidationSeverity.WARNING, details={"actual_length": len(title)}))
        return issues

    def _validate_description(self, description: str) -> List:
        issues = []
        if not description or not description.strip():
            issues.append(self._create_issue(message="Question description cannot be empty", field="description"))
        elif len(description) < self.MIN_DESCRIPTION_LENGTH:
            issues.append(self._create_issue(message=f"Question description must be at least {self.MIN_DESCRIPTION_LENGTH} characters for clarity", field="description", severity=ValidationSeverity.ERROR, details={"actual_length": len(description)}))
        return issues

    def _validate_category(self, category: str) -> List:
        issues = []
        if not category or not category.strip():
            issues.append(self._create_issue(message="Question category cannot be empty", field="category"))
        return issues

    def _validate_starter_code(self, starter: StarterCode) -> List:
        issues = []
        for language in self.REQUIRED_LANGUAGES:
            code = getattr(starter, language, None)
            if not code or not code.strip():
                issues.append(self._create_issue(message=f"Starter code for {language} is missing or empty", field=f"starter.{language}", language=language))
            elif len(code.strip()) < 10:
                issues.append(self._create_issue(message=f"Starter code for {language} is too short", field=f"starter.{language}", language=language, severity=ValidationSeverity.WARNING, details={"code_length": len(code)}))
        return issues

    def _validate_test_cases(self, test_cases: List) -> List:
        issues = []
        if not test_cases:
            issues.append(self._create_issue(message="At least one test case is required", field="test_cases"))
        elif len(test_cases) < self.MIN_TEST_CASES:
            issues.append(self._create_issue(message=f"At least {self.MIN_TEST_CASES} test case(s) required", field="test_cases", details={"actual_count": len(test_cases)}))
        else:
            for i, tc in enumerate(test_cases):
                if not tc.input and tc.input != "":
                    issues.append(self._create_issue(message=f"Test case {i+1} is missing input", field=f"test_cases[{i}].input", test_case_index=i))
                if not tc.expected_output and tc.expected_output != "":
                    issues.append(self._create_issue(message=f"Test case {i+1} is missing expected output", field=f"test_cases[{i}].expected_output", test_case_index=i))
        return issues

    def _validate_examples(self, examples: List) -> List:
        issues = []
        if not examples:
            issues.append(self._create_issue(message="At least one example is recommended", field="examples", severity=ValidationSeverity.WARNING))
        elif len(examples) < self.MIN_EXAMPLES:
            issues.append(self._create_issue(message=f"At least {self.MIN_EXAMPLES} example(s) recommended", field="examples", severity=ValidationSeverity.WARNING, details={"actual_count": len(examples)}))
        return issues

    def _validate_difficulty(self, difficulty) -> List:
        issues = []
        if difficulty is None:
            issues.append(self._create_issue(message="Difficulty level is required", field="difficulty"))
        return issues


# ── Test Case Validation ──────────────────────────────────────────────

class TestCaseValidationUseCase(BaseValidationUseCase):
    def __init__(self, executor: Optional[Any] = None, config: Optional[TestCaseValidationConfig] = None):
        self.executor = executor
        self.config = config or TestCaseValidationConfig()

    @property
    def use_case(self) -> ValidationUseCase:
        return ValidationUseCase.TEST_CASES

    async def _execute_validation(self, question: Question) -> UseCaseValidationResult:
        issues: List = []
        issues.extend(self._validate_test_case_count(question.test_cases))
        for i, test_case in enumerate(question.test_cases):
            issues.extend(self._validate_single_test_case(test_case, i))
        issues.extend(self._check_duplicate_test_cases(question.test_cases))
        issues.extend(self._check_hidden_visible_distribution(question.test_cases))
        if self.executor:
            issues.extend(await self._validate_executability(question))
        passed = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        return self._create_result(passed=passed, issues=issues)

    def _validate_test_case_count(self, test_cases: List[QuestionTestCase]) -> List:
        issues = []
        count = len(test_cases)
        if count < self.config.min_test_cases:
            issues.append(self._create_issue(message=f"At least {self.config.min_test_cases} test case(s) required, found {count}", field="test_cases", details={"count": count, "minimum": self.config.min_test_cases}))
        if count > self.config.max_test_cases:
            issues.append(self._create_issue(message=f"Maximum {self.config.max_test_cases} test cases allowed, found {count}", field="test_cases", severity=ValidationSeverity.WARNING, details={"count": count, "maximum": self.config.max_test_cases}))
        return issues

    def _validate_single_test_case(self, test_case: QuestionTestCase, index: int) -> List:
        issues = []
        if test_case.input is None:
            issues.append(self._create_issue(message=f"Test case {index + 1} is missing input", field=f"test_cases[{index}].input", test_case_index=index))
        elif len(test_case.input) > self.config.max_input_length:
            issues.append(self._create_issue(message=f"Test case {index + 1} input exceeds maximum length", field=f"test_cases[{index}].input", test_case_index=index, severity=ValidationSeverity.WARNING, details={"length": len(test_case.input), "maximum": self.config.max_input_length}))
        if test_case.expected_output is None:
            issues.append(self._create_issue(message=f"Test case {index + 1} is missing expected output", field=f"test_cases[{index}].expected_output", test_case_index=index))
        elif len(test_case.expected_output) > self.config.max_output_length:
            issues.append(self._create_issue(message=f"Test case {index + 1} expected output exceeds maximum length", field=f"test_cases[{index}].expected_output", test_case_index=index, severity=ValidationSeverity.WARNING, details={"length": len(test_case.expected_output), "maximum": self.config.max_output_length}))
        if not test_case.description:
            issues.append(self._create_issue(message=f"Test case {index + 1} is missing description", field=f"test_cases[{index}].description", test_case_index=index, severity=ValidationSeverity.INFO))
        issues.extend(self._check_output_determinism(test_case, index))
        return issues

    def _check_output_determinism(self, test_case: QuestionTestCase, index: int) -> List:
        issues = []
        patterns = [
            (r"\b0x[0-9a-f]+\b", "hexadecimal memory address"),
            (r"\b\d{13,}\b", "timestamp-like number"),
            (r"<.*object at 0x[0-9a-f]+>", "object reference"),
            (r"random", "random value reference"),
        ]
        for pattern, description in patterns:
            if re.search(pattern, test_case.expected_output, re.IGNORECASE):
                issues.append(self._create_issue(message=f"Test case {index + 1} expected output may contain non-deterministic value: {description}", field=f"test_cases[{index}].expected_output", test_case_index=index, severity=ValidationSeverity.WARNING, details={"pattern": pattern}))
        return issues

    def _check_duplicate_test_cases(self, test_cases: List[QuestionTestCase]) -> List:
        issues = []
        seen_inputs = {}
        for i, test_case in enumerate(test_cases):
            input_key = test_case.input.strip() if test_case.input else ""
            if input_key in seen_inputs:
                prev_index = seen_inputs[input_key]
                issues.append(self._create_issue(message=f"Test case {i + 1} has same input as test case {prev_index + 1}", field=f"test_cases[{i}].input", test_case_index=i, severity=ValidationSeverity.WARNING, details={"duplicate_of": prev_index}))
            else:
                seen_inputs[input_key] = i
        return issues

    def _check_hidden_visible_distribution(self, test_cases: List[QuestionTestCase]) -> List:
        issues = []
        if not test_cases:
            return issues
        hidden_count = sum(1 for tc in test_cases if tc.hidden)
        visible_count = len(test_cases) - hidden_count
        if visible_count == 0:
            issues.append(self._create_issue(message="At least one visible (non-hidden) test case is recommended", field="test_cases", severity=ValidationSeverity.WARNING, details={"hidden_count": hidden_count, "visible_count": visible_count}))
        if self.config.require_hidden_tests and hidden_count == 0:
            issues.append(self._create_issue(message="At least one hidden test case is required by configuration", field="test_cases", details={"hidden_count": hidden_count}))
        return issues

    async def _validate_executability(self, question: Question) -> List:
        issues = []
        if not self.executor:
            return issues
        for i, test_case in enumerate(question.test_cases):
            try:
                test_code = f"""
import sys
import json
input_data = json.loads({json.dumps(test_case.input)})
print("Input parsed successfully")
"""
                result = await self.executor.execute(language="python", code=test_code, stdin="")
                if result.exit_code != 0:
                    issues.append(self._create_issue(message=f"Test case {i + 1} input format may cause execution issues", field=f"test_cases[{i}].input", test_case_index=i, severity=ValidationSeverity.WARNING, details={"error": result.stderr}))
            except Exception as e:
                issues.append(self._create_issue(message=f"Failed to validate test case {i + 1} executability: {str(e)}", field=f"test_cases[{i}]", test_case_index=i, severity=ValidationSeverity.INFO))
        return issues


# ── Starter Code Validation ───────────────────────────────────────────

class StarterCodeValidationUseCase(BaseValidationUseCase):
    LANGUAGES = ["python", "javascript", "java"]

    def __init__(self, executor: Optional[Any] = None):
        self.executor = executor

    @property
    def use_case(self) -> ValidationUseCase:
        return ValidationUseCase.STARTER_CODE

    async def _execute_validation(self, question: Question) -> UseCaseValidationResult:
        issues: List = []
        for language in self.LANGUAGES:
            code = getattr(question.starter, language, None)
            if not code:
                issues.append(self._create_issue(message=f"Starter code for {language} is missing", field=f"starter.{language}", language=language))
                continue
            if self.executor:
                issues.extend(await self._validate_syntax(language, code))
            else:
                issues.extend(self._basic_validate(language, code))
        passed = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        return self._create_result(passed=passed, issues=issues)

    def _escape_code(self, code: str) -> str:
        return code.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')

    def _parse_error_message(self, language: str, stderr: str) -> str:
        if not stderr:
            return "Unknown error"
        lines = stderr.strip().split("\n")
        for line in lines:
            if "error" in line.lower() or "Error" in line:
                return line.strip()
        for line in lines:
            if line.strip():
                return line.strip()
        return stderr[:200] if len(stderr) > 200 else stderr

    def _create_syntax_test_code(self, language: str, code: str) -> str:
        if language == "python":
            return f'''
try:
    compile("""{self._escape_code(code)}""", '<string>', 'exec')
    print("Syntax OK")
except SyntaxError as e:
    print(f"SyntaxError: {{e}}")
    raise
'''
        elif language == "javascript":
            return code + '\nconsole.log("Syntax OK");'
        elif language == "java":
            return code
        return code

    async def _validate_syntax(self, language: str, code: str) -> List:
        issues = []
        try:
            test_code = self._create_syntax_test_code(language, code)
            result = await self.executor.execute(language=language, code=test_code, stdin="")
            if result.exit_code != 0:
                issues.append(self._create_issue(message=f"Syntax error in {language} starter code: {self._parse_error_message(language, result.stderr)}", field=f"starter.{language}", language=language, details={"stderr": result.stderr}))
        except Exception as e:
            issues.append(self._create_issue(message=f"Failed to validate {language} starter code: {str(e)}", field=f"starter.{language}", language=language, severity=ValidationSeverity.WARNING))
        return issues

    def _basic_validate(self, language: str, code: str) -> List:
        if language == "python":
            return self._basic_python_validate(code)
        elif language == "javascript":
            return self._basic_javascript_validate(code)
        elif language == "java":
            return self._basic_java_validate(code)
        return []

    def _basic_python_validate(self, code: str) -> List:
        issues = []
        open_chars = {"(": 0, "[": 0, "{": 0}
        close_chars = {")": "(", "]": "[", "}": "{"}
        for char in code:
            if char in open_chars:
                open_chars[char] += 1
            elif char in close_chars:
                open_chars[close_chars[char]] -= 1
        for char, count in open_chars.items():
            if count != 0:
                issues.append(self._create_issue(message=f"Unbalanced {char} in Python starter code", field="starter.python", language="python", severity=ValidationSeverity.WARNING))
        if "def " in code and ":" not in code:
            issues.append(self._create_issue(message="Python function definition missing colon", field="starter.python", language="python"))
        return issues

    def _basic_javascript_validate(self, code: str) -> List:
        issues = []
        open_chars = {"(": 0, "[": 0, "{": 0}
        close_chars = {")": "(", "]": "[", "}": "{"}
        for char in code:
            if char in open_chars:
                open_chars[char] += 1
            elif char in close_chars:
                open_chars[close_chars[char]] -= 1
        for char, count in open_chars.items():
            if count != 0:
                issues.append(self._create_issue(message=f"Unbalanced {char} in JavaScript starter code", field="starter.javascript", language="javascript", severity=ValidationSeverity.WARNING))
        return issues

    def _basic_java_validate(self, code: str) -> List:
        issues = []
        if "class " not in code:
            issues.append(self._create_issue(message="Java starter code should contain a class definition", field="starter.java", language="java", severity=ValidationSeverity.WARNING))
        brace_count = code.count("{") - code.count("}")
        if brace_count != 0:
            issues.append(self._create_issue(message="Unbalanced braces in Java starter code", field="starter.java", language="java", severity=ValidationSeverity.WARNING))
        return issues


# ── Solution Validation ───────────────────────────────────────────────

class SolutionValidationUseCase(BaseValidationUseCase):
    def __init__(self, executor: Optional[Any] = None):
        self.executor = executor

    @property
    def use_case(self) -> ValidationUseCase:
        return ValidationUseCase.SOLUTION

    async def _execute_validation(self, question: Question) -> UseCaseValidationResult:
        issues: List = []
        if not question.solution:
            issues.append(self._create_issue(message="Reference solution is required for validation", field="solution"))
            return self._create_result(passed=False, issues=issues)
        if self.executor:
            issues.extend(await self._validate_solution_with_piston(question))
        else:
            issues.append(self._create_issue(message="Cannot validate solution execution without Piston service", field="solution", severity=ValidationSeverity.WARNING))
        passed = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        return self._create_result(passed=passed, issues=issues)

    def _compare_outputs(self, actual: str, expected: str) -> bool:
        if actual == expected:
            return True
        if actual.strip() == expected.strip():
            return True
        try:
            return json.loads(actual) == json.loads(expected)
        except (json.JSONDecodeError, ValueError):
            pass
        try:
            return float(actual) == float(expected)
        except (ValueError, TypeError):
            pass
        if actual.lower() in ("true", "false") and expected.lower() in ("true", "false"):
            return actual.lower() == expected.lower()
        return False

    def _create_runner(self, solution_code: str, func_name: str, question: Question) -> str:
        return f"""
import sys
import json
from typing import List

{solution_code}

lines = sys.stdin.read().strip().split('\\n')
try:
    if len(lines) == 1:
        try:
            input_data = json.loads(lines[0])
        except:
            input_data = lines[0]
        result = {func_name}(input_data)
    elif len(lines) == 2:
        try:
            first = json.loads(lines[0])
            second = json.loads(lines[1]) if lines[1].isdigit() or lines[1].startswith('[') else int(lines[1])
            result = {func_name}(first, second)
        except:
            result = {func_name}(lines[0], lines[1])
    else:
        result = {func_name}(lines)
    if isinstance(result, list):
        print(json.dumps(result))
    elif isinstance(result, bool):
        print(str(result).lower())
    else:
        print(result)
except Exception as e:
    print(f"Error: {{e}}", file=sys.stderr)
    sys.exit(1)
"""

    def _create_executable_solution(self, question: Question) -> Optional[str]:
        starter_code = question.starter.python
        func_match = re.search(r"def\s+(\w+)\s*\(", starter_code)
        if not func_match:
            return None
        func_name = func_match.group(1)
        if "pass" not in starter_code or "return" in starter_code:
            return self._create_runner(starter_code, func_name, question)
        return None

    async def _validate_solution_with_piston(self, question: Question) -> List:
        issues = []
        solution_code = self._create_executable_solution(question)
        if not solution_code:
            issues.append(self._create_issue(message="Could not create executable solution from reference solution", field="solution"))
            return issues
        passed_count = 0
        total_count = len(question.test_cases)
        for i, test_case in enumerate(question.test_cases):
            try:
                result = await self.executor.execute(language="python", code=solution_code, stdin=test_case.input)
                if result.exit_code != 0:
                    issues.append(self._create_issue(message=f"Solution failed on test case {i + 1}: {result.stderr[:100]}", field="solution", test_case_index=i, details={"test_case": test_case.description, "error": result.stderr}))
                    continue
                actual_output = result.stdout.strip()
                expected_output = test_case.expected_output.strip()
                if self._compare_outputs(actual_output, expected_output):
                    passed_count += 1
                else:
                    issues.append(self._create_issue(message=f"Solution output mismatch on test case {i + 1}", field="solution", test_case_index=i, details={"test_case": test_case.description, "expected": expected_output, "actual": actual_output}))
            except Exception as e:
                issues.append(self._create_issue(message=f"Failed to execute solution for test case {i + 1}: {str(e)}", field="solution", test_case_index=i))
        if total_count > 0 and passed_count < total_count:
            issues.append(self._create_issue(message=f"Solution only passed {passed_count}/{total_count} test cases", field="solution", details={"passed": passed_count, "total": total_count}))
        return issues


# ── Time Limit Validation ─────────────────────────────────────────────

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


# ── Function Signature Validation ─────────────────────────────────────

class FunctionSignatureValidationUseCase(BaseValidationUseCase):
    VALID_PYTHON_TYPES = {
        "int", "str", "bool", "float", "list", "dict", "set", "tuple",
        "List", "Dict", "Set", "Tuple", "Optional", "Any", "Union",
        "None", "Callable", "Iterable", "Sequence",
    }

    def __init__(self, config: Optional[FunctionSignatureConfig] = None, require_type_hints: bool = True):
        self.config = config or FunctionSignatureConfig()
        self.require_type_hints = require_type_hints

    @property
    def use_case(self) -> ValidationUseCase:
        return ValidationUseCase.FUNCTION_SIGNATURE

    async def _execute_validation(self, question: Question) -> UseCaseValidationResult:
        issues: List = []
        issues.extend(self._validate_python_signature(question.starter.python))
        issues.extend(self._validate_javascript_signature(question.starter.javascript))
        issues.extend(self._validate_java_signature(question.starter.java))
        issues.extend(self._check_signature_consistency(question))
        passed = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        return self._create_result(passed=passed, issues=issues)

    def _parse_python_params(self, params_str: str) -> List:
        params = []
        depth = 0
        current = ""
        for char in params_str:
            if char in "([{":
                depth += 1
                current += char
            elif char in ")]}":
                depth -= 1
                current += char
            elif char == "," and depth == 0:
                if current.strip():
                    params.append(self._parse_single_param(current.strip()))
                current = ""
            else:
                current += char
        if current.strip():
            params.append(self._parse_single_param(current.strip()))
        return params

    def _parse_single_param(self, param: str) -> tuple:
        if "=" in param:
            param = param.split("=")[0].strip()
        if ":" in param:
            parts = param.split(":", 1)
            name = parts[0].strip()
            type_hint = parts[1].strip() if len(parts) > 1 else None
            return (name, type_hint)
        return (param.strip(), None)

    def _is_valid_python_type(self, type_str: str) -> bool:
        type_str = type_str.strip()
        if type_str in self.VALID_PYTHON_TYPES:
            return True
        generic_match = re.match(r"(\w+)\[", type_str)
        if generic_match and generic_match.group(1) in self.VALID_PYTHON_TYPES:
            return True
        if type_str.startswith(("Optional[", "Union[", "Callable[")):
            return True
        if type_str.lower() in {t.lower() for t in self.VALID_PYTHON_TYPES}:
            return True
        return False

    def _validate_python_signature(self, code: str) -> List:
        issues = []
        func_match = re.search(r"def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^\n:]+))?", code)
        if not func_match:
            issues.append(self._create_issue(message="No valid Python function definition found", field="starter.python", language="python"))
            return issues
        func_name, params_str, return_type = func_match.group(1), func_match.group(2), func_match.group(3)
        if not re.match(r"^[a-z_][a-z0-9_]*$", func_name, re.IGNORECASE):
            issues.append(self._create_issue(message=f"Invalid Python function name: {func_name}", field="starter.python", language="python", severity=ValidationSeverity.WARNING))
        if params_str.strip():
            for param_name, param_type in self._parse_python_params(params_str):
                if self.require_type_hints and not param_type:
                    issues.append(self._create_issue(message=f"Parameter '{param_name}' missing type hint", field="starter.python", language="python", severity=ValidationSeverity.WARNING, details={"parameter": param_name}))
                if param_type and not self._is_valid_python_type(param_type):
                    issues.append(self._create_issue(message=f"Potentially invalid type hint for parameter '{param_name}': {param_type}", field="starter.python", language="python", severity=ValidationSeverity.INFO, details={"parameter": param_name, "type": param_type}))
        if self.require_type_hints and not return_type:
            issues.append(self._create_issue(message="Return type hint missing for Python function", field="starter.python", language="python", severity=ValidationSeverity.WARNING))
        if return_type and not self._is_valid_python_type(return_type.strip()):
            issues.append(self._create_issue(message=f"Potentially invalid return type: {return_type.strip()}", field="starter.python", language="python", severity=ValidationSeverity.INFO, details={"return_type": return_type.strip()}))
        return issues

    def _validate_javascript_signature(self, code: str) -> List:
        issues = []
        func_match = re.search(r"function\s+(\w+)\s*\(([^)]*)\)", code)
        if not func_match:
            func_match = re.search(r"(?:const|let|var)\s+(\w+)\s*=\s*(?:\([^)]*\)|[^=])\s*=>", code)
        if not func_match:
            issues.append(self._create_issue(message="No valid JavaScript function definition found", field="starter.javascript", language="javascript"))
            return issues
        func_name = func_match.group(1)
        if not re.match(r"^[a-zA-Z_$][a-zA-Z0-9_$]*$", func_name):
            issues.append(self._create_issue(message=f"Invalid JavaScript function name: {func_name}", field="starter.javascript", language="javascript", severity=ValidationSeverity.WARNING))
        return issues

    def _validate_java_signature(self, code: str) -> List:
        issues = []
        method_match = re.search(r"public\s+(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)", code)
        if not method_match:
            method_match = re.search(r"(?:public|private|protected)\s+(?:static\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)", code)
        if not method_match:
            method_match = re.search(r"(?:static\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)\s*\{", code)
        if not method_match:
            method_match = re.search(r"(\w+(?:\[\])?)\s+(\w+)\s*\(([^)]*)\)\s*\{", code)
        if not method_match:
            issues.append(self._create_issue(message="No valid Java method definition found", field="starter.java", language="java"))
            return issues
        return_type, method_name = method_match.group(1), method_match.group(2)
        if not re.match(r"^[a-z][a-zA-Z0-9_]*$", method_name):
            issues.append(self._create_issue(message=f"Java method name '{method_name}' should follow camelCase convention", field="starter.java", language="java", severity=ValidationSeverity.INFO))
        if return_type == "void":
            issues.append(self._create_issue(message="Java method returns void - ensure this is intentional", field="starter.java", language="java", severity=ValidationSeverity.INFO))
        return issues

    def _extract_python_function_name(self, code: str) -> Optional[str]:
        match = re.search(r"def\s+(\w+)\s*\(", code)
        return match.group(1) if match else None

    def _extract_js_function_name(self, code: str) -> Optional[str]:
        match = re.search(r"function\s+(\w+)\s*\(", code)
        if match:
            return match.group(1)
        match = re.search(r"(?:const|let|var)\s+(\w+)\s*=", code)
        return match.group(1) if match else None

    def _extract_java_method_name(self, code: str) -> Optional[str]:
        match = re.search(r"public\s+\w+\s+(\w+)\s*\(", code)
        return match.group(1) if match else None

    def _check_signature_consistency(self, question: Question) -> List:
        issues = []
        python_name = self._extract_python_function_name(question.starter.python)
        js_name = self._extract_js_function_name(question.starter.javascript)
        java_name = self._extract_java_method_name(question.starter.java)
        if python_name and js_name:
            if python_name.replace("_", "").lower() != js_name.lower():
                issues.append(self._create_issue(message=f"Function names differ between Python ({python_name}) and JavaScript ({js_name})", severity=ValidationSeverity.INFO, details={"python": python_name, "javascript": js_name}))
        if python_name and java_name:
            if python_name.replace("_", "").lower() != java_name.lower():
                issues.append(self._create_issue(message=f"Function names differ between Python ({python_name}) and Java ({java_name})", severity=ValidationSeverity.INFO, details={"python": python_name, "java": java_name}))
        return issues


# ── Output Format Validation ──────────────────────────────────────────

class OutputFormatValidationUseCase(BaseValidationUseCase):
    FORMAT_JSON_ARRAY = "json_array"
    FORMAT_JSON_OBJECT = "json_object"
    FORMAT_NUMBER = "number"
    FORMAT_STRING = "string"
    FORMAT_BOOLEAN = "boolean"
    FORMAT_MIXED = "mixed"

    def __init__(self, config: Optional[OutputFormatConfig] = None):
        self.config = config or OutputFormatConfig()

    @property
    def use_case(self) -> ValidationUseCase:
        return ValidationUseCase.OUTPUT_FORMAT

    async def _execute_validation(self, question: Question) -> UseCaseValidationResult:
        issues: List = []
        if not question.test_cases:
            issues.append(self._create_issue(message="No test cases to validate output format", field="test_cases"))
            return self._create_result(passed=False, issues=issues)
        formats = []
        for i, test_case in enumerate(question.test_cases):
            formats.append((i, self._detect_output_format(test_case.expected_output), test_case.expected_output))
        issues.extend(self._check_format_consistency(formats))
        for i, test_case in enumerate(question.test_cases):
            issues.extend(self._validate_single_output(test_case.expected_output, i))
        issues.extend(self._check_examples_consistency(question))
        passed = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        return self._create_result(passed=passed, issues=issues)

    def _detect_output_format(self, output: str) -> str:
        output = output.strip()
        if output.startswith("[") and output.endswith("]"):
            try:
                if isinstance(json.loads(output), list):
                    return self.FORMAT_JSON_ARRAY
            except json.JSONDecodeError:
                pass
        if output.startswith("{") and output.endswith("}"):
            try:
                if isinstance(json.loads(output), dict):
                    return self.FORMAT_JSON_OBJECT
            except json.JSONDecodeError:
                pass
        try:
            float(output)
            return self.FORMAT_NUMBER
        except ValueError:
            pass
        if output.lower() in ("true", "false"):
            return self.FORMAT_BOOLEAN
        return self.FORMAT_STRING

    def _are_formats_compatible(self, format1: str, format2: str) -> bool:
        if format1 == format2:
            return True
        ns = {self.FORMAT_NUMBER, self.FORMAT_STRING}
        if format1 in ns and format2 in ns:
            return True
        bs = {self.FORMAT_BOOLEAN, self.FORMAT_STRING}
        if format1 in bs and format2 in bs:
            return True
        return False

    def _check_format_consistency(self, formats: List) -> List:
        issues = []
        unique_formats = set(f[1] for f in formats)
        if len(unique_formats) > 1:
            incompatible = {self.FORMAT_JSON_ARRAY, self.FORMAT_JSON_OBJECT}
            if unique_formats & incompatible and len(unique_formats & incompatible) > 1:
                issues.append(self._create_issue(message="Inconsistent output formats: mixing JSON arrays and objects", field="test_cases", details={"formats_found": list(unique_formats), "test_cases": [{"index": f[0], "format": f[1], "output": f[2][:50]} for f in formats]}))
            elif unique_formats & incompatible and (unique_formats - incompatible):
                issues.append(self._create_issue(message="Inconsistent output formats: mixing JSON with primitive types", field="test_cases", details={"formats_found": list(unique_formats)}))
            else:
                issues.append(self._create_issue(message=f"Minor output format inconsistency detected: {', '.join(unique_formats)}", field="test_cases", severity=ValidationSeverity.WARNING, details={"formats_found": list(unique_formats)}))
        return issues

    def _validate_single_output(self, output: str, index: int) -> List:
        issues = []
        output = output.strip()
        if not output:
            issues.append(self._create_issue(message=f"Test case {index + 1} has empty expected output", field=f"test_cases[{index}].expected_output", test_case_index=index, severity=ValidationSeverity.WARNING))
            return issues
        if output.startswith("[") or output.startswith("{"):
            try:
                parsed = json.loads(output)
                if isinstance(parsed, list) and len(parsed) == 0:
                    issues.append(self._create_issue(message=f"Test case {index + 1} returns empty array - ensure this is intentional", field=f"test_cases[{index}].expected_output", test_case_index=index, severity=ValidationSeverity.INFO))
                if isinstance(parsed, list) and len(parsed) > 1:
                    element_types = set(type(e).__name__ for e in parsed)
                    if len(element_types) > 1:
                        issues.append(self._create_issue(message=f"Test case {index + 1} array has mixed element types", field=f"test_cases[{index}].expected_output", test_case_index=index, severity=ValidationSeverity.WARNING, details={"types": list(element_types)}))
            except json.JSONDecodeError as e:
                issues.append(self._create_issue(message=f"Test case {index + 1} has invalid JSON output: {str(e)}", field=f"test_cases[{index}].expected_output", test_case_index=index, details={"error": str(e)}))
        if output.lower() in ("true", "false") and output != output.lower():
            issues.append(self._create_issue(message=f"Test case {index + 1} boolean output should be lowercase", field=f"test_cases[{index}].expected_output", test_case_index=index, severity=ValidationSeverity.INFO, details={"output": output}))
        if output != output.strip():
            issues.append(self._create_issue(message=f"Test case {index + 1} output has leading/trailing whitespace", field=f"test_cases[{index}].expected_output", test_case_index=index, severity=ValidationSeverity.INFO))
        return issues

    def _check_examples_consistency(self, question: Question) -> List:
        issues = []
        if not question.examples or not question.test_cases:
            return issues
        test_case_format = self._detect_output_format(question.test_cases[0].expected_output)
        for i, example in enumerate(question.examples):
            example_format = self._detect_output_format(example.output)
            if example_format != test_case_format:
                if self._are_formats_compatible(example_format, test_case_format):
                    issues.append(self._create_issue(message=f"Example {i + 1} output format differs from test cases", field=f"examples[{i}].output", severity=ValidationSeverity.INFO, details={"example_format": example_format, "test_case_format": test_case_format}))
                else:
                    issues.append(self._create_issue(message=f"Example {i + 1} output format is incompatible with test cases", field=f"examples[{i}].output", severity=ValidationSeverity.WARNING, details={"example_format": example_format, "test_case_format": test_case_format}))
        return issues


# ── Orchestrator ──────────────────────────────────────────────────────

class QuestionValidatorService:
    """Service orchestrating all validation strategies through a single interface."""

    def __init__(self, executor: Optional[Any] = None, config: Optional[QuestionValidationConfig] = None):
        self.executor = executor
        self.config = config or QuestionValidationConfig()
        self._init_use_cases()

    def _init_use_cases(self):
        self.use_cases: Dict[ValidationUseCase, Any] = {
            ValidationUseCase.STRUCTURE: StructureValidationUseCase(),
            ValidationUseCase.TEST_CASES: TestCaseValidationUseCase(executor=self.executor, config=self.config.test_cases),
            ValidationUseCase.STARTER_CODE: StarterCodeValidationUseCase(executor=self.executor),
            ValidationUseCase.SOLUTION: SolutionValidationUseCase(executor=self.executor),
            ValidationUseCase.TIME_LIMITS: TimeLimitValidationUseCase(config=self.config.time_limits),
            ValidationUseCase.FUNCTION_SIGNATURE: FunctionSignatureValidationUseCase(config=self.config.function_signature),
            ValidationUseCase.OUTPUT_FORMAT: OutputFormatValidationUseCase(config=self.config.output_format),
        }

    async def validate_question(self, question: Question, use_cases: Optional[List[ValidationUseCase]] = None) -> QuestionValidationResult:
        use_cases_to_run = use_cases or list(self.use_cases.keys())
        use_cases_to_run = [uc for uc in use_cases_to_run if uc not in self.config.skip_use_cases]
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
                results[use_case_enum] = UseCaseValidationResult(use_case=use_case_enum, passed=False, issues=[])
        total_issues = sum(len(r.issues) for r in results.values())
        error_count = sum(1 for r in results.values() for issue in r.issues if issue.severity == ValidationSeverity.ERROR)
        warning_count = sum(1 for r in results.values() for issue in r.issues if issue.severity == ValidationSeverity.WARNING)
        valid = error_count == 0
        if self.config.fail_on_warnings and warning_count > 0:
            valid = False
        return QuestionValidationResult(
            question_id=question.id, valid=valid, results=results,
            total_issues=total_issues, error_count=error_count,
            warning_count=warning_count, validated_at=datetime.utcnow(),
        )

    async def validate_batch(self, questions: List[Question]) -> List[QuestionValidationResult]:
        results = await asyncio.gather(*[self.validate_question(question) for question in questions])
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
        return await self.validate_question(question, use_cases=[
            ValidationUseCase.STRUCTURE,
            ValidationUseCase.OUTPUT_FORMAT,
            ValidationUseCase.TIME_LIMITS,
            ValidationUseCase.FUNCTION_SIGNATURE,
        ])

    async def full_validate(self, question: Question) -> QuestionValidationResult:
        return await self.validate_question(question)

    def get_validation_summary(self, result: QuestionValidationResult) -> Dict[str, Any]:
        summary = {
            "question_id": result.question_id, "valid": result.valid,
            "total_issues": result.total_issues, "error_count": result.error_count,
            "warning_count": result.warning_count,
            "use_cases_run": len(result.results),
            "use_cases_passed": sum(1 for r in result.results.values() if r.passed),
            "issues_by_use_case": {},
        }
        for use_case, uc_result in result.results.items():
            issues = [{"severity": issue.severity.value, "message": issue.message, "field": issue.field} for issue in uc_result.issues]
            summary["issues_by_use_case"][use_case.value] = {"passed": uc_result.passed, "issue_count": len(issues), "issues": issues}
        return summary
