import pytest
from app.adapters.coaching_prompts import (
    build_system_prompt,
    build_structured_system_prompt,
    build_user_prompt,
    build_structured_user_prompt,
    MODE_SECTIONS,
    PERSONA,
    STRUCTURED_PERSONA,
    GENERAL_GUIDELINES,
)


class TestBuildSystemPrompt:
    def test_persona_is_socratic(self):
        prompt = build_system_prompt("hint", "python")
        assert "Socratic" in prompt
        assert "NEVER give away the answer" in prompt

    def test_frustration_escalation_strategy(self):
        prompt = build_system_prompt("hint", "python")
        assert "frustration" in prompt
        assert "completely stuck" in prompt

    def test_lesson_context_framing(self):
        prompt = build_system_prompt("hint", "python", lesson_context="Python Lesson 4: For Loops")
        assert "Frame your guiding questions" in prompt
        assert "Connect the student's current struggle" in prompt

    def test_debug_mode_socratic(self):
        prompt = build_system_prompt("debug", "python")
        assert "Do NOT explain the fix" in prompt

    def test_review_mode_socratic(self):
        prompt = build_system_prompt("review", "python")
        assert "Do NOT write the improved code" in prompt

    def test_explain_mode_bite_sized(self):
        prompt = build_system_prompt("explain", "python")
        assert "ONE foundational idea at a time" in prompt
        assert "Do NOT dump the full concept" in prompt


    def test_includes_persona(self):
        prompt = build_system_prompt("hint", "python")
        assert "You are CodeCoach AI" in prompt

    def test_includes_general_guidelines(self):
        prompt = build_system_prompt("hint", "python")
        assert "General Guidelines" in prompt

    def test_includes_language(self):
        prompt = build_system_prompt("hint", "python")
        assert "Respond in: python" in prompt

    def test_includes_hints_mode_section(self):
        prompt = build_system_prompt("hint", "python")
        assert "Hints (mode: hint)" in prompt

    def test_includes_review_mode_section(self):
        prompt = build_system_prompt("review", "python")
        assert "Code Review (mode: review)" in prompt

    def test_includes_explain_mode_section(self):
        prompt = build_system_prompt("explain", "python")
        assert "Explanations (mode: explain)" in prompt

    def test_includes_debug_mode_section(self):
        prompt = build_system_prompt("debug", "python")
        assert "Debug Help (mode: debug)" in prompt

    def test_includes_freeform_mode_section(self):
        prompt = build_system_prompt("freeform", "python")
        assert "General Questions (mode: freeform)" in prompt

    def test_unknown_mode_omits_section(self):
        prompt = build_system_prompt("unknown", "python")
        assert "You are CodeCoach AI" in prompt
        assert "Respond in: python" in prompt
        assert "General Guidelines" in prompt

    def test_includes_lesson_context_when_provided(self):
        prompt = build_system_prompt("hint", "python", lesson_context="Python Lesson 4: For Loops")
        assert "Python Lesson 4: For Loops" in prompt
        assert "lesson" in prompt.lower()

    def test_omits_lesson_context_when_not_provided(self):
        prompt = build_system_prompt("hint", "python")
        assert "lesson_context" not in prompt


