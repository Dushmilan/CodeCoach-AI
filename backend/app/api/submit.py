from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import SubmitRequest, SubmitResponse, SubmitResult
from app.ports.code_executor import CodeExecutor
from app.ports.question_repository import QuestionRepository
from app.repositories.file_question_repository import FileQuestionRepository
from app.services.piston_service import PistonService
from app.api.auth import get_current_user
from app.models.auth_schemas import UserResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_user)])


def get_repository() -> QuestionRepository:
    return FileQuestionRepository("questions/sample_questions.json")


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

    test_cases = [
        {
            "input": tc.input,
            "expected_output": tc.expected_output,
            "hidden": tc.hidden,
        }
        for tc in question.test_cases
    ]

    try:
        results = await executor.evaluate_suite(
            language=request.language.value,
            code=request.code,
            test_cases=test_cases,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Submit evaluation error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Evaluation failed: {str(e)}"
        )

    passed_count = sum(1 for r in results if r.passed)
    return SubmitResponse(
        passed=passed_count == len(results) if results else False,
        total=len(results),
        passed_count=passed_count,
        results=[
            SubmitResult(
                index=r.index,
                passed=r.passed,
                input=r.input,
                expected=r.expected,
                actual=r.actual,
                hidden=r.hidden,
            )
            for r in results
        ],
    )
