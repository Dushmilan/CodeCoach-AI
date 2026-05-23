import pytest
from app.adapters.coaching_response_parser import CoachingResponseParser


@pytest.fixture
def parser():
    return CoachingResponseParser()


class TestParseStructured:
    def test_valid_json(self, parser):
        content = '{"summary": "Great work", "hints": ["Try X"]}'
        result = parser.parse_structured(content)
        assert result["summary"] == "Great work"
        assert result["hints"] == ["Try X"]

    def test_json_with_triple_backtick_json_fence(self, parser):
        content = '```json\n{"summary": "Hi", "hints": []}\n```'
        result = parser.parse_structured(content)
        assert result["summary"] == "Hi"

    def test_json_with_triple_backtick_fence(self, parser):
        content = '```\n{"summary": "Hello", "hints": []}\n```'
        result = parser.parse_structured(content)
        assert result["summary"] == "Hello"

    def test_malformed_json_falls_back(self, parser):
        content = "Here is some text with no JSON at all"
        result = parser.parse_structured(content)
        assert isinstance(result, dict)
        assert "summary" in result

    def test_nested_json_object(self, parser):
        content = '{"summary": "Test", "code_review": {"line": 1}}'
        result = parser.parse_structured(content)
        assert result["summary"] == "Test"
        assert result["code_review"]["line"] == 1

    def test_empty_content(self, parser):
        result = parser.parse_structured("")
        assert isinstance(result, dict)
        assert result["hints"] == []


class TestParseStreamChunk:
    def test_parses_data_prefix(self, parser):
        line = 'data: {"choices": [{"delta": {"content": "Hello"}}]}'
        result = parser.parse_stream_chunk(line)
        assert result == "Hello"

    def test_returns_empty_for_done_signal(self, parser):
        result = parser.parse_stream_chunk("data: [DONE]")
        assert result == ""

    def test_returns_empty_for_no_data_prefix(self, parser):
        result = parser.parse_stream_chunk("random line")
        assert result == ""

    def test_returns_empty_for_malformed_json(self, parser):
        result = parser.parse_stream_chunk("data: {bad json")
        assert result == ""

    def test_returns_empty_for_missing_choices(self, parser):
        line = 'data: {"not_choices": []}'
        result = parser.parse_stream_chunk(line)
        assert result == ""

    def test_returns_empty_for_empty_choices(self, parser):
        line = 'data: {"choices": []}'
        result = parser.parse_stream_chunk(line)
        assert result == ""

    def test_returns_empty_for_missing_delta(self, parser):
        line = 'data: {"choices": [{"no_delta": true}]}'
        result = parser.parse_stream_chunk(line)
        assert result == ""


class TestFallbackParse:
    def test_extracts_json_from_markdown_block(self, parser):
        content = "Some text\n```json\n{\"summary\": \"Extracted\"}\n```\nmore text"
        result = parser._fallback_parse(content)
        assert result["summary"] == "Extracted"

    def test_auto_closes_unclosed_braces(self, parser):
        content = '{"summary": "Open", "nested": {"inner": 1}'
        result = parser._fallback_parse(content)
        assert result["summary"] == "Open"

    def test_auto_closes_unclosed_brackets(self, parser):
        content = '{"summary": "Test", "hints": ["a", "b"'
        result = parser._fallback_parse(content)

    def test_ensures_all_eight_fields_present(self, parser):
        content = '{"summary": "Minimal"}'
        result = parser._fallback_parse(content)
        assert "summary" in result
        assert "hints" in result
        assert "code_review" in result
        assert "complexity_analysis" in result
        assert "suggestions" in result
        assert "edge_cases" in result
        assert "explanation" in result
        assert "debug_help" in result

    def test_list_fields_default_to_empty_list(self, parser):
        content = '{"summary": "Test"}'
        result = parser._fallback_parse(content)
        assert result["code_review"] is None
        assert result["hints"] == []

    def test_fallback_with_no_json_returns_clean_content(self, parser):
        content = "Just plain text with no structure"
        result = parser._fallback_parse(content)
        assert result["summary"] is not None
        assert len(result["summary"]) > 0
