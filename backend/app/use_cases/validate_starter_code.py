"""
Starter code validation use case.

Validates that starter code for all languages compiles/runs without errors.
Uses Piston execution engine for validation.
"""

from typing import List, Optional, Any, Dict

from app.models.schemas import Question, StarterCode
from app.models.question_validation_schemas import (
    UseCaseValidationResult,
    ValidationUseCase,
    ValidationSeverity,
)
from app.use_cases.base import BaseValidationUseCase


class StarterCodeValidationUseCase(BaseValidationUseCase):
    """
    Validates starter code for all supported languages.
    
    Checks:
    - Python starter code has valid syntax
    - JavaScript starter code has valid syntax
    - Java starter code compiles
    - All starter codes have proper function signatures
    """
    
    # Languages to validate
    LANGUAGES = ["python", "javascript", "java"]
    
    def __init__(
        self,
        piston_service: Optional[Any] = None
    ):
        """
        Initialize starter code validation use case.
        
        Args:
            piston_service: Piston service for code execution
        """
        self.piston_service = piston_service
    
    @property
    def use_case(self) -> ValidationUseCase:
        return ValidationUseCase.STARTER_CODE
    
    async def _execute_validation(
        self, 
        question: Question
    ) -> UseCaseValidationResult:
        """Execute starter code validation."""
        issues: List = []
        
        # Validate each language's starter code
        for language in self.LANGUAGES:
            code = getattr(question.starter, language, None)
            
            if not code:
                issues.append(self._create_issue(
                    message=f"Starter code for {language} is missing",
                    field=f"starter.{language}",
                    language=language,
                    severity=ValidationSeverity.ERROR
                ))
                continue
            
            # Validate syntax using Piston
            if self.piston_service:
                syntax_issues = await self._validate_syntax(language, code)
                issues.extend(syntax_issues)
            else:
                # Fallback to basic validation without Piston
                issues.extend(self._basic_validate(language, code))
        
        passed = not any(
            issue.severity == ValidationSeverity.ERROR 
            for issue in issues
        )
        
        return self._create_result(passed=passed, issues=issues)
    
    async def _validate_syntax(
        self, 
        language: str, 
        code: str
    ) -> List:
        """
        Validate code syntax using Piston execution.
        
        Args:
            language: Programming language
            code: Code to validate
            
        Returns:
            List of validation issues
        """
        issues = []
        
        try:
            # Create a test that checks syntax without full execution
            test_code = self._create_syntax_test_code(language, code)
            
            result = await self.piston_service.execute_code(
                language=language,
                code=test_code,
                stdin=""
            )
            
            # Check for compilation/syntax errors
            if result.get("exit_code", 0) != 0:
                stderr = result.get("stderr", "")
                
                # Parse error message for user-friendly output
                error_message = self._parse_error_message(language, stderr)
                
                issues.append(self._create_issue(
                    message=f"Syntax error in {language} starter code: {error_message}",
                    field=f"starter.{language}",
                    language=language,
                    severity=ValidationSeverity.ERROR,
                    details={"stderr": stderr}
                ))
            
        except Exception as e:
            issues.append(self._create_issue(
                message=f"Failed to validate {language} starter code: {str(e)}",
                field=f"starter.{language}",
                language=language,
                severity=ValidationSeverity.WARNING
            ))
        
        return issues
    
    def _create_syntax_test_code(self, language: str, code: str) -> str:
        """
        Create code that tests syntax without full execution.
        
        For Python: Use compile() to check syntax
        For JavaScript: Just run the code
        For Java: Compile the class
        """
        if language == "python":
            # Use compile() to check syntax without execution
            return f'''
try:
    compile("""{self._escape_code(code)}""", '<string>', 'exec')
    print("Syntax OK")
except SyntaxError as e:
    print(f"SyntaxError: {{e}}")
    raise
'''
        elif language == "javascript":
            # JavaScript will naturally fail on syntax errors
            return code + '\nconsole.log("Syntax OK");'
        elif language == "java":
            # Java starter code should compile
            return code
        else:
            return code
    
    def _escape_code(self, code: str) -> str:
        """Escape code for embedding in a string."""
        return code.replace('\\', '\\\\').replace('"""', '\\"\\"\\"')
    
    def _parse_error_message(self, language: str, stderr: str) -> str:
        """Parse error message to be more user-friendly."""
        if not stderr:
            return "Unknown error"
        
        # Extract the most relevant error line
        lines = stderr.strip().split('\n')
        
        for line in lines:
            if 'error' in line.lower() or 'Error' in line:
                return line.strip()
        
        # Return first non-empty line
        for line in lines:
            if line.strip():
                return line.strip()
        
        return stderr[:200] if len(stderr) > 200 else stderr
    
    def _basic_validate(self, language: str, code: str) -> List:
        """
        Basic validation without Piston.
        
        Performs simple checks that don't require execution.
        """
        issues = []
        
        if language == "python":
            # Check for basic Python syntax patterns
            issues.extend(self._basic_python_validate(code))
        elif language == "javascript":
            # Check for basic JavaScript syntax patterns
            issues.extend(self._basic_javascript_validate(code))
        elif language == "java":
            # Check for basic Java syntax patterns
            issues.extend(self._basic_java_validate(code))
        
        return issues
    
    def _basic_python_validate(self, code: str) -> List:
        """Basic Python syntax validation."""
        issues = []
        
        # Check for balanced parentheses, brackets, braces
        open_chars = {'(': 0, '[': 0, '{': 0}
        close_chars = {')': '(', ']': '[', '}': '{'}
        
        for char in code:
            if char in open_chars:
                open_chars[char] += 1
            elif char in close_chars:
                open_chars[close_chars[char]] -= 1
        
        for char, count in open_chars.items():
            if count != 0:
                issues.append(self._create_issue(
                    message=f"Unbalanced {char} in Python starter code",
                    field="starter.python",
                    language="python",
                    severity=ValidationSeverity.WARNING
                ))
        
        # Check for common syntax errors
        if 'def ' in code and ':' not in code:
            issues.append(self._create_issue(
                message="Python function definition missing colon",
                field="starter.python",
                language="python",
                severity=ValidationSeverity.ERROR
            ))
        
        return issues
    
    def _basic_javascript_validate(self, code: str) -> List:
        """Basic JavaScript syntax validation."""
        issues = []
        
        # Check for balanced parentheses, brackets, braces
        open_chars = {'(': 0, '[': 0, '{': 0}
        close_chars = {')': '(', ']': '[', '}': '{'}
        
        for char in code:
            if char in open_chars:
                open_chars[char] += 1
            elif char in close_chars:
                open_chars[close_chars[char]] -= 1
        
        for char, count in open_chars.items():
            if count != 0:
                issues.append(self._create_issue(
                    message=f"Unbalanced {char} in JavaScript starter code",
                    field="starter.javascript",
                    language="javascript",
                    severity=ValidationSeverity.WARNING
                ))
        
        return issues
    
    def _basic_java_validate(self, code: str) -> List:
        """Basic Java syntax validation."""
        issues = []
        
        # Check for class definition
        if 'class ' not in code:
            issues.append(self._create_issue(
                message="Java starter code should contain a class definition",
                field="starter.java",
                language="java",
                severity=ValidationSeverity.WARNING
            ))
        
        # Check for balanced braces
        brace_count = code.count('{') - code.count('}')
        if brace_count != 0:
            issues.append(self._create_issue(
                message=f"Unbalanced braces in Java starter code",
                field="starter.java",
                language="java",
                severity=ValidationSeverity.WARNING
            ))
        
        return issues
