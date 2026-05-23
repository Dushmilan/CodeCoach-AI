from fastapi import APIRouter, Depends, HTTPException
from functools import lru_cache

from app.models.schemas import SubmitRequest, SubmitResponse, SubmitResult
from app.ports.code_executor import CodeExecutor, ExecutionResult
from app.ports.question_repository import QuestionRepository
from app.repositories.file_question_repository import FileQuestionRepository
from app.services.piston_service import PistonService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@lru_cache()
def get_repository() -> QuestionRepository:
    return FileQuestionRepository("questions/sample_questions.json")


@lru_cache()
def get_executor() -> CodeExecutor:
    return PistonService()


@router.post("/", response_model=SubmitResponse)
async def submit_code(
    request: SubmitRequest,
    repository: QuestionRepository = Depends(get_repository),
    executor: CodeExecutor = Depends(get_executor),
):
    question = await repository.get_by_id(request.question_id)
    if not question:
        raise HTTPException(
            status_code=404, detail=f"Question not found: {request.question_id}"
        )

    language_key = request.language.value
    test_cases = question.test_cases
    results = []

    for i, tc in enumerate(test_cases):
        index = i + 1

        try:
            exec_result: ExecutionResult = await executor.execute(
                language=language_key,
                code=request.code,
                stdin=tc.input,
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Submit execution error for case {index}: {e}")
            result = SubmitResult(
                index=index,
                passed=False,
                input="" if tc.hidden else tc.input,
                expected="" if tc.hidden else tc.expected_output,
                actual="",
                hidden=tc.hidden,
            )
            results.append(result)
            continue

        actual_output = exec_result.stdout.rstrip("\n")
        expected_output = tc.expected_output.rstrip("\n")
        passed = actual_output == expected_output and exec_result.exit_code == 0

        result = SubmitResult(
            index=index,
            passed=passed,
            input="" if tc.hidden else tc.input,
            expected="" if tc.hidden else tc.expected_output,
            actual="" if tc.hidden else actual_output,
            hidden=tc.hidden,
        )
        results.append(result)

    passed_count = sum(1 for r in results if r.passed)
    return SubmitResponse(
        passed=passed_count == len(results),
        total=len(results),
        passed_count=passed_count,
        results=results,
    )
