import pytest
from unittest.mock import MagicMock, AsyncMock

from app.models.schemas import Question, Difficulty, StarterCode, Example, TestCase
from app.models.question_validation_schemas import (
    ValidationUseCase,
    QuestionValidationResult,
)


@pytest.fixture
def valid_question():
    return Question(
        id="test-q",
        title="Test",
        difficulty=Difficulty.EASY,
        category="arrays",
        description="A test problem",
        starter=StarterCode(
            python="def f(): pass",
            javascript="function f(){}",
            java="class S{public static void f(){}}",
        ),
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
    async def test_quick_validate_runs_fast_use_cases(
        self, valid_question, mock_executor
    ):
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
        assert order[-1] == ValidationUseCase.ANIMATION

    @pytest.mark.asyncio
    async def test_get_validation_summary(self, valid_question, mock_executor):
        from app.services.question_validator import QuestionValidatorService

        service = QuestionValidatorService(executor=mock_executor)

        result = await service.validate_question(valid_question)
        summary = service.get_validation_summary(result)

        assert summary["question_id"] == "test-q"
        assert "total_issues" in summary
        assert "use_cases_run" in summary
        assert "issues_by_use_case" in summary

    @pytest.mark.asyncio
    async def test_skipped_use_cases(self, valid_question, mock_executor):
        from app.services.question_validator import QuestionValidatorService
        from app.models.question_validation_schemas import QuestionValidationConfig

        config = QuestionValidationConfig(skip_use_cases=[ValidationUseCase.SOLUTION])
        service = QuestionValidatorService(executor=mock_executor, config=config)

        result = await service.validate_question(valid_question)
        assert ValidationUseCase.SOLUTION not in result.results


# ============================================================================
# Round 6: fail_on_warnings consumer audit.
# The Round-5 WARNING downgrade (prose reference + stub starter) must not be
# re-flagged bank-wide by a strict consumer. Audit result: no production
# caller sets fail_on_warnings=True — every consumer (validation API
# get_validator_service, admin validate endpoint, QuestionBank default,
# scripts/sync_local_to_db.py which does not invoke validation at all)
# runs the default non-strict config. These tests pin that contract.
# ============================================================================


class TestFailOnWarningsDefaultRound6:
    """Default is non-strict at every consumer layer; strict is opt-in only."""

    def test_config_defaults_to_non_strict(self):
        from app.models.question_validation_schemas import QuestionValidationConfig

        assert QuestionValidationConfig().fail_on_warnings is False

    def test_default_service_constructs_non_strict(self, mock_executor):
        from app.services.question_validator import QuestionValidatorService

        service = QuestionValidatorService(executor=mock_executor)
        assert service.config.fail_on_warnings is False

    def test_api_factory_builds_non_strict_service(self, mock_executor):
        from app.api.question_validation import get_validator_service

        service = get_validator_service(executor=mock_executor)
        assert service.config.fail_on_warnings is False

    @pytest.mark.asyncio
    async def test_warning_only_shape_stays_valid_by_default(self, mock_executor):
        from app.services.question_validator import QuestionValidatorService
        from app.models.schemas import Question

        question = Question(
            id="prose-ref",
            title="Prose reference",
            difficulty="easy",
            category="arrays",
            description="A test problem",
            starter={
                "python": "def f(): pass",
                "javascript": "function f(){}",
                "java": "class S{public static void f(){}}",
            },
            examples=[{"input": "1", "output": "1"}],
            test_cases=[{"input": "1", "expected_output": "1"}],
            solution="Return the array as is.",
        )
        service = QuestionValidatorService(executor=mock_executor)
        result = await service.validate_question(
            question, use_cases=[ValidationUseCase.SOLUTION]
        )
        assert result.error_count == 0
        assert result.warning_count >= 1
        assert result.valid is True

    @pytest.mark.asyncio
    async def test_strict_opt_in_still_reflags_warnings(self, mock_executor):
        from app.services.question_validator import QuestionValidatorService
        from app.models.question_validation_schemas import QuestionValidationConfig
        from app.models.schemas import Question

        question = Question(
            id="prose-ref",
            title="Prose reference",
            difficulty="easy",
            category="arrays",
            description="A test problem",
            starter={
                "python": "def f(): pass",
                "javascript": "function f(){}",
                "java": "class S{public static void f(){}}",
            },
            examples=[{"input": "1", "output": "1"}],
            test_cases=[{"input": "1", "expected_output": "1"}],
            solution="Return the array as is.",
        )
        strict = QuestionValidatorService(
            executor=mock_executor,
            config=QuestionValidationConfig(fail_on_warnings=True),
        )
        result = await strict.validate_question(
            question, use_cases=[ValidationUseCase.SOLUTION]
        )
        assert result.warning_count >= 1
        assert result.valid is False

    def test_no_production_consumer_enables_strict_mode(self):
        from pathlib import Path

        backend = Path(__file__).resolve().parents[2]
        hits = []
        for sub in ("app", "scripts"):
            for path in (backend / sub).rglob("*.py"):
                text = path.read_text()
                if "fail_on_warnings=True" in text.replace(" ", ""):
                    hits.append(str(path.relative_to(backend)))
        assert hits == []


# ============================================================================
# Round 7: call-site-anchored strict-mode guard.
# Round 6's guard scans app/ + scripts/ for the literal `fail_on_warnings=True`,
# which a future strict consumer in a NEW top-level dir (or a new API module)
# would silently bypass. These tests anchor on the constructor instead: every
# non-test file that calls `QuestionValidatorService(` is enumerated
# backend-wide, the set itself is pinned (a new consumer trips the test and
# forces an audit), and each call-site file is asserted strict-free. tests/
# is the intentional exception -- the strict opt-in test above must keep
# constructing a strict service to pin the reflag behavior.
# ============================================================================


class TestFailOnWarningsCallSitesRound7:
    """No present-or-future call site may opt into strict mode unnoticed."""

    @staticmethod
    def _backend_root():
        from pathlib import Path

        return Path(__file__).resolve().parents[2]

    def _call_site_files(self):
        backend = self._backend_root()
        sites = []
        for path in sorted(backend.rglob("*.py")):
            if "tests" in path.relative_to(backend).parts:
                continue
            if "QuestionValidatorService(" in path.read_text():
                sites.append(path)
        return sites

    def test_all_call_sites_are_known(self):
        sites = {
            str(p.relative_to(self._backend_root())) for p in self._call_site_files()
        }
        assert sites == {
            "app/api/admin.py",
            "app/api/question_validation.py",
        }

    def test_no_call_site_enables_strict_mode(self):
        offenders = [
            str(p.relative_to(self._backend_root()))
            for p in self._call_site_files()
            if "fail_on_warnings=True" in p.read_text().replace(" ", "")
        ]
        assert offenders == []


# ============================================================================
# Round 8: orchestrator resilience is real behavior, not dead code.
# The combined suite never takes the "unknown use case" skip
# (question_validator.py:85-87) or the "use case raised" fallback
# (91-93): every registered use case exists and ``BaseValidationUseCase``
# swallows its own errors. Both branches are the orchestrator's failure
# contract -- skip-and-warn on unknown, degrade-and-continue on raise --
# so these tests pin them as behavior: a deregistered enum is skipped
# without failing the question, and a raising use case degrades to a
# passed=False empty result while the rest of the batch still runs.
# ============================================================================


class TestQuestionValidatorResilienceRound8:
    """Unknown use cases skip; raising use cases degrade, never propagate."""

    async def test_unknown_use_case_is_skipped_not_key_error(
        self, valid_question, mock_executor
    ):
        from app.services.question_validator import QuestionValidatorService

        service = QuestionValidatorService(executor=mock_executor)
        del service.use_cases[ValidationUseCase.STRUCTURE]
        result = await service.validate_question(
            valid_question, use_cases=[ValidationUseCase.STRUCTURE]
        )
        assert ValidationUseCase.STRUCTURE not in result.results
        assert result.total_issues == 0
        assert result.valid is True

    async def test_raising_use_case_degrades_rest_of_batch_runs(
        self, valid_question, mock_executor
    ):
        from app.services.question_validator import QuestionValidatorService

        calls = []

        class _Boom:
            async def execute(self, question):
                calls.append(question)
                raise RuntimeError("boom")

        service = QuestionValidatorService(executor=mock_executor)
        service.use_cases[ValidationUseCase.STRUCTURE] = _Boom()
        result = await service.validate_question(
            valid_question,
            use_cases=[
                ValidationUseCase.STRUCTURE,
                ValidationUseCase.OUTPUT_FORMAT,
            ],
        )
        degraded = result.results[ValidationUseCase.STRUCTURE]
        assert degraded.passed is False
        assert degraded.issues == []
        assert ValidationUseCase.OUTPUT_FORMAT in result.results
        assert result.error_count == 0
        assert calls == [valid_question]
