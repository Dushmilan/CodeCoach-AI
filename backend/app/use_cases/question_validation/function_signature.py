"""Function signature validation use case."""

import re
from typing import List, Optional

from app.models.schemas import Question
from app.models.question_validation_schemas import (
    UseCaseValidationResult,
    ValidationUseCase,
    ValidationSeverity,
    FunctionSignatureConfig,
)

from .base import BaseValidationUseCase


class FunctionSignatureValidationUseCase(BaseValidationUseCase):
    VALID_PYTHON_TYPES = {
        "int",
        "str",
        "bool",
        "float",
        "list",
        "dict",
        "set",
        "tuple",
        "List",
        "Dict",
        "Set",
        "Tuple",
        "Optional",
        "Any",
        "Union",
        "None",
        "Callable",
        "Iterable",
        "Sequence",
    }

    def __init__(
        self,
        config: Optional[FunctionSignatureConfig] = None,
        require_type_hints: bool = True,
    ):
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
            issues.append(
                self._create_issue(
                    message="No valid Python function definition found",
                    field="starter.python",
                    language="python",
                )
            )
            return issues
        func_name, params_str, return_type = (
            func_match.group(1),
            func_match.group(2),
            func_match.group(3),
        )
        if not re.match(r"^[a-z_][a-z0-9_]*$", func_name, re.IGNORECASE):
            issues.append(
                self._create_issue(
                    message=f"Invalid Python function name: {func_name}",
                    field="starter.python",
                    language="python",
                    severity=ValidationSeverity.WARNING,
                )
            )
        if params_str.strip():
            for param_name, param_type in self._parse_python_params(params_str):
                if self.require_type_hints and not param_type:
                    issues.append(
                        self._create_issue(
                            message=f"Parameter '{param_name}' missing type hint",
                            field="starter.python",
                            language="python",
                            severity=ValidationSeverity.WARNING,
                            details={"parameter": param_name},
                        )
                    )
                if param_type and not self._is_valid_python_type(param_type):
                    issues.append(
                        self._create_issue(
                            message=f"Potentially invalid type hint for parameter '{param_name}': {param_type}",
                            field="starter.python",
                            language="python",
                            severity=ValidationSeverity.INFO,
                            details={"parameter": param_name, "type": param_type},
                        )
                    )
        if self.require_type_hints and not return_type:
            issues.append(
                self._create_issue(
                    message="Return type hint missing for Python function",
                    field="starter.python",
                    language="python",
                    severity=ValidationSeverity.WARNING,
                )
            )
        if return_type and not self._is_valid_python_type(return_type.strip()):
            issues.append(
                self._create_issue(
                    message=f"Potentially invalid return type: {return_type.strip()}",
                    field="starter.python",
                    language="python",
                    severity=ValidationSeverity.INFO,
                    details={"return_type": return_type.strip()},
                )
            )
        return issues

    def _validate_javascript_signature(self, code: str) -> List:
        issues = []
        func_match = re.search(r"function\s+(\w+)\s*\(([^)]*)\)", code)
        if not func_match:
            func_match = re.search(
                r"(?:const|let|var)\s+(\w+)\s*=\s*(?:\([^)]*\)|[^=])\s*=>", code
            )
        if not func_match:
            issues.append(
                self._create_issue(
                    message="No valid JavaScript function definition found",
                    field="starter.javascript",
                    language="javascript",
                )
            )
            return issues
        func_name = func_match.group(1)
        if not re.match(r"^[a-zA-Z_$][a-zA-Z0-9_$]*$", func_name):
            issues.append(
                self._create_issue(
                    message=f"Invalid JavaScript function name: {func_name}",
                    field="starter.javascript",
                    language="javascript",
                    severity=ValidationSeverity.WARNING,
                )
            )
        return issues

    def _validate_java_signature(self, code: str) -> List:
        issues = []
        method_match = re.search(
            r"public\s+(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)", code
        )
        if not method_match:
            method_match = re.search(
                r"(?:public|private|protected)\s+(?:static\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)",
                code,
            )
        if not method_match:
            method_match = re.search(
                r"(?:static\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)\s*\{", code
            )
        if not method_match:
            method_match = re.search(r"(\w+(?:\[\])?)\s+(\w+)\s*\(([^)]*)\)\s*\{", code)
        if not method_match:
            issues.append(
                self._create_issue(
                    message="No valid Java method definition found",
                    field="starter.java",
                    language="java",
                )
            )
            return issues
        return_type, method_name = method_match.group(1), method_match.group(2)
        if not re.match(r"^[a-z][a-zA-Z0-9_]*$", method_name):
            issues.append(
                self._create_issue(
                    message=f"Java method name '{method_name}' should follow camelCase convention",
                    field="starter.java",
                    language="java",
                    severity=ValidationSeverity.INFO,
                )
            )
        if return_type == "void":
            issues.append(
                self._create_issue(
                    message="Java method returns void - ensure this is intentional",
                    field="starter.java",
                    language="java",
                    severity=ValidationSeverity.INFO,
                )
            )
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
                issues.append(
                    self._create_issue(
                        message=f"Function names differ between Python ({python_name}) and JavaScript ({js_name})",
                        severity=ValidationSeverity.INFO,
                        details={"python": python_name, "javascript": js_name},
                    )
                )
        if python_name and java_name:
            if python_name.replace("_", "").lower() != java_name.lower():
                issues.append(
                    self._create_issue(
                        message=f"Function names differ between Python ({python_name}) and Java ({java_name})",
                        severity=ValidationSeverity.INFO,
                        details={"python": python_name, "java": java_name},
                    )
                )
        return issues
