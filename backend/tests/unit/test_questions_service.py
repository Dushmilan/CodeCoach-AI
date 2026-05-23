import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException

from app.models.schemas import Question, QuestionSummary, Difficulty, StarterCode, Example, TestCase


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
    return repo


def _qs(id_, title, difficulty, category):
    return QuestionSummary(id=id_, title=title, difficulty=difficulty, category=category)

@pytest.fixture
def sample_questions():
    return [
        _qs("two-sum", "Two Sum", Difficulty.EASY, "arrays"),
        _qs("rev-list", "Reverse List", Difficulty.MEDIUM, "linked-lists"),
    ]


class TestQuestionsServiceGetAll:
    @pytest.mark.asyncio
    async def test_get_all_questions(self, mock_repo, sample_questions):
        mock_repo.get_summaries = AsyncMock(return_value=sample_questions)
        from app.services.questions_service import QuestionsService
        service = QuestionsService(repository=mock_repo)

        result = await service.get_all_questions()

        assert len(result) == 2
        assert result[0].id == "two-sum"
        assert result[1].id == "rev-list"

    @pytest.mark.asyncio
    async def test_get_all_with_pagination(self, mock_repo, sample_questions):
        mock_repo.get_summaries = AsyncMock(return_value=sample_questions)
        from app.services.questions_service import QuestionsService
        service = QuestionsService(repository=mock_repo)

        page1 = await service.get_all_questions(page=1, per_page=1)
        assert len(page1) == 1
        assert page1[0].id == "two-sum"

        page2 = await service.get_all_questions(page=2, per_page=1)
        assert len(page2) == 1
        assert page2[0].id == "rev-list"

    @pytest.mark.asyncio
    async def test_get_all_with_difficulty_filter(self, mock_repo, sample_questions):
        easy_only = [q for q in sample_questions if q.difficulty == Difficulty.EASY]
        mock_repo.get_summaries = AsyncMock(return_value=easy_only)
        from app.services.questions_service import QuestionsService
        service = QuestionsService(repository=mock_repo)

        result = await service.get_all_questions(difficulty=Difficulty.EASY)
        assert len(result) == 1
        assert result[0].difficulty == Difficulty.EASY


class TestQuestionsServiceGetById:
    @pytest.mark.asyncio
    async def test_get_by_id_found(self, mock_repo, sample_questions):
        mock_repo.get_by_id = AsyncMock(return_value=sample_questions[0])
        from app.services.questions_service import QuestionsService
        service = QuestionsService(repository=mock_repo)

        result = await service.get_question_by_id("two-sum")
        assert result.id == "two-sum"
        assert result.title == "Two Sum"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, mock_repo):
        mock_repo.get_by_id = AsyncMock(return_value=None)
        from app.services.questions_service import QuestionsService
        service = QuestionsService(repository=mock_repo)

        with pytest.raises(HTTPException) as exc:
            await service.get_question_by_id("nonexistent")
        assert exc.value.status_code == 404


class TestQuestionsServiceSearch:
    @pytest.mark.asyncio
    async def test_search_questions(self, mock_repo, sample_questions):
        mock_repo.search_summaries = AsyncMock(return_value=[sample_questions[0]])
        from app.services.questions_service import QuestionsService
        service = QuestionsService(repository=mock_repo)

        result = await service.search_questions(query="two")
        assert len(result) == 1
        assert result[0].id == "two-sum"


class TestQuestionsServiceStats:
    @pytest.mark.asyncio
    async def test_get_categories(self, mock_repo):
        mock_repo.get_categories = AsyncMock(return_value=["arrays", "strings"])
        from app.services.questions_service import QuestionsService
        service = QuestionsService(repository=mock_repo)

        result = await service.get_categories()
        assert result == ["arrays", "strings"]

    @pytest.mark.asyncio
    async def test_get_company_tags(self, mock_repo):
        mock_repo.get_company_tags = AsyncMock(return_value=["Google", "Amazon"])
        from app.services.questions_service import QuestionsService
        service = QuestionsService(repository=mock_repo)

        result = await service.get_company_tags()
        assert "Google" in result

    @pytest.mark.asyncio
    async def test_get_total_count(self, mock_repo, sample_questions):
        mock_repo.get_all = AsyncMock(return_value=sample_questions)
        from app.services.questions_service import QuestionsService
        service = QuestionsService(repository=mock_repo)

        result = await service.get_total_count()
        assert result == 2

    @pytest.mark.asyncio
    async def test_get_difficulty_counts(self, mock_repo, sample_questions):
        mock_repo.get_all = AsyncMock(return_value=sample_questions)
        from app.services.questions_service import QuestionsService
        service = QuestionsService(repository=mock_repo)

        counts = await service.get_difficulty_counts()
        assert counts["easy"] == 1
        assert counts["medium"] == 1
        assert counts["hard"] == 0

    @pytest.mark.asyncio
    async def test_get_category_counts(self, mock_repo, sample_questions):
        mock_repo.get_all = AsyncMock(return_value=sample_questions)
        from app.services.questions_service import QuestionsService
        service = QuestionsService(repository=mock_repo)

        counts = await service.get_category_counts()
        assert counts["arrays"] == 1
        assert counts["linked-lists"] == 1


class TestQuestionsServiceByCategory:
    @pytest.mark.asyncio
    async def test_get_by_category(self, mock_repo, sample_questions):
        arrays = [q for q in sample_questions if q.category == "arrays"]
        mock_repo.get_summaries = AsyncMock(return_value=arrays)
        from app.services.questions_service import QuestionsService
        service = QuestionsService(repository=mock_repo)

        result = await service.get_questions_by_category("arrays")
        assert len(result) == 1
        assert result[0].category == "arrays"

    @pytest.mark.asyncio
    async def test_get_by_difficulty(self, mock_repo, sample_questions):
        easy = [q for q in sample_questions if q.difficulty == Difficulty.EASY]
        mock_repo.get_summaries = AsyncMock(return_value=easy)
        from app.services.questions_service import QuestionsService
        service = QuestionsService(repository=mock_repo)

        result = await service.get_questions_by_difficulty(Difficulty.EASY)
        assert len(result) == 1
