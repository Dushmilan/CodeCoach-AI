"""
Comprehensive tests for simple validators (Python, JavaScript, Java).

This file re-exports tests from modularized test files for backwards compatibility.
All tests have been split into focused modules:

Unit Tests:
- backend/tests/unit/test_python_validator.py
- backend/tests/unit/test_javascript_validator.py
- backend/tests/unit/test_java_validator.py
- backend/tests/unit/test_test_runner.py
- backend/tests/unit/test_error_handler.py
- backend/tests/unit/test_results_display.py
- backend/tests/unit/test_output_comparison.py

Integration Tests:
- backend/tests/integration/test_validators_integration.py

For running tests, use:
    pytest backend/tests/unit/ -v           # Run all unit tests
    pytest backend/tests/integration/ -v    # Run all integration tests
    pytest backend/tests/ -v                # Run all tests
"""

# Re-export test classes for backwards compatibility
from backend.tests.unit.test_python_validator import (
    TestSimplePythonValidatorHappyPath,
    TestSimplePythonValidatorErrors,
    TestSimplePythonValidatorEdgeCases,
)

from backend.tests.unit.test_javascript_validator import (
    TestSimpleJavaScriptValidatorHappyPath,
    TestSimpleJavaScriptValidatorErrors,
    TestSimpleJavaScriptValidatorEdgeCases,
)

from backend.tests.unit.test_java_validator import (
    TestSimpleJavaValidatorHappyPath,
    TestSimpleJavaValidatorErrors,
    TestSimpleJavaValidatorEdgeCases,
)

from backend.tests.unit.test_test_runner import TestSimpleTestRunner

from backend.tests.unit.test_error_handler import TestValidationErrorHandler

from backend.tests.unit.test_results_display import TestResultsDisplay

from backend.tests.unit.test_output_comparison import TestOutputComparison


# Legacy test class aliases (for backwards compatibility)
TestSimplePythonValidator = TestSimplePythonValidatorHappyPath
TestSimpleJavaScriptValidator = TestSimpleJavaScriptValidatorHappyPath
TestSimpleJavaValidator = TestSimpleJavaValidatorHappyPath


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
