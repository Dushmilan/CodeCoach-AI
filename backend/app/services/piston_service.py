"""Piston code execution — single deep module.

Encapsulates code wrapping per language, execution via Piston API,
result formatting, and static validation.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException

from app.ports.code_executor import CodeExecutor, ExecutionResult, TestCaseResult
from app.adapters.code_wrappers import build_runner, get_wrapper
from app.adapters.execution_result_formatter import ExecutionResultFormatter
from app.services.static_code_validator import StaticCodeValidator, get_file_extension

logger = logging.getLogger(__name__)


# ── Piston Service ─────────────────────────────────────────────────────

class PistonService(CodeExecutor):
    """Executes code via Piston (Docker) sandbox. This is the deep module
    — wrapping, formatting, and validation are internal details."""

    # Piston API uses different language names than our internal names
    _PISTON_LANGUAGE_MAP = {
        "c": "gcc",
    }

    def __init__(self):
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
            raise HTTPException(status_code=400, detail=f"Unsupported language: {language}. Supported: {list(self.languages.keys())}")

        lang_config = self.languages[language]
        version_to_use = version or lang_config["version"]
        wrapper = get_wrapper(language)
        code_to_run = wrapper.wrap(code) if wrapper else code

        piston_language = self._PISTON_LANGUAGE_MAP.get(language, language)

        payload = {
            "language": piston_language,
            "version": version_to_use,
            "files": [{"name": f"main.{get_file_extension(language)}", "content": code_to_run}],
            "stdin": stdin, "args": [],
            "compile_timeout": 10000, "run_timeout": 3000,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/execute", json=payload, headers={"Content-Type": "application/json"})
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail=f"Piston API error: {response.text}")
                raw = response.json()
                processed = self.formatter.format(raw)
                return ExecutionResult(**processed)
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Code execution timeout")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error executing code: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Internal server error during code execution: {str(e)}")

    async def get_runtimes(self) -> List[dict]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/runtimes")
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail="Failed to fetch runtimes")
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching runtimes: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch available runtimes")

    # ── Batch Test Suite Execution ────────────────────────────────────────

    async def evaluate_suite(
        self,
        language: str,
        code: str,
        test_cases: List[dict],
    ) -> List[TestCaseResult]:
        """Execute all test cases in a single Piston request using a generated runner."""
        if language not in self.languages:
            raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")
        if not test_cases:
            return []

        runner_code = build_runner(language, code, test_cases)
        exec_result = await self.execute(
            language=language,
            code=runner_code,
            stdin="",
        )

        return self._parse_suite_output(exec_result, test_cases)

    def _parse_suite_output(
        self, exec_result: ExecutionResult, test_cases: List[dict]
    ) -> List[TestCaseResult]:
        """Parse the delimited JSON output from a suite runner."""
        stdout = exec_result.stdout or ""
        signal_info = f" (signal {exec_result.signal})" if exec_result.signal else ""
        # Extract JSON between delimiters
        marker = "@@SUITE_RESULT@@"
        start = stdout.find(marker)
        end = stdout.rfind(marker)
        if start == -1 or end == -1 or start == end:
            # Runner failed — mark all as failed and show stderr
            stderr = exec_result.stderr[:200]
            return [
                TestCaseResult(
                    index=i + 1,
                    passed=False,
                    input="" if tc.get("hidden") else tc["input"],
                    expected="" if tc.get("hidden") else tc["expected_output"],
                    actual=f"Execution Error{signal_info}: {stderr}",
                    hidden=tc.get("hidden", False),
                )
                for i, tc in enumerate(test_cases)
            ]

        json_str = stdout[start + len(marker) : end].strip()
        try:
            results = json.loads(json_str)
        except json.JSONDecodeError:
            err_msg = f"Invalid suite output{signal_info}" if signal_info else ""
            return [
                TestCaseResult(
                    index=i + 1,
                    passed=False,
                    input="" if tc.get("hidden") else tc["input"],
                    expected="" if tc.get("hidden") else tc["expected_output"],
                    actual=err_msg,
                    hidden=tc.get("hidden", False),
                )
                for i, tc in enumerate(test_cases)
            ]

        # Map runner results back to TestCaseResult objects
        result_map = {r["index"]: r for r in results}
        # If runner produced fewer results than test cases and signal was set,
        # the missing ones likely crashed — mark them as failed
        missing_signal = signal_info if len(results) < len(test_cases) else ""
        out: List[TestCaseResult] = []
        for i, tc in enumerate(test_cases):
            idx = i + 1
            r = result_map.get(idx, {})
            hidden = tc.get("hidden", False)
            actual = r.get("actual", "")
            if not r and missing_signal:
                actual = f"Crashed{missing_signal}"
            elif r:
                # Re-verify: compare normalized actual vs expected to catch runner bugs
                runner_passed = r.get("passed", False)
                re_verified = self._normalize(actual) == self._normalize(tc.get("expected_output", ""))
                if runner_passed != re_verified:
                    logger.warning(
                        "Runner mismatch for test case %d: runner=%s re-verify=%s "
                        "actual=%r expected=%r",
                        idx, runner_passed, re_verified, actual[:100], tc.get("expected_output", "")[:100],
                    )
            out.append(
                TestCaseResult(
                    index=idx,
                    passed=r.get("passed", False) if r else False,
                    input="" if hidden else tc["input"],
                    expected="" if hidden else tc["expected_output"],
                    actual="" if hidden else actual,
                    hidden=hidden,
                )
            )
        return out

    @staticmethod
    def _normalize(s: str) -> str:
        import re
        return re.sub(r'\s+', '', s.strip())

    def validate_code(self, language: str, code: str) -> dict:
        return self.validator.validate(language, code)
