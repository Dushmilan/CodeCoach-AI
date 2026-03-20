"""
Simple validators for Java, JavaScript, and Python code validation.
Focuses on visible test cases with basic output matching.
"""

import json
import subprocess
import tempfile
import os
import time
from typing import Dict, Any, List


class SimplePythonValidator:
    """Simple Python code validator using subprocess execution."""
    
    def __init__(self):
        self.limits = {'time_ms': 1000, 'memory_mb': 64}
    
    def validate(self, code: str, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Python code against a test case."""
        try:
            # Create temporary file for Python code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute with input
                start_time = time.time()
                
                process = subprocess.run(
                    ['python', temp_file],
                    input=test_case['input'],
                    text=True,
                    capture_output=True,
                    timeout=self.limits['time_ms'] / 1000
                )
                
                execution_time = (time.time() - start_time) * 1000
                
                if process.returncode != 0:
                    return {
                        'passed': False,
                        'error': process.stderr,
                        'execution_time': execution_time
                    }
                
                # Compare outputs
                actual_output = process.stdout.strip()
                expected_output = test_case['expected_output'].strip()
                
                passed = self.compare_outputs(actual_output, expected_output)
                
                return {
                    'passed': passed,
                    'actual_output': actual_output,
                    'expected_output': expected_output,
                    'execution_time': execution_time,
                    'error': None
                }
                
            except subprocess.TimeoutExpired:
                return {
                    'passed': False,
                    'error': 'Time limit exceeded',
                    'execution_time': self.limits['time_ms']
                }
            finally:
                os.unlink(temp_file)
                
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'execution_time': 0
            }
    
    def compare_outputs(self, actual: str, expected: str) -> bool:
        """Compare actual vs expected output."""
        # Basic string comparison
        if actual == expected:
            return True
        
        # Try JSON comparison for arrays/objects
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
        
        return False


class SimpleJavaScriptValidator:
    """Simple JavaScript code validator using Node.js."""
    
    def __init__(self):
        self.limits = {'time_ms': 1500, 'memory_mb': 128}
    
    def validate(self, code: str, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JavaScript code against a test case."""
        try:
            # Create temporary file for JavaScript code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute with input
                start_time = time.time()
                
                process = subprocess.run(
                    ['node', temp_file],
                    input=test_case['input'],
                    text=True,
                    capture_output=True,
                    timeout=self.limits['time_ms'] / 1000
                )
                
                execution_time = (time.time() - start_time) * 1000
                
                if process.returncode != 0:
                    return {
                        'passed': False,
                        'error': process.stderr,
                        'execution_time': execution_time
                    }
                
                # Compare outputs
                actual_output = process.stdout.strip()
                expected_output = test_case['expected_output'].strip()
                
                passed = self.compare_outputs(actual_output, expected_output)
                
                return {
                    'passed': passed,
                    'actual_output': actual_output,
                    'expected_output': expected_output,
                    'execution_time': execution_time,
                    'error': None
                }
                
            except subprocess.TimeoutExpired:
                return {
                    'passed': False,
                    'error': 'Time limit exceeded',
                    'execution_time': self.limits['time_ms']
                }
            finally:
                os.unlink(temp_file)
                
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'execution_time': 0
            }
    
    def compare_outputs(self, actual: str, expected: str) -> bool:
        """Compare actual vs expected output."""
        return SimplePythonValidator().compare_outputs(actual, expected)


