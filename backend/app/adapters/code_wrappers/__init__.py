from typing import Any, Dict, List, Optional
from .base import CodeWrapper
from .python_wrapper import PythonCodeWrapper
from .javascript_wrapper import JavaScriptCodeWrapper
from .java_wrapper import JavaCodeWrapper
from .r_wrapper import RCodeWrapper
from .bash_wrapper import BashCodeWrapper

_WRAPPERS: Dict[str, CodeWrapper] = {
    "python": PythonCodeWrapper(),
    "javascript": JavaScriptCodeWrapper(),
    "java": JavaCodeWrapper(),
    "r": RCodeWrapper(),
    "bash": BashCodeWrapper(),
}


def get_wrapper(language: str) -> Optional[CodeWrapper]:
    return _WRAPPERS.get(language)


def build_runner(language: str, code: str, test_cases: List[Dict[str, Any]]) -> str:
    wrapper = get_wrapper(language)
    if wrapper is None:
        return code
    return wrapper.wrap_with_tests(code, test_cases)