class TestBuildStructuredSystemPrompt:
    def test_structured_persona_is_socratic(self):
        prompt = build_structured_system_prompt("hint", "python")
        assert "Socratic" in prompt
        assert "Never give away the full solution" in prompt

    def test_structured_includes_general_guidelines(self):
        prompt = build_structured_system_prompt("hint", "python")
        assert "General Guidelines" in prompt
        assert "Be concise but thorough" in prompt

    def test_single_hint_rule(self):
        prompt = build_structured_system_prompt("hint", "python")
        assert "EXACTLY 1 subtle hint" in prompt

    def test_minimize_populated_fields_rule(self):
        prompt = build_structured_system_prompt("hint", "python")
        assert "Only populate the specific field" in prompt

    def test_end_summary_with_question_rule(self):
        prompt = build_structured_system_prompt("hint", "python")
        assert "end summary with a question" in prompt

    def test_structured_frustration_escalation_strategy(self):
        prompt = build_structured_system_prompt("hint", "python")
        assert "frustration" in prompt
        assert "completely stuck" in prompt

    def test_structured_lesson_context_framing(self):
        prompt = build_structured_system_prompt("hint", "python", lesson_context="Python Lesson 4: For Loops")
        assert "Frame your guiding questions" in prompt
        assert "Connect the student's current struggle" in prompt


    def test_includes_structured_persona(self):
        prompt = build_structured_system_prompt("hint", "python")
        assert "You MUST respond with ONLY a valid JSON object" in prompt

    def test_includes_language_line(self):
        prompt = build_structured_system_prompt("hint", "python")
        assert "Language: python" in prompt

    def test_includes_hints_structured_section(self):
        prompt = build_structured_system_prompt("hint", "python")
        assert "hint mode:" in prompt
        assert "EXACTLY 1 subtle hint" in prompt

    def test_includes_review_structured_section(self):
        prompt = build_structured_system_prompt("review", "python")
        assert "review mode:" in prompt
        assert "Overall assessment" in prompt

    def test_includes_explain_structured_section(self):
        prompt = build_structured_system_prompt("explain", "python")
        assert "explain mode:" in prompt
        assert "One concept at a time" in prompt

    def test_includes_debug_structured_section(self):
        prompt = build_structured_system_prompt("debug", "python")
        assert "debug mode:" in prompt
        assert "Acknowledge the issue" in prompt

    def test_includes_freeform_structured_section(self):
        prompt = build_structured_system_prompt("freeform", "python")
        assert "freeform mode:" in prompt
        assert "Main answer" in prompt

    def test_unknown_mode_omits_structured_section(self):
        prompt = build_structured_system_prompt("unknown", "python")
        assert "You MUST respond with ONLY a valid JSON object" in prompt
        assert "Language: python" in prompt

    def test_structured_includes_lesson_context_when_provided(self):
        prompt = build_structured_system_prompt("hint", "python", lesson_context="Python Lesson 4: For Loops")
        assert "Python Lesson 4: For Loops" in prompt

    def test_structured_omits_lesson_context_when_not_provided(self):
        prompt = build_structured_system_prompt("hint", "python")
        assert "lesson_context" not in prompt


class TestBuildUserPrompt:
    def test_contains_problem_and_code_and_message(self):
        prompt = build_user_prompt("Two Sum", "def f(): pass", "Help me", "hint")
        assert "Two Sum" in prompt
        assert "def f(): pass" in prompt
        assert "Help me" in prompt
        assert "hint" in prompt

    def test_code_in_code_block(self):
        prompt = build_user_prompt("Test", "code here", "msg", "review")
        assert "code here" in prompt
        assert "```" in prompt

    def test_includes_mode_label(self):
        prompt = build_user_prompt("P", "c", "m", "debug")
        assert "Mode: debug" in prompt

    def test_ends_with_coaching_feedback_request(self):
        prompt = build_user_prompt("P", "c", "m", "hint")
        assert "coaching feedback" in prompt


class TestBuildStructuredUserPrompt:
    def test_contains_problem_and_code_and_message(self):
        prompt = build_structured_user_prompt("Two Sum", "def f(): pass", "Help", "explain")
        assert "Two Sum" in prompt
        assert "def f(): pass" in prompt
        assert "Help" in prompt

    def test_includes_json_instruction(self):
        prompt = build_structured_user_prompt("P", "c", "m", "hint")
        assert "valid JSON object" in prompt


class TestModeSections:
    def test_maps_all_five_modes(self):
        assert set(MODE_SECTIONS.keys()) == {"hint", "review", "explain", "debug", "freeform"}

    def test_each_mode_has_unstructured_section(self):
        for name, entry in MODE_SECTIONS.items():
            assert "unstructured" in entry, f"{name} missing unstructured section"
            assert isinstance(entry["unstructured"], str)

    def test_each_mode_has_structured_section(self):
        for name, entry in MODE_SECTIONS.items():
            assert "structured" in entry, f"{name} missing structured section"
            assert isinstance(entry["structured"], str)
