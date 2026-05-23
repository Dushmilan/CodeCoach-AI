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
