import pytest
from app.adapters.execution_result_formatter import ExecutionResultFormatter


@pytest.fixture
def formatter():
    return ExecutionResultFormatter()


class TestFormat:
    def test_complete_response(self, formatter):
        result = formatter.format(
            {
                "run": {
                    "stdout": "hello",
                    "stderr": "",
                    "code": 0,
                    "signal": None,
                    "wall_time": 0.123,
                    "memory": 4096,
                },
                "language": "python",
                "version": "3.11.0",
            }
        )
        assert result["stdout"] == "hello"
        assert result["stderr"] == ""
        assert result["exit_code"] == 0
        assert result["signal"] is None
        assert result["execution_time"] == 0.123
        assert result["memory_usage"] == 4096
        assert result["language"] == "python"
        assert result["version"] == "3.11.0"

    def test_missing_fields_use_defaults(self, formatter):
        result = formatter.format({})
        assert result["stdout"] == ""
        assert result["stderr"] == ""
        assert result["exit_code"] == 1
        assert result["signal"] is None
        assert result["execution_time"] is None
        assert result["memory_usage"] is None
        assert result["language"] == ""
        assert result["version"] == ""

    def test_missing_run_object(self, formatter):
        result = formatter.format({"language": "java"})
        assert result["stdout"] == ""
        assert result["exit_code"] == 1
        assert result["language"] == "java"

    def test_null_wall_time_falls_back_to_time(self, formatter):
        result = formatter.format(
            {
                "run": {
                    "stdout": "",
                    "stderr": "",
                    "code": 0,
                    "time": 0.456,
                }
            }
        )
        assert result["execution_time"] == 0.456

    def test_wall_time_takes_precedence_over_time(self, formatter):
        result = formatter.format(
            {
                "run": {
                    "stdout": "",
                    "stderr": "",
                    "code": 0,
                    "wall_time": 0.123,
                    "time": 0.456,
                }
            }
        )
        assert result["execution_time"] == 0.123

    def test_filters_warning_lines_from_stderr(self, formatter):
        result = formatter.format(
            {
                "run": {
                    "stdout": "",
                    "stderr": "main.py:1: Warning: something\nActual error\nmain.py:3: Deprecated: old\nNote: info",
                    "code": 1,
                }
            }
        )
        assert "Warning:" not in result["stderr"]
        assert "Actual error" in result["stderr"]
        assert "Deprecated" not in result["stderr"]
        assert "Note:" not in result["stderr"]

    def test_filters_hash_warning_lines(self, formatter):
        result = formatter.format(
            {
                "run": {
                    "stdout": "",
                    "stderr": "#warning some compiler note\ndata here",
                    "code": 1,
                }
            }
        )
        assert "data here" in result["stderr"]
        assert "#warning" not in result["stderr"]

    def test_stdout_truncated_in_log_only(self, formatter):
        long_stdout = "a" * 1000
        result = formatter.format(
            {
                "run": {
                    "stdout": long_stdout,
                    "stderr": "",
                    "code": 0,
                }
            }
        )
        assert result["stdout"] == long_stdout

    def test_both_time_and_wall_time_none(self, formatter):
        result = formatter.format(
            {
                "run": {
                    "stdout": "",
                    "stderr": "",
                    "code": 0,
                }
            }
        )
        assert result["execution_time"] is None

    def test_signal_field_preserved(self, formatter):
        result = formatter.format(
            {
                "run": {
                    "stdout": "",
                    "stderr": "",
                    "code": -6,
                    "signal": "6",
                },
                "language": "python",
            }
        )
        assert result["signal"] == "6"

    def test_run_key_missing_returns_defaults(self, formatter):
        result = formatter.format({"language": "python"})
        assert result["stdout"] == ""
        assert result["exit_code"] == 1
        assert result["signal"] is None

    def test_stdout_not_string_logged_gracefully(self, formatter):
        result = formatter.format(
            {
                "run": {
                    "stdout": 12345,  # not a string
                    "stderr": "",
                    "code": 0,
                }
            }
        )
        assert isinstance(result["stdout"], str) or result["stdout"] == 12345
