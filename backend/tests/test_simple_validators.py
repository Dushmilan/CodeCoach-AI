"""
Comprehensive tests for simple validators (Python only).

This file re-exports tests from modularized test files for backwards compatibility.
All tests have been split into focused modules:

Unit Tests:
- backend/tests/unit/test_python_validator.py
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
from tests.unit.test_python_validator import (
    TestSimplePythonValidatorHappyPath,
    TestSimplePythonValidatorErrors,
    TestSimplePythonValidatorEdgeCases,
)

from tests.unit.test_test_runner import TestSimpleTestRunner

from tests.unit.test_error_handler import TestValidationErrorHandler

from tests.unit.test_results_display import TestResultsDisplay

from tests.unit.test_output_comparison import TestOutputComparison


# Legacy test class aliases (for backwards compatibility)
TestSimplePythonValidator = TestSimplePythonValidatorHappyPath


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
