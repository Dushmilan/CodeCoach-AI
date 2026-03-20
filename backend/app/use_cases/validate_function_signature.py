"""
Function signature validation use case.

Validates that function signatures in starter code are properly defined
with correct parameter types and return types.
"""

from typing import List, Optional
import re

from app.models.schemas import Question
from app.models.question_validation_schemas import (
    UseCaseValidationResult,
    ValidationUseCase,
    ValidationSeverity,
    FunctionSignatureConfig,
)
from app.use_cases.base import BaseValidationUseCase


class FunctionSignatureValidationUseCase(BaseValidationUseCase):
    """
    Validates function signatures in starter code.
    
    Checks:
    - Function has a valid name
    - Parameters are properly defined
    - Return type is specified (if required)
    - Type hints are valid (Python)
    """
    
    # Common valid type hints
    VALID_PYTHON_TYPES = {
        "int", "str", "bool", "float", "list", "dict", "set", "tuple",
        "List", "Dict", "Set", "Tuple", "Optional", "Any", "Union",
        "None", "Callable", "Iterable", "Sequence"
    }
    
    def __init__(
        self,
        config: Optional[FunctionSignatureConfig] = None,
        require_type_hints: bool = True
    ):
        """
        Initialize function signature validation use case.
        
        Args:
            config: Configuration for function signature validation
            require_type_hints: Whether to require type hints
        """
        self.config = config or FunctionSignatureConfig()
        self.require_type_hints = require_type_hints
    
    @property
    def use_case(self) -> ValidationUseCase:
        return ValidationUseCase.FUNCTION_SIGNATURE
    
    async def _execute_validation(
        self, 
        question: Question
    ) -> UseCaseValidationResult:
        """Execute function signature validation."""
        issues: List = []
        
        # Validate Python signature
        issues.extend(self._validate_python_signature(question.starter.python))
        
        # Validate JavaScript signature
        issues.extend(self._validate_javascript_signature(question.starter.javascript))
        
        # Validate Java signature
        issues.extend(self._validate_java_signature(question.starter.java))
        
        # Check signature consistency across languages
        issues.extend(self._check_signature_consistency(question))
        
        passed = not any(
            issue.severity == ValidationSeverity.ERROR 
            for issue in issues
        )
        
        return self._create_result(passed=passed, issues=issues)
    
    def _validate_python_signature(self, code: str) -> List:
        """Validate Python function signature."""
        issues = []
        
        # Find function definition
        func_match = re.search(
            r'def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^\n:]+))?',
            code
        )
        
        if not func_match:
            issues.append(self._create_issue(
                message="No valid Python function definition found",
                field="starter.python",
                language="python",
                severity=ValidationSeverity.ERROR
            ))
            return issues
        
        func_name = func_match.group(1)
        params_str = func_match.group(2)
        return_type = func_match.group(3)
        
        # Check function name
        if not re.match(r'^[a-z_][a-z0-9_]*$', func_name, re.IGNORECASE):
            issues.append(self._create_issue(
                message=f"Invalid Python function name: {func_name}",
                field="starter.python",
                language="python",
                severity=ValidationSeverity.WARNING
            ))
        
        # Check parameters
        if params_str.strip():
            params = self._parse_python_params(params_str)
            
            for param in params:
                param_name, param_type = param
                
                # Check if type hint is present
                if self.require_type_hints and not param_type:
                    issues.append(self._create_issue(
                        message=f"Parameter '{param_name}' missing type hint",
                        field="starter.python",
                        language="python",
                        severity=ValidationSeverity.WARNING,
                        details={"parameter": param_name}
                    ))
                
                # Validate type hint if present
                if param_type and not self._is_valid_python_type(param_type):
                    issues.append(self._create_issue(
                        message=f"Potentially invalid type hint for parameter '{param_name}': {param_type}",
                        field="starter.python",
                        language="python",
                        severity=ValidationSeverity.INFO,
                        details={"parameter": param_name, "type": param_type}
                    ))
        
        # Check return type
        if self.require_type_hints and not return_type:
            issues.append(self._create_issue(
                message="Return type hint missing for Python function",
                field="starter.python",
                language="python",
                severity=ValidationSeverity.WARNING
            ))
        
        if return_type:
            return_type = return_type.strip()
            if not self._is_valid_python_type(return_type):
                issues.append(self._create_issue(
                    message=f"Potentially invalid return type: {return_type}",
                    field="starter.python",
                    language="python",
                    severity=ValidationSeverity.INFO,
                    details={"return_type": return_type}
                ))
        
        return issues
    
    def _parse_python_params(self, params_str: str) -> List:
        """Parse Python function parameters."""
        params = []
        
        # Split by comma, handling nested brackets
        depth = 0
        current = ""
        
        for char in params_str:
            if char in '([{':
                depth += 1
                current += char
            elif char in ')]}':
                depth -= 1
                current += char
            elif char == ',' and depth == 0:
                if current.strip():
                    params.append(self._parse_single_param(current.strip()))
                current = ""
            else:
                current += char
        
        if current.strip():
            params.append(self._parse_single_param(current.strip()))
        
        return params
    
    def _parse_single_param(self, param: str) -> tuple:
        """Parse a single parameter into name and type."""
        # Handle default values
        if '=' in param:
            param = param.split('=')[0].strip()
        
        # Handle type hints
        if ':' in param:
            parts = param.split(':', 1)
            name = parts[0].strip()
            type_hint = parts[1].strip() if len(parts) > 1 else None
            return (name, type_hint)
        
        return (param.strip(), None)
    
    def _is_valid_python_type(self, type_str: str) -> bool:
        """Check if a Python type hint is valid."""
        # Remove any generic parameters for checking
        type_str = type_str.strip()
        
        # Check basic types
        if type_str in self.VALID_PYTHON_TYPES:
            return True
        
        # Check for generic types (List[int], Dict[str, int], etc.)
        generic_match = re.match(r'(\w+)\[', type_str)
        if generic_match:
            base_type = generic_match.group(1)
            if base_type in self.VALID_PYTHON_TYPES:
                return True
        
        # Check for Optional, Union, etc.
        if type_str.startswith(('Optional[', 'Union[', 'Callable[')):
            return True
        
        # Allow lowercase versions
        if type_str.lower() in {t.lower() for t in self.VALID_PYTHON_TYPES}:
            return True
        
        return False
    
    def _validate_javascript_signature(self, code: str) -> List:
        """Validate JavaScript function signature."""
        issues = []
        
        # Find function definition
        func_match = re.search(
            r'function\s+(\w+)\s*\(([^)]*)\)',
            code
        )
        
        if not func_match:
            # Check for arrow function
            func_match = re.search(
                r'(?:const|let|var)\s+(\w+)\s*=\s*(?:\([^)]*\)|[^=])\s*=>',
                code
            )
        
        if not func_match:
            issues.append(self._create_issue(
                message="No valid JavaScript function definition found",
                field="starter.javascript",
                language="javascript",
                severity=ValidationSeverity.ERROR
            ))
            return issues
        
        func_name = func_match.group(1)
        
        # Check function name
        if not re.match(r'^[a-zA-Z_$][a-zA-Z0-9_$]*$', func_name):
            issues.append(self._create_issue(
                message=f"Invalid JavaScript function name: {func_name}",
                field="starter.javascript",
                language="javascript",
                severity=ValidationSeverity.WARNING
            ))
        
        return issues
    
    def _validate_java_signature(self, code: str) -> List:
        """Validate Java method signature."""
        issues = []
        
        # Find method definition - try multiple patterns
        # Pattern 1: public with return type
        method_match = re.search(
            r'public\s+(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)',
            code
        )
        
        # Pattern 2: any access modifier with return type
        if not method_match:
            method_match = re.search(
                r'(?:public|private|protected)\s+(?:static\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)',
                code
            )
        
        # Pattern 3: method without explicit access modifier (package-private)
        if not method_match:
            method_match = re.search(
                r'(?:static\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)\s*\{',
                code
            )
        
        # Pattern 4: Look for any method-like pattern
        if not method_match:
            method_match = re.search(
                r'(\w+(?:\[\])?)\s+(\w+)\s*\(([^)]*)\)\s*\{',
                code
            )
        
        if not method_match:
            issues.append(self._create_issue(
                message="No valid Java method definition found",
                field="starter.java",
                language="java",
                severity=ValidationSeverity.ERROR
            ))
            return issues
        
        return_type = method_match.group(1)
        method_name = method_match.group(2)
        
        # Check method name
        if not re.match(r'^[a-z][a-zA-Z0-9_]*$', method_name):
            issues.append(self._create_issue(
                message=f"Java method name '{method_name}' should follow camelCase convention",
                field="starter.java",
                language="java",
                severity=ValidationSeverity.INFO
            ))
        
        # Check for void return type
        if return_type == "void":
            issues.append(self._create_issue(
                message="Java method returns void - ensure this is intentional",
                field="starter.java",
                language="java",
                severity=ValidationSeverity.INFO
            ))
        
        return issues
    
    def _check_signature_consistency(self, question: Question) -> List:
        """Check that function signatures are consistent across languages."""
        issues = []
        
        # Extract function names from each language
        python_name = self._extract_python_function_name(question.starter.python)
        js_name = self._extract_js_function_name(question.starter.javascript)
        java_name = self._extract_java_method_name(question.starter.java)
        
        # Check if names are consistent (allowing for language conventions)
        # Python/JS typically use snake_case, Java uses camelCase
        # So we normalize for comparison
        
        if python_name and js_name:
            # Normalize names for comparison
            python_normalized = python_name.replace('_', '').lower()
            js_normalized = js_name.lower()
            
            if python_normalized != js_normalized:
                issues.append(self._create_issue(
                    message=f"Function names differ between Python ({python_name}) and JavaScript ({js_name})",
                    severity=ValidationSeverity.INFO,
                    details={
                        "python": python_name,
                        "javascript": js_name
                    }
                ))
        
        if python_name and java_name:
            python_normalized = python_name.replace('_', '').lower()
            java_normalized = java_name.lower()
            
            if python_normalized != java_normalized:
                issues.append(self._create_issue(
                    message=f"Function names differ between Python ({python_name}) and Java ({java_name})",
                    severity=ValidationSeverity.INFO,
                    details={
                        "python": python_name,
                        "java": java_name
                    }
                ))
        
        return issues
    
    def _extract_python_function_name(self, code: str) -> Optional[str]:
        """Extract function name from Python code."""
        match = re.search(r'def\s+(\w+)\s*\(', code)
        return match.group(1) if match else None
    
    def _extract_js_function_name(self, code: str) -> Optional[str]:
        """Extract function name from JavaScript code."""
        match = re.search(r'function\s+(\w+)\s*\(', code)
        if match:
            return match.group(1)
        
        # Arrow function
        match = re.search(r'(?:const|let|var)\s+(\w+)\s*=', code)
        return match.group(1) if match else None
    
    def _extract_java_method_name(self, code: str) -> Optional[str]:
        """Extract method name from Java code."""
        match = re.search(r'public\s+\w+\s+(\w+)\s*\(', code)
        return match.group(1) if match else None
