from typing import Optional

from .base import CodeWrapper
from .python_wrapper import PythonCodeWrapper
from .javascript_wrapper import JavaScriptCodeWrapper
from .java_wrapper import JavaCodeWrapper

WRAPPERS: dict = {
    "python": PythonCodeWrapper(),
    "javascript": JavaScriptCodeWrapper(),
    "java": JavaCodeWrapper(),
}


def get_wrapper(language: str) -> Optional[CodeWrapper]:
    return WRAPPERS.get(language)
