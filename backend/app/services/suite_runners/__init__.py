"""Suite runner builders — generate batch test harness code per language."""

from typing import Any, Dict, List

from app.services.suite_runners.python_runner import python_suite_runner
from app.services.suite_runners.javascript_runner import javascript_suite_runner
from app.services.suite_runners.java_runner import java_suite_runner


def build_suite_runner(language: str, user_code: str, test_cases: List[Dict[str, Any]]) -> str:
    if language == "python":
        return python_suite_runner(user_code, test_cases)
    elif language == "javascript":
        return javascript_suite_runner(user_code, test_cases)
    elif language == "java":
        return java_suite_runner(user_code, test_cases)
    return user_code
