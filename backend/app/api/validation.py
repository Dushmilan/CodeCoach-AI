"""
Simple validation API endpoints for three-language code validation.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from app.services.simple_validators import SimpleTestRunner, SimpleResultsDisplay
from app.models.schemas import CodeValidationRequest, ValidationResult

router = APIRouter()

# Initialize test runner
runner = SimpleTestRunner()
display = SimpleResultsDisplay()


@router.post("/validate", response_model=ValidationResult)
async def validate_code(request: CodeValidationRequest):
    """
    Validate code against visible test cases for Java, JavaScript, or Python.
    
    Example request:
    {
        "language": "python",
        "code": "def twoSum(nums, target): return [0, 1]",
        "test_cases": [
            {
                "input": "[2,7,11,15]\n9",
                "expected_output": "[0, 1]",
                "description": "Basic two-sum case"
            }
        ]
    }
    """
    try:
        # Validate input
        if not request.code.strip():
            raise HTTPException(status_code=400, detail="Code cannot be empty")
        
        if not request.test_cases:
            raise HTTPException(status_code=400, detail="At least one test case is required")
        
        # Run validation
        results = runner.run_all_tests(
            language=request.language,
            code=request.code,
            test_cases=request.test_cases
        )
        
        # Format results for API response
        return ValidationResult(
            total_tests=results['total_tests'],
            passed_tests=results['passed_tests'],
            success_rate=results['success_rate'],
            results=results['results'],
            formatted_output=display.format_results(results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate/single")
async def validate_single_test(request: Dict[str, Any]):
    """
    Validate code against a single test case.
    
    Example request:
    {
        "language": "python",
        "code": "print('hello')",
        "test_case": {
            "input": "",
            "expected_output": "hello",
            "description": "Simple print test"
        }
    }
    """
    try:
        language = request.get('language')
        code = request.get('code')
        test_case = request.get('test_case')
        
        if not all([language, code, test_case]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        result = runner.run_single_test(language, code, test_case)
        
        return {
            "result": result,
            "formatted_output": f"Test: {test_case.get('description', 'Single test')}\n"
                               f"Status: {'✅ PASS' if result['passed'] else '❌ FAIL'}\n"
                               f"{'Error: ' + result['error'] if result.get('error') else ''}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/languages")
async def get_supported_languages():
    """Get list of supported languages for validation."""
    return {
        "languages": ["python", "javascript", "java"],
        "descriptions": {
            "python": "Python 3.x with standard library",
            "javascript": "Node.js with basic runtime",
            "java": "Java with standard library"
        },
        "limits": {
            "python": {"time_ms": 1000, "memory_mb": 64},
            "javascript": {"time_ms": 1500, "memory_mb": 128},
            "java": {"time_ms": 800, "memory_mb": 256}
        }
    }


@router.get("/example/{problem}")
async def get_example_test_cases(problem: str):
    """Get example test cases for common problems."""
    
    examples = {
        "two-sum": {
            "description": "Find two numbers that add up to target",
            "test_cases": [
                {
                    "input": "[2,7,11,15]\n9",
                    "expected_output": "[0, 1]",
                    "description": "Basic case with target at indices 0 and 1"
                },
                {
                    "input": "[3,2,4]\n6",
                    "expected_output": "[1, 2]",
                    "description": "Non-consecutive indices"
                },
                {
                    "input": "[3,3]\n6",
                    "expected_output": "[0, 1]",
                    "description": "Duplicate values"
                }
            ]
        },
        "valid-parentheses": {
            "description": "Check if parentheses are valid",
            "test_cases": [
                {
                    "input": "()",
                    "expected_output": "true",
                    "description": "Simple valid parentheses"
                },
                {
                    "input": "()[]{}",
                    "expected_output": "true",
                    "description": "Multiple types of brackets"
                },
                {
                    "input": "(]",
                    "expected_output": "false",
                    "description": "Mismatched brackets"
                }
            ]
        },
        "reverse-string": {
            "description": "Reverse a string",
            "test_cases": [
                {
                    "input": "hello",
                    "expected_output": "olleh",
                    "description": "Basic string reversal"
                },
                {
                    "input": "A man, a plan, a canal: Panama",
                    "expected_output": "amanaP :lanac a ,nalp a ,nam A",
                    "description": "String with punctuation"
                }
            ]
        }
    }
    
    if problem not in examples:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    return examples[problem]


@router.post("/health")
async def validation_health_check():
    """Health check endpoint for validation service."""
    try:
        # Test basic functionality
        test_code = "print('hello')"
        test_case = {
            "input": "",
            "expected_output": "hello",
            "description": "Health check"
        }
        
        result = runner.run_single_test('python', test_code, test_case)
        
        return {
            "status": "healthy",
            "python_available": True,
            "javascript_available": True,  # Assume available for now
            "java_available": True,      # Assume available for now
            "test_passed": result['passed']
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }