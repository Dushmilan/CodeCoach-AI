"""Tests for issue #5 refactors: ValidationUseCase.description property and
single-add consolidation in QuestionBank.add."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.question_validation_schemas import (
    QuestionValidationResult,
    ValidationUseCase,
)
from app.models.schemas import Question
from app.services.question_bank import QuestionBank


def test_validation_usecase_has_description():
    assert ValidationUseCase.SOLUTION.description.startswith(
        "Validates that the reference solution"
    )
    assert ValidationUseCase.STRUCTURE.description.startswith(
        "Validates question structure"
    )
    for uc in ValidationUseCase:
        assert isinstance(uc.description, str) and uc.description


class FakeRepo:
    def __init__(self):
        self.add = AsyncMock()
        self.save_validation_status = AsyncMock()
        self.count = AsyncMock(return_value=0)
        self.get_all = AsyncMock(return_value=[])


def _make_question(qid="q1"):
    q = MagicMock(spec=Question)
    q.id = qid
    return q


@pytest.mark.asyncio
async def test_add_persists_once_when_validator_missing():
    repo = FakeRepo()
    bank = QuestionBank(repository=repo)
    status = await bank.add(_make_question(), validate=False)
    repo.add.assert_awaited_once()
    assert status.is_validated is False
    assert status.validation_passed is False


@pytest.mark.asyncio
async def test_add_persists_once_when_validation_fails():
    repo = FakeRepo()
    validator = MagicMock()
    validator.validate_question = AsyncMock(
        return_value=QuestionValidationResult(question_id="q1", valid=False)
    )
    bank = QuestionBank(repository=repo, validator=validator)
    status = await bank.add(_make_question(), validate=True)
    repo.add.assert_awaited_once()
    assert status.is_validated is True
    assert status.validation_passed is False


@pytest.mark.asyncio
async def test_add_persists_once_and_invalidates_cache_when_valid():
    repo = FakeRepo()
    validator = MagicMock()
    validator.validate_question = AsyncMock(
        return_value=QuestionValidationResult(question_id="q1", valid=True)
    )
    cache = MagicMock()
    cache.delete = AsyncMock()
    bank = QuestionBank(repository=repo, validator=validator, cache=cache)
    status = await bank.add(_make_question(), validate=True)
    repo.add.assert_awaited_once()
    cache.delete.assert_awaited_once()
    assert status.is_validated is True
    assert status.validation_passed is True
