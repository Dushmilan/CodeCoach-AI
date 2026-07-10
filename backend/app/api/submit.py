from fastapi import APIRouter, Depends, HTTPException, Request
from app.models.schemas import SubmitRequest, SubmitResponse, SubmitResult
from app.ports.code_executor import CodeExecutor
from app.ports.question_repository import QuestionRepository
from app.api.auth import get_current_user
from app.api.dependencies import get_executor, get_question_repo
from app.middleware.rate_limit import limiter, RUN_RATE_LIMIT
import logging

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("/", response_model=SubmitResponse)
@limiter.limit(RUN_RATE_LIMIT)
async def submit_code(
    request: Request,
    submit_request: SubmitRequest,
    repository: QuestionRepository = Depends(get_question_repo),
    executor: CodeExecutor = Depends(get_executor),
):
    question = await repository.get_by_id(submit_request.question_id)
    if not question:
        raise HTTPException(
            status_code=404, detail=f"Question not found: {submit_request.question_id}"
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
            language=submit_request.language.value,
            code=submit_request.code,
            test_cases=test_cases,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Submit evaluation error: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

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
