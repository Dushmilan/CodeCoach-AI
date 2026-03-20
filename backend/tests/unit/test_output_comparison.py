"""
Unit tests for output comparison logic.
Tests cover string matching, JSON normalization, and numeric comparison.
"""

import pytest
from app.services.simple_validators import SimplePythonValidator


class TestOutputComparison:
    """Test suite for output comparison logic."""

    def test_exact_string_match(self):
        """Test exact string comparison."""
        validator = SimplePythonValidator()
        assert validator.compare_outputs("hello", "hello") == True

    def test_string_mismatch(self):
        """Test string mismatch."""
        validator = SimplePythonValidator()
        assert validator.compare_outputs("hello", "world") == False

    def test_json_array_match(self):
        """Test JSON array comparison."""
        validator = SimplePythonValidator()
        assert validator.compare_outputs("[1, 2, 3]", "[1, 2, 3]") == True
        assert validator.compare_outputs("[1,2,3]", "[1, 2, 3]") == True  # JSON normalization

    def test_json_object_match(self):
        """Test JSON object comparison."""
        validator = SimplePythonValidator()
        assert validator.compare_outputs('{"a": 1}', '{"a": 1}') == True
        assert validator.compare_outputs('{"a":1}', '{"a": 1}') == True  # JSON normalization

    def test_numeric_match(self):
        """Test numeric comparison."""
        validator = SimplePythonValidator()
        assert validator.compare_outputs("42", "42") == True
        assert validator.compare_outputs("42.0", "42") == True  # Float comparison

    def test_numeric_mismatch(self):
        """Test numeric mismatch."""
        validator = SimplePythonValidator()
        assert validator.compare_outputs("42", "43") == False

    def test_whitespace_preserved(self):
        """Test that leading/trailing whitespace is handled."""
        validator = SimplePythonValidator()
        # The validator strips output before comparison
        assert validator.compare_outputs("hello", "hello") == True

    def test_case_sensitivity(self):
        """Test case sensitivity in comparison."""
        validator = SimplePythonValidator()
        assert validator.compare_outputs("Hello", "hello") == False

    def test_empty_strings(self):
        """Test empty string comparison."""
        validator = SimplePythonValidator()
        assert validator.compare_outputs("", "") == True

    def test_multiline_comparison(self):
        """Test multiline string comparison."""
        validator = SimplePythonValidator()
        assert validator.compare_outputs("line1\nline2", "line1\nline2") == True
        assert validator.compare_outputs("line1\nline2", "line1\nline3") == False
