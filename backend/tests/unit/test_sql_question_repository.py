import pytest
import pytest_asyncio
from app.models.schemas import Question, Difficulty, StarterCode, Example, TestCase


@pytest.fixture
def sample_question():
    return Question(
        id="test-1",
        title="Test Question",
        difficulty=Difficulty.EASY,
        category="arrays",
        company_tags=["Google", "Meta"],
        description="A test question description.",
        starter=StarterCode(
            python="def solve():\n    pass",
            javascript="function solve() {}",
            java="class Solve {}",
        ),
        examples=[Example(input="1", output="1", explanation="Basic test")],
        test_cases=[TestCase(input="1", expected_output="1", description="TC1")],
        hints=["Think about it"],
        solution="Just do it",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["n <= 1000"],
        is_interactive=False,
    )


@pytest_asyncio.fixture
async def repo(test_db):
    from app.repositories.sql_question_repository import SqlQuestionRepository

    return SqlQuestionRepository(test_db)


class TestSqlQuestionRepository:
    @pytest.mark.asyncio
    async def test_add_and_get_by_id(self, repo, sample_question):
        await repo.add(sample_question)
        await repo.session.commit()

        fetched = await repo.get_by_id("test-1")
        assert fetched is not None
        assert fetched.id == "test-1"
        assert fetched.title == "Test Question"
        assert fetched.difficulty == Difficulty.EASY
        assert fetched.category == "arrays"
        assert fetched.company_tags == ["Google", "Meta"]
        assert fetched.hints == ["Think about it"]

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo):
        fetched = await repo.get_by_id("nonexistent")
        assert fetched is None

    @pytest.mark.asyncio
    async def test_get_all(self, repo, sample_question):
        await repo.add(sample_question)

        q2 = sample_question.model_copy()
        q2.id = "test-2"
        q2.title = "Another Question"
        await repo.add(q2)
        await repo.session.commit()

        all_q = await repo.get_all()
        assert len(all_q) == 2

    @pytest.mark.asyncio
    async def test_get_all_filters_by_difficulty(self, repo, sample_question):
        await repo.add(sample_question)

        q2 = sample_question.model_copy()
        q2.id = "test-2"
        q2.difficulty = Difficulty.HARD
        await repo.add(q2)
        await repo.session.commit()

        easy = await repo.get_all(difficulty=Difficulty.EASY)
        assert len(easy) == 1
        assert easy[0].id == "test-1"

        hard = await repo.get_all(difficulty=Difficulty.HARD)
        assert len(hard) == 1
        assert hard[0].id == "test-2"

    @pytest.mark.asyncio
    async def test_get_all_filters_by_category(self, repo, sample_question):
        await repo.add(sample_question)

        q2 = sample_question.model_copy()
        q2.id = "test-2"
        q2.category = "strings"
        await repo.add(q2)
        await repo.session.commit()

        arrays = await repo.get_all(category="arrays")
        assert len(arrays) == 1
        assert arrays[0].id == "test-1"

    @pytest.mark.asyncio
    async def test_search_by_title(self, repo, sample_question):
        await repo.add(sample_question)

        q2 = sample_question.model_copy()
        q2.id = "test-2"
        q2.title = "UniqueSearchTitle"
        await repo.add(q2)
        await repo.session.commit()

        results = await repo.search("UniqueSearch")
        assert len(results) == 1
        assert results[0].id == "test-2"

    @pytest.mark.asyncio
    async def test_search_by_description(self, repo, sample_question):
        await repo.add(sample_question)

        q2 = sample_question.model_copy()
        q2.id = "test-2"
        q2.description = "A very unique description for searching"
        await repo.add(q2)
        await repo.session.commit()

        results = await repo.search("unique description")
        assert len(results) == 1
        assert results[0].id == "test-2"

    @pytest.mark.asyncio
    async def test_search_with_difficulty_filter(self, repo, sample_question):
        await repo.add(sample_question)

        q2 = sample_question.model_copy()
        q2.id = "test-2"
        q2.title = "Test Another"
        q2.difficulty = Difficulty.HARD
        await repo.add(q2)
        await repo.session.commit()

        results = await repo.search("Test", difficulty=Difficulty.EASY)
        assert len(results) == 1
        assert results[0].id == "test-1"

    @pytest.mark.asyncio
    async def test_get_categories(self, repo, sample_question):
        await repo.add(sample_question)

        q2 = sample_question.model_copy()
        q2.id = "test-2"
        q2.category = "strings"
        await repo.add(q2)
        await repo.session.commit()

        cats = await repo.get_categories()
        assert "arrays" in cats
        assert "strings" in cats
        assert len(cats) == 2

    @pytest.mark.asyncio
    async def test_get_company_tags(self, repo, sample_question):
        await repo.add(sample_question)

        q2 = sample_question.model_copy()
        q2.id = "test-2"
        q2.company_tags = ["Acme", "Beta"]
        await repo.add(q2)
        await repo.session.commit()

        tags = await repo.get_company_tags()
        assert "Google" in tags
        assert "Meta" in tags
        assert "Acme" in tags
        assert "Beta" in tags

    @pytest.mark.asyncio
    async def test_get_summaries(self, repo, sample_question):
        await repo.add(sample_question)
        await repo.session.commit()

        summaries = await repo.get_summaries()
        assert len(summaries) == 1
        assert summaries[0].id == "test-1"
        assert summaries[0].title == "Test Question"
        assert summaries[0].difficulty == Difficulty.EASY
        assert summaries[0].category == "arrays"

    @pytest.mark.asyncio
    async def test_get_summaries_filters_by_difficulty(self, repo, sample_question):
        await repo.add(sample_question)

        q2 = sample_question.model_copy()
        q2.id = "test-2"
        q2.difficulty = Difficulty.HARD
        await repo.add(q2)
        await repo.session.commit()

        summaries = await repo.get_summaries(difficulty=Difficulty.EASY)
        assert len(summaries) == 1
        assert summaries[0].id == "test-1"

    @pytest.mark.asyncio
    async def test_search_summaries(self, repo, sample_question):
        await repo.add(sample_question)

        q2 = sample_question.model_copy()
        q2.id = "test-2"
        q2.title = "Reverse String"
        await repo.add(q2)
        await repo.session.commit()

        results = await repo.search_summaries("Reverse")
        assert len(results) == 1
        assert results[0].id == "test-2"

    @pytest.mark.asyncio
    async def test_get_summaries_limit_offset(self, repo, sample_question):
        await repo.add(sample_question)

        q2 = sample_question.model_copy()
        q2.id = "test-2"
        q2.title = "A Second Question"
        await repo.add(q2)
        await repo.session.commit()

        first = await repo.get_summaries(limit=1, offset=0)
        assert [s.id for s in first] == ["test-2"]
        second = await repo.get_summaries(limit=1, offset=1)
        assert [s.id for s in second] == ["test-1"]
        assert await repo.count_summaries() == 2

    @pytest.mark.asyncio
    async def test_count_summaries_matches_search_filters(self, repo, sample_question):
        await repo.add(sample_question)

        q2 = sample_question.model_copy()
        q2.id = "test-2"
        q2.title = "Reverse String"
        await repo.add(q2)
        await repo.session.commit()

        assert await repo.count_summaries(query="Reverse") == 1
        assert await repo.count_summaries(difficulty=Difficulty.HARD) == 0
        assert await repo.count_summaries() == 2

    @pytest.mark.asyncio
    async def test_add_with_complex_fields(self, repo):
        q = Question(
            id="complex-1",
            title="Complex Question",
            difficulty=Difficulty.HARD,
            category="dynamic-programming",
            company_tags=[],
            description="Complex description.",
            starter=StarterCode(
                python="def solve():\n    pass",
                javascript="function solve() {}",
                java="class Solve {}",
            ),
            examples=[
                Example(input="[1,2,3]", output="6", explanation="Sum"),
                Example(input="[4,5]", output="9", explanation="Also sum"),
            ],
            test_cases=[
                TestCase(input="[1,2,3]", expected_output="6", description="Basic"),
                TestCase(
                    input="[]", expected_output="0", description="Empty", hidden=True
                ),
            ],
            hints=["Hint 1", "Hint 2", "Hint 3"],
            solution="Dynamic programming approach",
            time_complexity="O(n^2)",
            space_complexity="O(n)",
            constraints=["n <= 100", "values <= 1000"],
            is_interactive=False,
        )
        await repo.add(q)
        await repo.session.commit()

        fetched = await repo.get_by_id("complex-1")
        assert fetched is not None
        assert len(fetched.examples) == 2
        assert len(fetched.test_cases) == 2
        assert len(fetched.hints) == 3
        assert len(fetched.constraints) == 2

    @pytest.mark.asyncio
    async def test_validation_statuses_empty(self, repo):
        statuses = await repo.get_validation_statuses()
        assert statuses == {}


