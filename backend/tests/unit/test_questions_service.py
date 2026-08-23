"""Tests for QuestionBank."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException

from app.models.schemas import (
    Question,
    QuestionSummary,
    Difficulty,
    StarterCode,
    Example,
    TestCase,
)
from app.services.question_bank import QuestionBank, QuestionFilters


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.get_all = AsyncMock(return_value=[])
    repo.get_by_id = AsyncMock(return_value=None)
    repo.search = AsyncMock(return_value=[])
    repo.get_categories = AsyncMock(return_value=[])
    repo.get_company_tags = AsyncMock(return_value=[])
    repo.add = AsyncMock()
    repo.get_summaries = AsyncMock(return_value=[])
    repo.search_summaries = AsyncMock(return_value=[])
    repo.save_validation_status = AsyncMock()
    repo.count = AsyncMock(return_value=0)
    repo.count_by_difficulty = AsyncMock(
        return_value={"easy": 0, "medium": 0, "hard": 0}
    )
    return repo


def _qs(id_, title, difficulty, category):
    return QuestionSummary(
        id=id_, title=title, difficulty=difficulty, category=category
    )


@pytest.fixture
def sample_questions():
    return [
        _qs("two-sum", "Two Sum", Difficulty.EASY, "arrays"),
        _qs("rev-list", "Reverse List", Difficulty.MEDIUM, "linked-lists"),
    ]


def make_bank(repo):
    return QuestionBank(repository=repo)


class TestQuestionBankQuery:
    @pytest.mark.asyncio
    async def test_query_all(self, mock_repo, sample_questions):
        mock_repo.get_summaries = AsyncMock(return_value=sample_questions)
        bank = make_bank(mock_repo)

        result = await bank.query(QuestionFilters())

        assert result.total == 2
        assert len(result.items) == 2
        assert result.items[0].id == "two-sum"

    @pytest.mark.asyncio
    async def test_query_with_pagination(self, mock_repo, sample_questions):
        mock_repo.get_summaries = AsyncMock(return_value=sample_questions)
        bank = make_bank(mock_repo)

        page1 = await bank.query(QuestionFilters(page=1, per_page=1))
        assert len(page1.items) == 1
        assert page1.items[0].id == "two-sum"

        page2 = await bank.query(QuestionFilters(page=2, per_page=1))
        assert len(page2.items) == 1
        assert page2.items[0].id == "rev-list"

    @pytest.mark.asyncio
    async def test_query_with_difficulty_filter(self, mock_repo, sample_questions):
        easy = [q for q in sample_questions if q.difficulty == Difficulty.EASY]
        mock_repo.get_summaries = AsyncMock(return_value=easy)
        bank = make_bank(mock_repo)

        result = await bank.query(QuestionFilters(difficulty=Difficulty.EASY))
        assert result.total == 1
        assert result.items[0].difficulty == Difficulty.EASY

    @pytest.mark.asyncio
    async def test_query_with_search(self, mock_repo, sample_questions):
        mock_repo.search_summaries = AsyncMock(return_value=[sample_questions[0]])
        bank = make_bank(mock_repo)

        result = await bank.query(QuestionFilters(query="two"))
        assert result.total == 1
        assert result.items[0].id == "two-sum"

    @pytest.mark.asyncio
    async def test_query_with_category_filter(self, mock_repo, sample_questions):
        arrays = [q for q in sample_questions if q.category == "arrays"]
        mock_repo.get_summaries = AsyncMock(return_value=arrays)
        bank = make_bank(mock_repo)

        result = await bank.query(QuestionFilters(category="arrays"))
        assert result.total == 1


class TestQuestionBankGet:
    @pytest.mark.asyncio
    async def test_get_by_id_found(self, mock_repo, sample_questions):
        mock_repo.get_by_id = AsyncMock(return_value=sample_questions[0])
        bank = make_bank(mock_repo)

        result = await bank.get("two-sum")
        assert result.id == "two-sum"
        assert result.title == "Two Sum"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, mock_repo):
        mock_repo.get_by_id = AsyncMock(return_value=None)
        bank = make_bank(mock_repo)

        with pytest.raises(HTTPException) as exc:
            await bank.get("nonexistent")
        assert exc.value.status_code == 404


class TestQuestionBankStats:
    @pytest.mark.asyncio
    async def test_categories(self, mock_repo):
        mock_repo.get_categories = AsyncMock(return_value=["arrays", "strings"])
        mock_repo.get_all = AsyncMock(return_value=[])
        bank = make_bank(mock_repo)

        stats = await bank.stats()
        assert "arrays" in stats.categories

    @pytest.mark.asyncio
    async def test_company_tags(self, mock_repo):
        mock_repo.get_company_tags = AsyncMock(return_value=["Google", "Amazon"])
        mock_repo.get_all = AsyncMock(return_value=[])
        bank = make_bank(mock_repo)

        stats = await bank.stats()
        assert "Google" in stats.companies

    @pytest.mark.asyncio
    async def test_total_count(self, mock_repo, sample_questions):
        mock_repo.get_all = AsyncMock(return_value=sample_questions)
        mock_repo.count = AsyncMock(return_value=2)
        bank = make_bank(mock_repo)

        stats = await bank.stats()
        assert stats.total == 2

    @pytest.mark.asyncio
    async def test_difficulty_counts(self, mock_repo, sample_questions):
        # M-04: counts come from the SQL GROUP BY aggregate, not get_all().
        mock_repo.count_by_difficulty = AsyncMock(
            return_value={"easy": 1, "medium": 1, "hard": 0}
        )
        bank = make_bank(mock_repo)

        stats = await bank.stats()
        assert stats.difficulty_counts["easy"] == 1
        assert stats.difficulty_counts["medium"] == 1
        assert stats.difficulty_counts["hard"] == 0
        mock_repo.count_by_difficulty.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_category_counts(self, mock_repo, sample_questions):
        mock_repo.get_all = AsyncMock(return_value=sample_questions)
        bank = make_bank(mock_repo)

        stats = await bank.stats()
        assert stats.category_counts["arrays"] == 1
        assert stats.category_counts["linked-lists"] == 1

    @pytest.mark.asyncio
    async def test_search_questions(self, mock_repo, sample_questions):
        mock_repo.search_summaries = AsyncMock(return_value=[sample_questions[0]])
        bank = make_bank(mock_repo)

        result = await bank.query(QuestionFilters(query="two"))
        assert result.total == 1
        assert result.items[0].id == "two-sum"

    @pytest.mark.asyncio
    async def test_get_by_category(self, mock_repo, sample_questions):
        arrays = [q for q in sample_questions if q.category == "arrays"]
        mock_repo.get_summaries = AsyncMock(return_value=arrays)
        bank = make_bank(mock_repo)

        result = await bank.query(QuestionFilters(category="arrays"))
        assert result.total == 1
        assert result.items[0].category == "arrays"

    @pytest.mark.asyncio
    async def test_get_by_difficulty(self, mock_repo, sample_questions):
        easy = [q for q in sample_questions if q.difficulty == Difficulty.EASY]
        mock_repo.get_summaries = AsyncMock(return_value=easy)
        bank = make_bank(mock_repo)

        result = await bank.query(QuestionFilters(difficulty=Difficulty.EASY))
        assert result.total == 1
        assert result.items[0].difficulty == Difficulty.EASY


class TestQuestionBankAdd:
    @pytest.mark.asyncio
    async def test_add_without_validation(self, mock_repo):
        mock_repo.add = AsyncMock()
        bank = make_bank(mock_repo)

        question = Question(
            id="test-q",
            title="Test",
            difficulty=Difficulty.EASY,
            category="arrays",
            description="desc",
            starter=StarterCode(python="def f(): pass"),
            examples=[Example(input="1", output="1")],
            test_cases=[TestCase(input="1", expected_output="1")],
        )
        result = await bank.add(question, validate=False)
        assert result.is_validated is False
