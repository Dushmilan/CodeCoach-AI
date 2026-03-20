"""
Unit tests for ValidationErrorHandler.
Tests cover error formatting and automatic error type detection.
"""

import pytest
from app.services.simple_validators import ValidationErrorHandler


class TestValidationErrorHandler:
    """Test suite for ValidationErrorHandler."""

    def test_error_formatting_syntax(self):
        """Test syntax error formatting."""
        handler = ValidationErrorHandler()
        assert "Syntax Error" in handler.format_error('syntax', 'invalid syntax')

    def test_error_formatting_timeout(self):
        """Test timeout error formatting."""
        handler = ValidationErrorHandler()
        assert "Time Limit Exceeded" in handler.format_error('timeout', 'timeout')

    def test_error_formatting_memory(self):
        """Test memory error formatting."""
        handler = ValidationErrorHandler()
        assert "Memory Limit Exceeded" in handler.format_error('memory', 'memory')

    def test_error_formatting_runtime(self):
        """Test runtime error formatting."""
        handler = ValidationErrorHandler()
        result = handler.format_error('runtime', 'NullPointerException')
        assert "Runtime Error" in result
        assert "NullPointerException" in result

    def test_error_formatting_compilation(self):
        """Test compilation error formatting."""
        handler = ValidationErrorHandler()
        result = handler.format_error('compilation', 'cannot find symbol')
        assert "Compilation Error" in result

    def test_error_formatting_output(self):
        """Test output error formatting."""
        handler = ValidationErrorHandler()
        assert "Wrong Answer" in handler.format_error('output', 'mismatch')

    def test_error_formatting_unknown(self):
        """Test unknown error formatting."""
        handler = ValidationErrorHandler()
        result = handler.format_error('unknown', 'something went wrong')
        assert "Error" in result
        assert "something went wrong" in result

    def test_error_formatting_timeout_detection(self):
        """Test automatic timeout detection from message."""
        handler = ValidationErrorHandler()
        result = handler.format_error('runtime', 'Time limit exceeded')
        assert "Time Limit Exceeded" in result

    def test_error_formatting_memory_detection(self):
        """Test automatic memory error detection from message."""
        handler = ValidationErrorHandler()
        result = handler.format_error('runtime', 'Out of memory error')
        assert "Memory Limit Exceeded" in result

    def test_error_formatting_syntax_detection(self):
        """Test automatic syntax error detection from message."""
        handler = ValidationErrorHandler()
        result = handler.format_error('runtime', 'Syntax error on line 5')
        assert "Syntax Error" in result

    def test_error_formatting_compilation_detection(self):
        """Test automatic compilation error detection from message."""
        handler = ValidationErrorHandler()
        result = handler.format_error('runtime', 'javac compilation failed')
        assert "Compilation Error" in result
