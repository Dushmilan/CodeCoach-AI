"""
Unit tests for SimpleResultsDisplay.
Tests cover results formatting and display functionality.
"""

import pytest
from app.services.simple_validators import SimpleResultsDisplay


class TestResultsDisplay:
    """Test suite for SimpleResultsDisplay."""

    def test_results_formatting(self):
        """Test results display formatting."""
        display = SimpleResultsDisplay()

        results = {
            'total_tests': 2,
            'passed_tests': 1,
            'success_rate': 0.5,
            'results': [
                {
                    'passed': True,
                    'test_description': 'Basic case',
                    'test_number': 1
                },
                {
                    'passed': False,
                    'expected_output': '[0,1]',
                    'actual_output': '[1,0]',
                    'test_description': 'Wrong order',
                    'test_number': 2,
                    'error': None
                }
            ]
        }

        formatted = display.format_results(results)
        assert "1/2" in formatted
        assert "PASS" in formatted
        assert "FAIL" in formatted

    def test_results_formatting_all_pass(self):
        """Test results display when all tests pass."""
        display = SimpleResultsDisplay()

        results = {
            'total_tests': 3,
            'passed_tests': 3,
            'success_rate': 1.0,
            'results': [
                {'passed': True, 'test_description': 'Test 1', 'test_number': 1},
                {'passed': True, 'test_description': 'Test 2', 'test_number': 2},
                {'passed': True, 'test_description': 'Test 3', 'test_number': 3}
            ]
        }

        formatted = display.format_results(results)
        assert "3/3" in formatted
        assert "100%" in formatted
        assert formatted.count("PASS") == 3

    def test_results_formatting_all_fail(self):
        """Test results display when all tests fail."""
        display = SimpleResultsDisplay()

        results = {
            'total_tests': 2,
            'passed_tests': 0,
            'success_rate': 0.0,
            'results': [
                {
                    'passed': False,
                    'test_description': 'Test 1',
                    'test_number': 1,
                    'expected_output': 'a',
                    'actual_output': 'b',
                    'error': None
                },
                {
                    'passed': False,
                    'test_description': 'Test 2',
                    'test_number': 2,
                    'error': 'Runtime error'
                }
            ]
        }

        formatted = display.format_results(results)
        assert "0/2" in formatted
        assert "0%" in formatted
        assert formatted.count("FAIL") == 2

    def test_results_formatting_empty(self):
        """Test results display with no tests."""
        display = SimpleResultsDisplay()

        results = {
            'total_tests': 0,
            'passed_tests': 0,
            'success_rate': 0,
            'results': []
        }

        formatted = display.format_results(results)
        assert "0/0" in formatted

    def test_results_formatting_with_execution_time(self):
        """Test results display with execution time."""
        display = SimpleResultsDisplay()

        results = {
            'total_tests': 1,
            'passed_tests': 1,
            'success_rate': 1.0,
            'results': [
                {
                    'passed': True,
                    'test_description': 'Test 1',
                    'test_number': 1,
                    'execution_time': 123.45
                }
            ]
        }

        formatted = display.format_results(results)
        assert "123.45ms" in formatted or "123.5ms" in formatted or "123ms" in formatted