class TestDifficultyCountsNoMaterialization:
    """M-04: stats counts must be answered by SQL aggregates, never by
    materializing every question row through get_all()."""

    @pytest.mark.asyncio
    async def test_difficulty_counts_use_grouped_query(self, repo, test_db):
        from sqlalchemy import text

        from app.services.question_bank import QuestionBank

        class NoMaterializeRepo(type(repo)):
            async def get_all(self, *args, **kwargs):
                raise AssertionError(
                    "difficulty stats must not call get_all(); use a SQL GROUP BY count"
                )

        await test_db.execute(
            text(
                "INSERT INTO questions "
                "(id, title, difficulty, category, company_tags, description, "
                " starter_code, examples, test_cases, constraints, hints, is_interactive) "
                "VALUES ('m04-e', 'E', 'easy', 'arrays', '[]', 'd', '{}', '[]', '[]', '[]', '[]', 0), "
                "('m04-e2', 'E2', 'easy', 'arrays', '[]', 'd', '{}', '[]', '[]', '[]', '[]', 0), "
                "('m04-h', 'H', 'hard', 'dp', '[]', 'd', '{}', '[]', '[]', '[]', '[]', 0)"
            )
        )
        await test_db.commit()

        spy_repo = NoMaterializeRepo(test_db)
        service = QuestionBank(repository=spy_repo)
        counts = await service._compute_difficulty_counts()

        assert counts == {"easy": 2, "medium": 0, "hard": 1}
