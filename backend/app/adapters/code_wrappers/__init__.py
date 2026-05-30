from typing import Dict, Optional
from .base import CodeWrapper
from .python_wrapper import PythonCodeWrapper
from .javascript_wrapper import JavaScriptCodeWrapper
from .java_wrapper import JavaCodeWrapper

_WRAPPERS: Dict[str, CodeWrapper] = {
    "python": PythonCodeWrapper(),
    "javascript": JavaScriptCodeWrapper(),
    "java": JavaCodeWrapper(),
}


def get_wrapper(language: str) -> Optional[CodeWrapper]:
    return _WRAPPERS.get(language)
