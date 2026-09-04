"""Stateful execution adapter — sent -> executed/failed persistence.

Wraps a CodeExecutor (e.g. PistonService) with durable intent rows via
ExecutionJobRepository. Persistence is best-effort: DB failures are logged
and never break execution (degrade open).
"""

import hashlib
import logging
import uuid
from typing import Any, List, Optional

from app.ports.code_executor import CodeExecutor, ExecutionResult, TestCaseResult
from app.ports.execution_job_repository import ExecutionJobRepository

logger = logging.getLogger(__name__)


def hash_content(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update((p or "").encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()[:64]


class ExecutionAdapter(CodeExecutor):
    """CodeExecutor with Supabase-backed state transitions."""

    def __init__(
        self,
        inner: CodeExecutor,
        repo: Optional[ExecutionJobRepository] = None,
        user_id: Optional[str] = None,
        question_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ):
        self.inner = inner
        self.repo = repo
        self.user_id = user_id
        self.question_id = question_id
        self.request_id = request_id or uuid.uuid4().hex

    async def _create_job(
        self, language: str, code: str, extra: dict[str, Any]
    ) -> Optional[Any]:
        if self.repo is None or not self.user_id:
            return None
        try:
            return await self.repo.create_sent(
                user_id=self.user_id,
                question_id=self.question_id,
                language=language,
                code_hash=hash_content(code),
                idempotency_key=uuid.uuid4().hex,
                request_payload={"language": language, **extra},
                request_id=self.request_id,
            )
        except Exception:  # noqa: BLE001
            logger.warning("Failed to persist execution sent state", exc_info=True)
            return None

    async def execute(
        self, language: str, code: str, stdin: str = "", version: Optional[str] = None
    ) -> ExecutionResult:
        job = await self._create_job(language, code, {"stdin": stdin})
        try:
            result = await self.inner.execute(
                language=language, code=code, stdin=stdin, version=version
            )
        except Exception as exc:  # noqa: BLE001
            if job is not None and self.repo is not None:
                try:
                    await self.repo.mark_failed(
                        job.id,
                        error_code=type(exc).__name__[:50],
                        error_message=str(exc)[:2000],
                    )
                except Exception:  # noqa: BLE001
                    logger.warning(
                        "Failed to persist execution failed state", exc_info=True
                    )
            raise
        if job is not None and self.repo is not None:
            try:
                await self.repo.mark_executed(
                    job.id,
                    response_payload={
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "exit_code": result.exit_code,
                    },
                )
            except Exception:  # noqa: BLE001
                logger.warning(
                    "Failed to persist execution completed state", exc_info=True
                )
        return result

    async def evaluate_suite(
        self, language: str, code: str, test_cases: List[dict]
    ) -> List[TestCaseResult]:
        job = await self._create_job(
            language, code, {"test_cases_count": len(test_cases)}
        )
        try:
            results = await self.inner.evaluate_suite(
                language=language, code=code, test_cases=test_cases
            )
        except Exception as exc:  # noqa: BLE001
            if job is not None and self.repo is not None:
                try:
                    await self.repo.mark_failed(
                        job.id,
                        error_code=type(exc).__name__[:50],
                        error_message=str(exc)[:2000],
                    )
                except Exception:  # noqa: BLE001
                    logger.warning(
                        "Failed to persist execution suite failed state",
                        exc_info=True,
                    )
            raise
        if job is not None and self.repo is not None:
            try:
                await self.repo.mark_executed(
                    job.id,
                    test_results=[
                        {
                            "index": r.index,
                            "passed": r.passed,
                            "hidden": r.hidden,
                        }
                        for r in results
                    ],
                )
            except Exception:  # noqa: BLE001
                logger.warning(
                    "Failed to persist execution suite completed state",
                    exc_info=True,
                )
        return results

    async def get_runtimes(self) -> List[dict]:
        return await self.inner.get_runtimes()

    def validate_code(self, language: str, code: str) -> dict:
        return self.inner.validate_code(language=language, code=code)