class SimpleJavaValidator:
    """Simple Java code validator with compilation."""
    
    def __init__(self):
        self.limits = {'time_ms': 800, 'memory_mb': 256}
    
    def validate(self, code: str, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Java code against a test case."""
        try:
            # Create temporary directory for Java files
            with tempfile.TemporaryDirectory() as temp_dir:
                java_file = os.path.join(temp_dir, 'Solution.java')
                class_file = os.path.join(temp_dir, 'Solution.class')
                
                # Write Java code
                with open(java_file, 'w') as f:
                    f.write(code)
                
                # Compile Java code
                compile_process = subprocess.run(
                    ['javac', java_file],
                    capture_output=True,
                    text=True
                )
                
                if compile_process.returncode != 0:
                    return {
                        'passed': False,
                        'error': f"Compilation error: {compile_process.stderr}",
                        'execution_time': 0
                    }
                
                # Execute compiled Java code
                start_time = time.time()
                
                process = subprocess.run(
                    ['java', '-cp', temp_dir, 'Solution'],
                    input=test_case['input'],
                    text=True,
                    capture_output=True,
                    timeout=self.limits['time_ms'] / 1000
                )
                
                execution_time = (time.time() - start_time) * 1000
                
                if process.returncode != 0:
                    return {
                        'passed': False,
                        'error': process.stderr,
                        'execution_time': execution_time
                    }
                
                # Compare outputs
                actual_output = process.stdout.strip()
                expected_output = test_case['expected_output'].strip()
                
                passed = self.compare_outputs(actual_output, expected_output)
                
                return {
                    'passed': passed,
                    'actual_output': actual_output,
                    'expected_output': expected_output,
                    'execution_time': execution_time,
                    'error': None
                }
                
        except subprocess.TimeoutExpired:
            return {
                'passed': False,
                'error': 'Time limit exceeded',
                'execution_time': self.limits['time_ms']
            }
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'execution_time': 0
            }
    
    def compare_outputs(self, actual: str, expected: str) -> bool:
        """Compare actual vs expected output."""
        return SimplePythonValidator().compare_outputs(actual, expected)


class SimpleTestRunner:
    """Unified test runner for all three languages."""
    
    def __init__(self):
        self.validators = {
            'python': SimplePythonValidator(),
            'javascript': SimpleJavaScriptValidator(),
            'java': SimpleJavaValidator()
        }
    
    def run_single_test(self, language: str, code: str, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test case."""
        if language not in self.validators:
            return {
                'passed': False,
                'error': f'Unsupported language: {language}',
                'execution_time': 0
            }
        
        validator = self.validators[language]
        return validator.validate(code, test_case)
    
    def run_all_tests(self, language: str, code: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run all test cases for a code submission."""
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            result = self.run_single_test(language, code, test_case)
            result['test_number'] = i
            result['test_description'] = test_case.get('description', f'Test {i}')
            results.append(result)
        
        passed_tests = sum(1 for r in results if r['passed'])
        total_tests = len(results)
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
            'results': results
        }


class ValidationErrorHandler:
    """Handle and format validation errors for user display."""
    
    @staticmethod
    def format_error(error_type: str, message: str) -> str:
        """Format error messages for user-friendly display."""
        error_map = {
            'syntax': "💥 Syntax Error: Check your code structure",
            'timeout': "⏰ Time Limit Exceeded: Your code took too long to execute",
            'memory': "🧠 Memory Limit Exceeded: Your code used too much memory",
            'runtime': f"⚠️ Runtime Error: {message}",
            'compilation': f"🔧 Compilation Error: {message}",
            'output': "❌ Wrong Answer: Output doesn't match expected"
        }
        
        # Detect error type from message
        if 'timeout' in message.lower() or 'time limit' in message.lower():
            return error_map['timeout']
        elif 'memory' in message.lower():
            return error_map['memory']
        elif 'syntax' in message.lower():
            return error_map['syntax']
        elif 'compilation' in message.lower() or 'javac' in message.lower():
            return error_map['compilation']
        else:
            return error_map.get(error_type, f"❓ Error: {message}")


class SimpleResultsDisplay:
    """Display validation results in user-friendly format."""
    
    @staticmethod
    def format_results(results: Dict[str, Any]) -> str:
        """Format test results for display."""
        output = []
        
        # Summary
        total = results['total_tests']
        passed = results['passed_tests']
        success_rate = results['success_rate']
        
        output.append(f"🎯 Test Results: {passed}/{total} passed ({success_rate:.0%})")
        output.append("=" * 50)
        
        # Individual test results
        for result in results['results']:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            test_desc = result['test_description']
            
            output.append(f"\n{status} {result['test_number']}. {test_desc}")
            
            if not result['passed']:
                if result.get('error'):
                    error_msg = ValidationErrorHandler.format_error('runtime', result['error'])
                    output.append(f"   {error_msg}")
                else:
                    output.append(f"   Expected: {result['expected_output']}")
                    output.append(f"   Actual:   {result['actual_output']}")
            
            if result.get('execution_time'):
                output.append(f"   Time: {result['execution_time']:.1f}ms")
        
        return "\n".join(output)


# Example usage and test cases
if __name__ == "__main__":
    # Example test cases
    test_cases = [
        {
            "input": "[2,7,11,15]\n9",
            "expected_output": "[0,1]",
            "description": "Basic two-sum case"
        },
        {
            "input": "[3,2,4]\n6",
            "expected_output": "[1,2]",
            "description": "Non-consecutive indices"
        }
    ]
    
    # Example Python code
    python_code = '''
def twoSum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []

# Read input
import sys
nums = eval(sys.stdin.readline().strip())
target = int(sys.stdin.readline().strip())
result = twoSum(nums, target)
print(result)
'''
    
    # Run validation
    runner = SimpleTestRunner()
    results = runner.run_all_tests('python', python_code, test_cases)
    
    # Display results
    display = SimpleResultsDisplay()
    print(display.format_results(results))