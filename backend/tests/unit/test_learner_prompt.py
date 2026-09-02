"""Unit: PromptBuilder learner_context + submission_context injection."""

from app.adapters.coaching_prompts import PromptBuilder


class TestPromptBuilderLearnerContext:
    def test_learner_and_submission_blocks_appended(self):
        b = PromptBuilder()
        system, _ = b.build(
            mode="hint",
            language="python",
            problem="p",
            code="c",
            message="m",
            structured=True,
            learner_context="## Learner Skill Context\n- arrays: mastery 0.10",
            submission_context="## Recent Attempts\n- q1 failed",
        )
        assert "## Learner Skill Context" in system
        assert "arrays: mastery 0.10" in system
        assert "Recent Attempts" in system
        # order: learner before submission before guidelines
        assert system.index("Learner Skill Context") < system.index("Recent Attempts")

    def test_no_learner_blocks_when_none(self):
        b = PromptBuilder()
        system, _ = b.build(
            mode="hint",
            language="python",
            problem="p",
            code="c",
            message="m",
            structured=True,
            learner_context=None,
            submission_context=None,
        )
        assert "Learner Skill Context" not in system
        assert "Recent Attempts" not in system

    def test_empty_string_not_appended(self):
        b = PromptBuilder()
        system, _ = b.build(
            mode="hint",
            language="python",
            problem="p",
            code="c",
            message="m",
            structured=True,
            learner_context="",
            submission_context="",
        )
        assert "Learner Skill Context" not in system
        assert "Recent Attempts" not in system

    def test_unstructured_also_includes_blocks(self):
        b = PromptBuilder()
        system, _ = b.build(
            mode="review",
            language="python",
            problem="p",
            code="c",
            message="m",
            structured=False,
            learner_context="skill-block",
            submission_context="sub-block",
        )
        assert "skill-block" in system
        assert "sub-block" in system
