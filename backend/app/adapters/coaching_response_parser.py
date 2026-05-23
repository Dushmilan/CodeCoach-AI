import json
import logging

logger = logging.getLogger(__name__)


class CoachingResponseParser:
    """Parses raw NIM API response text into a structured coaching response dict."""

    def parse_structured(self, content: str) -> dict:
        try:
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()

            structured_data = json.loads(content)
            return structured_data

        except json.JSONDecodeError:
            return self._fallback_parse(content)

    def parse_stream_chunk(self, line: str) -> str:
        if not line.startswith("data: "):
            return ""
        data = line[6:]
        if data == "[DONE]":
            return ""
        try:
            chunk = json.loads(data)
            if "choices" in chunk and chunk["choices"]:
                delta = chunk["choices"][0].get("delta", {})
                return delta.get("content", "")
        except json.JSONDecodeError:
            pass
        return ""

    def _fallback_parse(self, content: str) -> dict:
        import re

        markdown_json = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if markdown_json:
            content = markdown_json.group(1)

        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            try:
                partial_json = json_match.group(0)
                open_braces = partial_json.count("{")
                close_braces = partial_json.count("}")
                if open_braces > close_braces:
                    partial_json += "}" * (open_braces - close_braces)
                open_brackets = partial_json.count("[")
                close_brackets = partial_json.count("]")
                if open_brackets > close_brackets:
                    partial_json += "]" * (open_brackets - close_brackets)

                structured_data = json.loads(partial_json)
                for field in ["summary", "hints", "suggestions", "edge_cases"]:
                    if field not in structured_data:
                        structured_data[field] = [] if field != "summary" else ""
                for field in ["code_review", "complexity_analysis", "explanation", "debug_help"]:
                    if field not in structured_data:
                        structured_data[field] = None
                return structured_data
            except Exception as parse_error:
                logger.warning(f"Failed to parse partial JSON: {parse_error}")

        clean_content = re.sub(r"\{[^}]*\}", "", content)
        clean_content = re.sub(r"\[.*?\]", "", clean_content)
        clean_content = re.sub(r"\s+", " ", clean_content).strip()

        return {
            "summary": clean_content[:200] if clean_content else "Unable to generate structured response. Please try again.",
            "hints": [],
            "code_review": None,
            "complexity_analysis": None,
            "suggestions": [],
            "edge_cases": [],
            "explanation": clean_content if clean_content else content[:1000],
            "debug_help": None,
        }
