import json
from app.adapters.coaching_prompts import (
    build_system_prompt,
    build_structured_system_prompt,
    build_user_prompt,
    build_structured_user_prompt,
    MODE_SECTIONS,
    PromptBuilder,
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
        prompt = build_system_prompt(
            "hint", "python", lesson_context="Python Lesson 4: For Loops"
        )
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
        prompt = build_system_prompt(
            "hint", "python", lesson_context="Python Lesson 4: For Loops"
        )
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

    def test_animation_contract_present(self):
        prompt = build_structured_system_prompt("hint", "python")
        assert "Animation Contract" in prompt
        assert "shapes" in prompt
        assert "motion" in prompt
        assert "never return JavaScript" in prompt

    def test_animation_never_invents_runtime_results(self):
        prompt = build_structured_system_prompt("explain", "python")
        assert "never invent runtime results" in prompt

    def test_all_nine_fields_rule(self):
        prompt = build_structured_system_prompt("hint", "python")
        assert "ALL 9 fields" in prompt

    def test_unstructured_prompt_omits_animation_contract(self):
        prompt = build_system_prompt("hint", "python")
        assert "Animation Contract" not in prompt

    def test_structured_frustration_escalation_strategy(self):
        prompt = build_structured_system_prompt("hint", "python")
        assert "frustration" in prompt
        assert "completely stuck" in prompt

    def test_structured_lesson_context_framing(self):
        prompt = build_structured_system_prompt(
            "hint", "python", lesson_context="Python Lesson 4: For Loops"
        )
        assert "Frame your guiding questions" in prompt
        assert "Connect the student's current struggle" in prompt

    def test_includes_structured_persona(self):
        prompt = build_structured_system_prompt("hint", "python")
        assert "You MUST respond with ONLY a valid JSON object" in prompt

    def test_includes_input_format_section(self):
        prompt = build_structured_system_prompt("hint", "python")
        assert "Input Format" in prompt
        assert "JSON object with fields" in prompt

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
        prompt = build_structured_system_prompt(
            "hint", "python", lesson_context="Python Lesson 4: For Loops"
        )
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
    def test_is_valid_json(self):
        prompt = build_structured_user_prompt(
            "Two Sum", "def f(): pass", "Help", "explain"
        )
        data = json.loads(prompt)
        assert data["problem"] == "Two Sum"
        assert data["code"] == "def f(): pass"
        assert data["message"] == "Help"
        assert data["mode"] == "explain"

    def test_has_expected_keys(self):
        prompt = build_structured_user_prompt("P", "c", "m", "hint")
        data = json.loads(prompt)
        assert set(data.keys()) == {"problem", "code", "message", "mode"}

    def test_handles_special_chars_in_code(self):
        prompt = build_structured_user_prompt(
            "Test", 'print("hello")\n# comment', "msg", "review"
        )
        data = json.loads(prompt)
        assert 'print("hello")' in data["code"]
        assert "# comment" in data["code"]

    def test_handles_special_chars_in_message(self):
        prompt = build_structured_user_prompt(
            "P", "c", 'it\'s "broken" somehow', "debug"
        )
        data = json.loads(prompt)
        assert data["message"] == 'it\'s "broken" somehow'

    def test_structured_user_prompt_includes_question(self):
        builder = PromptBuilder()
        _, user = builder.build(
            mode="animate",
            language="python",
            problem="Two Sum",
            code="def f(): pass",
            message="animate",
            structured=True,
            initial_code="def f():\n    pass",
            question={"title": "Two Sum", "category": "hash_map"},
        )
        data = json.loads(user)
        assert data["question"]["title"] == "Two Sum"
        assert data["question"]["category"] == "hash_map"

    def test_structured_user_prompt_never_leaks_hidden_test_cases(self):
        # Hidden test cases are curriculum secrets: they must never reach the
        # third-party model even though they live on the question object.
        builder = PromptBuilder()
        _, user = builder.build(
            mode="animate",
            language="python",
            problem="Two Sum",
            code="def f(): pass",
            message="animate",
            structured=True,
            initial_code="def f():\n    pass",
            question={
                "title": "Two Sum",
                "category": "hash_map",
                "test_cases": [{"input": "secret input", "output": "secret"}],
            },
        )
        data = json.loads(user)
        assert data["question"]["title"] == "Two Sum"
        assert "test_cases" not in data["question"]
        assert "secret input" not in user

    def test_structured_user_prompt_omits_question_when_absent(self):
        builder = PromptBuilder()
        _, user = builder.build(
            mode="animate",
            language="python",
            problem="P",
            code="c",
            message="m",
            structured=True,
            initial_code="s",
        )
        data = json.loads(user)
        assert "question" not in data


class TestAnimateMode:
    def test_animate_is_in_mode_sections(self):
        assert "animate" in MODE_SECTIONS

    def test_structured_prompt_includes_animate_contract(self):
        builder = PromptBuilder()
        system, _ = builder.build(
            mode="animate",
            language="python",
            problem="P",
            code="c",
            message="m",
            structured=True,
            initial_code="s",
        )
        assert "Animate Mode" in system
        assert "Generic Scene Contract" in system
        assert '"rect"' in system
        assert '"move"' in system
        assert "never return JavaScript" in system

    def test_animate_contract_enforces_a_rich_multi_step_scene(self):
        builder = PromptBuilder()
        system, _ = builder.build(
            mode="animate",
            language="python",
            problem="P",
            code="c",
            message="m",
            structured=True,
            initial_code="s",
        )
        assert "at least 3 steps" in system
        assert "pointer" in system

    def test_animate_contract_requires_single_shape_definition(self):
        builder = PromptBuilder()
        system, _ = builder.build(
            mode="animate",
            language="python",
            problem="P",
            code="c",
            message="m",
            structured=True,
            initial_code="s",
        )
        assert "Define every shape exactly once" in system
        assert "Never repeat a shape id" in system

    def test_animate_contract_requires_transform_op_per_step(self):
        builder = PromptBuilder()
        system, _ = builder.build(
            mode="animate",
            language="python",
            problem="P",
            code="c",
            message="m",
            structured=True,
            initial_code="s",
        )
        assert "only appear" not in system
        assert "visibly moves forward" in system
        assert "MUST include at least one transform op" in system

    def test_animate_contract_forces_a_moving_pointer(self):
        builder = PromptBuilder()
        system, _ = builder.build(
            mode="animate",
            language="python",
            problem="P",
            code="c",
            message="m",
            structured=True,
            initial_code="s",
        )
        assert "pointer" in system
        assert "advance" in system
        assert "move" in system

    def test_unstructured_prompt_includes_animate_section(self):
        builder = PromptBuilder()
        system, _ = builder.build(
            mode="animate",
            language="python",
            problem="P",
            code="c",
            message="m",
            structured=False,
        )
        assert "Animate (mode: animate)" in system

    def test_non_animate_modes_omit_animate_contract(self):
        builder = PromptBuilder()
        system, _ = builder.build(
            mode="hint",
            language="python",
            problem="P",
            code="c",
            message="m",
            structured=True,
        )
        assert "Animate Mode" not in system

    def test_structured_user_prompt_includes_initial_code(self):
        builder = PromptBuilder()
        _, user = builder.build(
            mode="animate",
            language="python",
            problem="Two Sum",
            code="def f(): pass",
            message="animate",
            structured=True,
            initial_code="def f():\n    pass",
        )
        data = json.loads(user)
        assert data["initial_code"] == "def f():\n    pass"

    def test_structured_user_prompt_omits_initial_code_when_absent(self):
        builder = PromptBuilder()
        _, user = builder.build(
            mode="hint",
            language="python",
            problem="P",
            code="c",
            message="m",
            structured=True,
        )
        data = json.loads(user)
        assert "initial_code" not in data

    def test_animate_contract_requires_a_non_null_animation(self):
        builder = PromptBuilder()
        system, _ = builder.build(
            mode="animate",
            language="python",
            problem="P",
            code="c",
            message="m",
            structured=True,
            initial_code="s",
        )
        assert "FORBIDDEN" in system
        assert "NON-NEGOTIABLE" in system
        assert "null" in system

    def test_animate_contract_never_uses_student_code(self):
        """The animation shows the OPTIMAL solution — the student's typed code
        is never compared, inspected, or visualized."""
        builder = PromptBuilder()
        system, _ = builder.build(
            mode="animate",
            language="python",
            problem="P",
            code="c",
            message="m",
            structured=True,
            initial_code="s",
        )
        assert "OPTIMAL solution" in system
        assert "Never compare against the student" in system
        assert "side-by-side" not in system

    def test_animate_contract_uses_question_input_data(self):
        builder = PromptBuilder()
        system, _ = builder.build(
            mode="animate",
            language="python",
            problem="P",
            code="c",
            message="m",
            structured=True,
            initial_code="s",
        )
        assert "question" in system
        assert "never invent runtime results" in system

    def test_animate_contract_keeps_scene_data_not_code(self):
        builder = PromptBuilder()
        system, _ = builder.build(
            mode="animate",
            language="python",
            problem="P",
            code="c",
            message="m",
            structured=True,
            initial_code="s",
        )
        assert "This is DATA, not code" in system
        assert "SVG" in system


class TestModeSections:
    def test_maps_all_six_modes(self):
        assert set(MODE_SECTIONS.keys()) == {
            "hint",
            "review",
            "explain",
            "debug",
            "freeform",
            "animate",
        }

    def test_each_mode_has_unstructured_section(self):
        for name, entry in MODE_SECTIONS.items():
            assert "unstructured" in entry, f"{name} missing unstructured section"
            assert isinstance(entry["unstructured"], str)

    def test_each_mode_has_structured_section(self):
        for name, entry in MODE_SECTIONS.items():
            assert "structured" in entry, f"{name} missing structured section"
            assert isinstance(entry["structured"], str)
