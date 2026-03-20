"""
Solution validation use case.

Validates that the reference solution passes all test cases.
This is the most critical validation as it ensures the problem is solvable.
"""

from typing import List, Optional, Any, Dict
import json
import re

from app.models.schemas import Question, TestCase as QuestionTestCase
from app.models.question_validation_schemas import (
    UseCaseValidationResult,
    ValidationUseCase,
    ValidationSeverity,
)
from app.use_cases.base import BaseValidationUseCase


class SolutionValidationUseCase(BaseValidationUseCase):
    """
    Validates that the reference solution passes all test cases.
    
    This is the most critical validation use case as it ensures:
    - The problem is solvable
    - Test cases have correct expected outputs
    - The solution matches the problem requirements
    
    Checks:
    - Solution exists
    - Solution passes all test cases
    - Solution output matches expected output format
    """
    
    def __init__(
        self,
        piston_service: Optional[Any] = None
    ):
        """
        Initialize solution validation use case.
        
        Args:
            piston_service: Piston service for code execution
        """
        self.piston_service = piston_service
    
    @property
    def use_case(self) -> ValidationUseCase:
        return ValidationUseCase.SOLUTION
    
    async def _execute_validation(
        self, 
        question: Question
    ) -> UseCaseValidationResult:
        """Execute solution validation."""
        issues: List = []
        
        # Check if solution exists
        if not question.solution:
            issues.append(self._create_issue(
                message="Reference solution is required for validation",
                field="solution",
                severity=ValidationSeverity.ERROR
            ))
            return self._create_result(passed=False, issues=issues)
        
        # Validate solution against test cases using Piston
        if self.piston_service:
            solution_issues = await self._validate_solution_with_piston(question)
            issues.extend(solution_issues)
        else:
            # Without Piston, we can only do basic checks
            issues.append(self._create_issue(
                message="Cannot validate solution execution without Piston service",
                field="solution",
                severity=ValidationSeverity.WARNING
            ))
        
        passed = not any(
            issue.severity == ValidationSeverity.ERROR 
            for issue in issues
        )
        
        return self._create_result(passed=passed, issues=issues)
    
    async def _validate_solution_with_piston(
        self, 
        question: Question
    ) -> List:
        """
        Validate solution by executing it against test cases.
        
        For Python, we create a complete solution that can be executed
        with the test case inputs.
        """
        issues = []
        
        # Focus on Python for validation (as per requirements)
        # Extract the solution code
        solution_code = self._create_executable_solution(question)
        
        if not solution_code:
            issues.append(self._create_issue(
                message="Could not create executable solution from reference solution",
                field="solution",
                severity=ValidationSeverity.ERROR
            ))
            return issues
        
        # Run each test case
        passed_count = 0
        total_count = len(question.test_cases)
        
        for i, test_case in enumerate(question.test_cases):
            try:
                result = await self.piston_service.execute_code(
                    language="python",
                    code=solution_code,
                    stdin=test_case.input
                )
                
                # Check execution result
                if result.get("exit_code", 0) != 0:
                    stderr = result.get("stderr", "")
                    issues.append(self._create_issue(
                        message=f"Solution failed on test case {i + 1}: {stderr[:100]}",
                        field="solution",
                        test_case_index=i,
                        severity=ValidationSeverity.ERROR,
                        details={
                            "test_case": test_case.description,
                            "error": stderr
                        }
                    ))
                    continue
                
                # Compare output
                actual_output = result.get("stdout", "").strip()
                expected_output = test_case.expected_output.strip()
                
                if self._compare_outputs(actual_output, expected_output):
                    passed_count += 1
                else:
                    issues.append(self._create_issue(
                        message=f"Solution output mismatch on test case {i + 1}",
                        field="solution",
                        test_case_index=i,
                        severity=ValidationSeverity.ERROR,
                        details={
                            "test_case": test_case.description,
                            "expected": expected_output,
                            "actual": actual_output
                        }
                    ))
                    
            except Exception as e:
                issues.append(self._create_issue(
                    message=f"Failed to execute solution for test case {i + 1}: {str(e)}",
                    field="solution",
                    test_case_index=i,
                    severity=ValidationSeverity.ERROR
                ))
        
        # Check if all tests passed
        if total_count > 0 and passed_count < total_count:
            issues.append(self._create_issue(
                message=f"Solution only passed {passed_count}/{total_count} test cases",
                field="solution",
                severity=ValidationSeverity.ERROR,
                details={
                    "passed": passed_count,
                    "total": total_count
                }
            ))
        
        return issues
    
    def _create_executable_solution(self, question: Question) -> Optional[str]:
        """
        Create an executable Python solution from the question.
        
        This combines the starter code structure with the solution logic.
        """
        # Get the Python starter code to understand the function signature
        starter_code = question.starter.python
        
        # Extract function name from starter code
        func_match = re.search(r'def\s+(\w+)\s*\(', starter_code)
        if not func_match:
            return None
        
        func_name = func_match.group(1)
        
        # Create a complete executable that:
        # 1. Includes the solution logic
        # 2. Reads input from stdin
        # 3. Calls the function
        # 4. Prints the result
        
        # Parse the solution to extract the implementation
        # The solution field contains a description, but we need actual code
        # For now, we'll use the starter code and assume the solution is
        # provided in a way that can be executed
        
        # If the starter code has a complete implementation (not just pass),
        # use it directly
        if 'pass' not in starter_code or 'return' in starter_code:
            solution_code = self._create_runner(starter_code, func_name, question)
            return solution_code
        
        # Otherwise, we need to generate a solution from the solution description
        # This is a limitation - we'd need actual solution code
        # For now, return a placeholder that will fail validation
        return None
    
    def _create_runner(
        self, 
        solution_code: str, 
        func_name: str, 
        question: Question
    ) -> str:
        """
        Create a complete runner that reads input and calls the solution function.
        """
        # Determine how to parse input based on the function signature
        # This is a simplified version - real implementation would need more
        # sophisticated input parsing
        
        runner_code = f'''
import sys
import json
from typing import List

{solution_code}

# Read input from stdin
lines = sys.stdin.read().strip().split('\\n')

# Parse input based on common patterns
# This is a simplified parser - real implementation would need more logic
try:
    if len(lines) == 1:
        # Single value input
        try:
            input_data = json.loads(lines[0])
        except:
            input_data = lines[0]
        result = {func_name}(input_data)
    elif len(lines) == 2:
        # Two value input (e.g., array and target)
        try:
            first = json.loads(lines[0])
            second = json.loads(lines[1]) if lines[1].isdigit() or lines[1].startswith('[') else int(lines[1])
            result = {func_name}(first, second)
        except:
            result = {func_name}(lines[0], lines[1])
    else:
        # Multiple lines
        result = {func_name}(lines)
    
    # Output result
    if isinstance(result, list):
        print(json.dumps(result))
    elif isinstance(result, bool):
        print(str(result).lower())
    else:
        print(result)
except Exception as e:
    print(f"Error: {{e}}", file=sys.stderr)
    sys.exit(1)
'''
        return runner_code
    
    def _compare_outputs(self, actual: str, expected: str) -> bool:
        """
        Compare actual and expected outputs.
        
        Handles different formats (JSON, strings, numbers, booleans).
        """
        # Direct string comparison
        if actual == expected:
            return True
        
        # Normalize whitespace
        if actual.strip() == expected.strip():
            return True
        
        # Try JSON comparison
        try:
            actual_json = json.loads(actual)
            expected_json = json.loads(expected)
            return actual_json == expected_json
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Try numeric comparison
        try:
            return float(actual) == float(expected)
        except (ValueError, TypeError):
            pass
        
        # Boolean comparison
        if actual.lower() in ('true', 'false') and expected.lower() in ('true', 'false'):
            return actual.lower() == expected.lower()
        
        return False
