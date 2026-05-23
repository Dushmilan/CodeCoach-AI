import httpx
import logging
from typing import List, Optional
from fastapi import HTTPException

from app.ports.code_executor import CodeExecutor, ExecutionResult
from app.adapters.code_wrappers import get_wrapper
from app.services.execution_result_formatter import ExecutionResultFormatter
from app.services.static_code_validator import StaticCodeValidator

logger = logging.getLogger(__name__)


class PistonService(CodeExecutor):
    """Service for executing code via Piston API."""

    def __init__(self):
        import os

        self.base_url = os.environ.get("PISTON_API_URL", "http://localhost:2000/api/v2")
        self.timeout = 30.0
        self.formatter = ExecutionResultFormatter()
        self.validator = StaticCodeValidator()

        self.languages = {
            "python": {"version": "3.10.0", "aliases": ["py", "python3"]},
            "javascript": {"version": "18.15.0", "aliases": ["js", "node"]},
            "java": {"version": "15.0.2", "aliases": ["java"]},
            "cpp": {"version": "10.2.0", "aliases": ["c++", "cpp"]},
            "c": {"version": "10.2.0", "aliases": ["c"]},
            "go": {"version": "1.16.2", "aliases": ["golang"]},
            "rust": {"version": "1.68.2", "aliases": ["rs", "rust"]},
            "typescript": {"version": "5.0.2", "aliases": ["ts", "typescript"]},
        }

    async def execute(
        self, language: str, code: str, stdin: str = "", version: Optional[str] = None
    ) -> ExecutionResult:
        if language not in self.languages:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language: {language}. Supported: {list(self.languages.keys())}",
            )

        lang_config = self.languages[language]
        version_to_use = version or lang_config["version"]

        wrapper = get_wrapper(language)
        code_to_run = wrapper.wrap(code) if wrapper else code

        payload = {
            "language": language,
            "version": version_to_use,
            "files": [
                {"name": f"main.{self._get_file_extension(language)}", "content": code_to_run}
            ],
            "stdin": stdin,
            "args": [],
            "compile_timeout": 10000,
            "run_timeout": 3000,
            "compile_memory_limit": -1,
            "run_memory_limit": -1,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/execute",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code != 200:
                    error_text = response.text
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Piston API error: {error_text}",
                    )

                raw = response.json()
                processed = self.formatter.format(raw)
                return ExecutionResult(**processed)

        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Code execution timeout")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error executing code: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error during code execution: {str(e)}",
            )

    async def get_runtimes(self) -> List[dict]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/runtimes")

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail="Failed to fetch runtimes",
                    )

                return response.json()

        except Exception as e:
            logger.error(f"Error fetching runtimes: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to fetch available runtimes"
            )

    def validate_code(self, language: str, code: str) -> dict:
        return self.validator.validate(language, code)

    def _get_file_extension(self, language: str) -> str:
        extensions = {
            "python": "py",
            "javascript": "js",
            "java": "java",
            "cpp": "cpp",
            "c": "c",
            "go": "go",
            "rust": "rs",
            "typescript": "ts",
        }
        return extensions.get(language, "txt")
