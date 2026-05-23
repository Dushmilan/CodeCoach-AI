import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from app.models.schemas import Question, Difficulty, StarterCode, Example, TestCase
from app.models.question_validation_schemas import (
    ValidationUseCase, QuestionValidationResult,
    UseCaseValidationResult, ValidationSeverity, ValidationIssue,
)


@pytest.fixture
def valid_question():
    return Question(
        id="test-q", title="Test", difficulty=Difficulty.EASY,
        category="arrays", description="A test problem",
        starter=StarterCode(python="def f(): pass", javascript="function f(){}", java="class S{public static void f(){}}"),
        examples=[Example(input="1", output="1")],
        test_cases=[TestCase(input="1", expected_output="1")],
    )


@pytest.fixture
def mock_executor():
    executor = MagicMock()
    executor.execute = AsyncMock(return_value=MagicMock(stdout="1\n", exit_code=0))
    return executor


class TestQuestionValidatorService:
    @pytest.mark.asyncio
    async def test_validate_all_use_cases(self, valid_question, mock_executor):
        from app.services.question_validator import QuestionValidatorService
        service = QuestionValidatorService(executor=mock_executor)

        result = await service.validate_question(valid_question)

        assert isinstance(result, QuestionValidationResult)
        assert result.question_id == "test-q"

    @pytest.mark.asyncio
    async def test_validate_selected_use_cases(self, valid_question, mock_executor):
        from app.services.question_validator import QuestionValidatorService
        service = QuestionValidatorService(executor=mock_executor)

        result = await service.validate_question(
            valid_question,
            use_cases=[ValidationUseCase.STRUCTURE, ValidationUseCase.OUTPUT_FORMAT],
        )

        assert ValidationUseCase.STRUCTURE in result.results
        assert ValidationUseCase.OUTPUT_FORMAT in result.results
        assert ValidationUseCase.TEST_CASES not in result.results

    @pytest.mark.asyncio
    async def test_validate_batch(self, valid_question, mock_executor):
        from app.services.question_validator import QuestionValidatorService
        service = QuestionValidatorService(executor=mock_executor)

        results = await service.validate_batch([valid_question, valid_question])
        assert len(results) == 2
        assert all(r.question_id == "test-q" for r in results)

    @pytest.mark.asyncio
    async def test_quick_validate_runs_fast_use_cases(self, valid_question, mock_executor):
        from app.services.question_validator import QuestionValidatorService
        service = QuestionValidatorService(executor=mock_executor)

        result = await service.quick_validate(valid_question)

        assert ValidationUseCase.STRUCTURE in result.results
        assert ValidationUseCase.OUTPUT_FORMAT in result.results
        assert ValidationUseCase.SOLUTION not in result.results

    @pytest.mark.asyncio
    async def test_full_validate_runs_all(self, valid_question, mock_executor):
        from app.services.question_validator import QuestionValidatorService
        service = QuestionValidatorService(executor=mock_executor)

        result = await service.full_validate(valid_question)

        for uc in ValidationUseCase:
            assert uc in result.results

    def test_get_use_case_order(self, mock_executor):
        from app.services.question_validator import QuestionValidatorService
        service = QuestionValidatorService(executor=mock_executor)

        order = service.get_use_case_order()
        assert order[0] == ValidationUseCase.STRUCTURE
        assert order[-1] == ValidationUseCase.SOLUTION

    def test_get_validation_summary(self, valid_question, mock_executor):
        from app.services.question_validator import QuestionValidatorService
        import asyncio
        service = QuestionValidatorService(executor=mock_executor)

        result = asyncio.run(service.validate_question(valid_question))
        summary = service.get_validation_summary(result)

        assert summary["question_id"] == "test-q"
        assert "total_issues" in summary
        assert "use_cases_run" in summary
        assert "issues_by_use_case" in summary

    @pytest.mark.asyncio
    async def test_skipped_use_cases(self, valid_question, mock_executor):
        from app.services.question_validator import QuestionValidatorService
        from app.models.question_validation_schemas import QuestionValidationConfig
        config = QuestionValidationConfig(
            skip_use_cases=[ValidationUseCase.SOLUTION]
        )
        service = QuestionValidatorService(executor=mock_executor, config=config)

        result = await service.validate_question(valid_question)
        assert ValidationUseCase.SOLUTION not in result.results
