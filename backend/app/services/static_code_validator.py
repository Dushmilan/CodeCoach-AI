"""Static code validation and file extension lookup."""


class StaticCodeValidator:
    def validate(self, language: str, code: str) -> dict:
        warnings = []
        if language == "python":
            if "input(" in code and "import sys" not in code:
                warnings.append("Consider using sys.stdin for better compatibility")
            if "print(" in code and not code.strip().endswith(")"):
                warnings.append("Check for unclosed parentheses")
        elif language == "javascript":
            if "console.log(" in code and not code.strip().endswith(")"):
                warnings.append("Check for unclosed parentheses")
        return {"valid": True, "warnings": warnings, "errors": []}


_FILE_EXTENSIONS = {
    "python": "py",
    "javascript": "js",
    "java": "java",
    "cpp": "cpp",
    "c": "c",
    "go": "go",
    "rust": "rs",
    "typescript": "ts",
}


def get_file_extension(language: str) -> str:
    return _FILE_EXTENSIONS.get(language, "txt")
