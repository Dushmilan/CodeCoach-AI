import pytest
import json
import tempfile
import os

from app.models.schemas import Difficulty


class TestFileQuestionRepository:
    @pytest.fixture
    def sample_json(self):
        questions = [
            {
                "id": "test-one",
                "title": "Test One",
                "difficulty": "easy",
                "category": "arrays",
                "company_tags": ["Acme"],
                "description": "First test question.",
                "starter": {
                    "python": "def one():\n    pass",
                    "javascript": "function one() {}",
                    "java": "class One {}",
                },
                "examples": [{"input": "1", "output": "1", "explanation": "Basic"}],
                "test_cases": [
                    {"input": "1", "expected_output": "1", "description": "TC1"}
                ],
            },
            {
                "id": "test-two",
                "title": "Test Two Sum",
                "difficulty": "medium",
                "category": "arrays",
                "company_tags": ["Acme", "Beta"],
                "description": "Second test question about summing.",
                "starter": {
                    "python": "def two():\n    pass",
                    "javascript": "function two() {}",
                    "java": "class Two {}",
                },
                "examples": [{"input": "2", "output": "2", "explanation": "Basic"}],
                "test_cases": [
                    {"input": "2", "expected_output": "2", "description": "TC1"}
                ],
            },
            {
                "id": "test-three",
                "title": "Reverse String",
                "difficulty": "hard",
                "category": "strings",
                "company_tags": ["Gamma"],
                "description": "Reverse a string in place.",
                "starter": {
                    "python": "def reverse(s):\n    pass",
                    "javascript": "function reverse(s) {}",
                    "java": "class Reverse {}",
                },
                "examples": [{"input": "abc", "output": "cba", "explanation": "Basic"}],
                "test_cases": [
                    {"input": "abc", "expected_output": "cba", "description": "TC1"}
                ],
            },
        ]
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(questions, f)
        yield path
        os.unlink(path)

    @pytest.mark.asyncio
    async def test_get_all_returns_all_questions(self, sample_json):
        from app.repositories.file_question_repository import FileQuestionRepository

        repo = FileQuestionRepository(sample_json)
        questions = await repo.get_all()

        assert len(questions) == 3
        assert questions[0].id == "test-one"
        assert questions[1].id == "test-two"

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, sample_json):
        from app.repositories.file_question_repository import FileQuestionRepository

        repo = FileQuestionRepository(sample_json)
        q = await repo.get_by_id("test-two")

        assert q is not None
        assert q.title == "Test Two Sum"
        assert q.difficulty == Difficulty.MEDIUM

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, sample_json):
        from app.repositories.file_question_repository import FileQuestionRepository

        repo = FileQuestionRepository(sample_json)
        q = await repo.get_by_id("nonexistent")

        assert q is None

    @pytest.mark.asyncio
    async def test_search_by_title(self, sample_json):
        from app.repositories.file_question_repository import FileQuestionRepository

        repo = FileQuestionRepository(sample_json)
        results = await repo.search("Sum")

        assert len(results) == 1
        assert results[0].id == "test-two"

    @pytest.mark.asyncio
    async def test_search_by_description(self, sample_json):
        from app.repositories.file_question_repository import FileQuestionRepository

        repo = FileQuestionRepository(sample_json)
        results = await repo.search("summing")

        assert len(results) == 1
        assert results[0].id == "test-two"

    @pytest.mark.asyncio
    async def test_get_categories(self, sample_json):
        from app.repositories.file_question_repository import FileQuestionRepository

        repo = FileQuestionRepository(sample_json)
        cats = await repo.get_categories()

        assert "arrays" in cats
        assert "strings" in cats
        assert len(cats) == 2

    @pytest.mark.asyncio
    async def test_get_company_tags(self, sample_json):
        from app.repositories.file_question_repository import FileQuestionRepository

        repo = FileQuestionRepository(sample_json)
        tags = await repo.get_company_tags()

        assert "Acme" in tags
        assert "Beta" in tags
        assert "Gamma" in tags
        assert len(tags) == 3

    @pytest.mark.asyncio
    async def test_get_all_filters_by_difficulty(self, sample_json):
        from app.repositories.file_question_repository import FileQuestionRepository

        repo = FileQuestionRepository(sample_json)
        results = await repo.get_all(difficulty=Difficulty.EASY)

        assert len(results) == 1
        assert results[0].id == "test-one"

    @pytest.mark.asyncio
    async def test_get_all_filters_by_category(self, sample_json):
        from app.repositories.file_question_repository import FileQuestionRepository

        repo = FileQuestionRepository(sample_json)
        results = await repo.get_all(category="arrays")

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_with_filters(self, sample_json):
        from app.repositories.file_question_repository import FileQuestionRepository

        repo = FileQuestionRepository(sample_json)
        results = await repo.search("test", difficulty=Difficulty.EASY)

        assert len(results) == 1
        assert results[0].id == "test-one"

    @pytest.mark.asyncio
    async def test_get_summaries(self, sample_json):
        from app.repositories.file_question_repository import FileQuestionRepository

        repo = FileQuestionRepository(sample_json)
        summaries = await repo.get_summaries()

        assert len(summaries) == 3
        assert summaries[0].id == "test-one"
        assert summaries[0].title == "Test One"
        assert summaries[0].difficulty == Difficulty.EASY
        assert summaries[0].category == "arrays"

    @pytest.mark.asyncio
    async def test_get_summaries_filters_by_difficulty(self, sample_json):
        from app.repositories.file_question_repository import FileQuestionRepository

        repo = FileQuestionRepository(sample_json)
        summaries = await repo.get_summaries(difficulty=Difficulty.EASY)

        assert len(summaries) == 1
        assert summaries[0].id == "test-one"

    @pytest.mark.asyncio
    async def test_get_summaries_filters_by_category(self, sample_json):
        from app.repositories.file_question_repository import FileQuestionRepository

        repo = FileQuestionRepository(sample_json)
        summaries = await repo.get_summaries(category="strings")

        assert len(summaries) == 1
        assert summaries[0].id == "test-three"

    @pytest.mark.asyncio
    async def test_search_summaries(self, sample_json):
        from app.repositories.file_question_repository import FileQuestionRepository

        repo = FileQuestionRepository(sample_json)
        results = await repo.search_summaries("Reverse")

        assert len(results) == 1
        assert results[0].id == "test-three"

    @pytest.mark.asyncio
    async def test_search_summaries_with_difficulty_filter(self, sample_json):
        from app.repositories.file_question_repository import FileQuestionRepository

        repo = FileQuestionRepository(sample_json)
        results = await repo.search_summaries("test", difficulty=Difficulty.EASY)

        assert len(results) == 1
        assert results[0].id == "test-one"

    @pytest.mark.asyncio
    async def test_save_and_get_validation_status(self, sample_json):
        from app.models.question_validation_schemas import QuestionValidationStatus
        from app.repositories.file_question_repository import FileQuestionRepository

        repo = FileQuestionRepository(sample_json)
        status = QuestionValidationStatus(
            is_validated=True, validation_passed=True, last_validated=None
        )
        await repo.save_validation_status("test-one", status)

        statuses = await repo.get_validation_statuses()
        assert "test-one" in statuses
        assert statuses["test-one"]["is_validated"] is True
        assert statuses["test-one"]["validation_passed"] is True

    @pytest.mark.asyncio
    async def test_get_validation_statuses_empty_by_default(self, sample_json):
        from app.repositories.file_question_repository import FileQuestionRepository

        repo = FileQuestionRepository(sample_json)
        statuses = await repo.get_validation_statuses()

        assert statuses == {}
