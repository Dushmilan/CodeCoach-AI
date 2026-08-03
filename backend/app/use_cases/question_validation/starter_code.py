"""Starter code validation use case."""

from typing import List, Optional

from app.ports.code_executor import CodeExecutor
from app.models.schemas import Question
from app.models.question_validation_schemas import (
    UseCaseValidationResult,
    ValidationUseCase,
    ValidationSeverity,
)

from .base import BaseValidationUseCase


class StarterCodeValidationUseCase(BaseValidationUseCase):
    LANGUAGES = ["python", "javascript", "java"]

    def __init__(self, executor: Optional[CodeExecutor] = None):
        self.executor = executor

    @property
    def use_case(self) -> ValidationUseCase:
        return ValidationUseCase.STARTER_CODE

    async def _execute_validation(self, question: Question) -> UseCaseValidationResult:
        issues: List = []
        for language in self.LANGUAGES:
            code = getattr(question.starter, language, None)
            if not code:
                issues.append(
                    self._create_issue(
                        message=f"Starter code for {language} is missing",
                        field=f"starter.{language}",
                        language=language,
                    )
                )
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
        issues: List = []
        if not self.executor:
            return issues
        try:
            test_code = self._create_syntax_test_code(language, code)
            result = await self.executor.execute(
                language=language, code=test_code, stdin=""
            )
            if result.exit_code != 0:
                issues.append(
                    self._create_issue(
                        message=f"Syntax error in {language} starter code: {self._parse_error_message(language, result.stderr)}",
                        field=f"starter.{language}",
                        language=language,
                        details={"stderr": result.stderr},
                    )
                )
        except Exception as e:
            issues.append(
                self._create_issue(
                    message=f"Failed to validate {language} starter code: {str(e)}",
                    field=f"starter.{language}",
                    language=language,
                    severity=ValidationSeverity.WARNING,
                )
            )
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
                issues.append(
                    self._create_issue(
                        message=f"Unbalanced {char} in Python starter code",
                        field="starter.python",
                        language="python",
                        severity=ValidationSeverity.WARNING,
                    )
                )
        if "def " in code and ":" not in code:
            issues.append(
                self._create_issue(
                    message="Python function definition missing colon",
                    field="starter.python",
                    language="python",
                )
            )
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
                issues.append(
                    self._create_issue(
                        message=f"Unbalanced {char} in JavaScript starter code",
                        field="starter.javascript",
                        language="javascript",
                        severity=ValidationSeverity.WARNING,
                    )
                )
        return issues

    def _basic_java_validate(self, code: str) -> List:
        issues = []
        if "class " not in code:
            issues.append(
                self._create_issue(
                    message="Java starter code should contain a class definition",
                    field="starter.java",
                    language="java",
                    severity=ValidationSeverity.WARNING,
                )
            )
        brace_count = code.count("{") - code.count("}")
        if brace_count != 0:
            issues.append(
                self._create_issue(
                    message="Unbalanced braces in Java starter code",
                    field="starter.java",
                    language="java",
                    severity=ValidationSeverity.WARNING,
                )
            )
        return issues
