import os
import sys
import json
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def generate_lessons(
    language: str,
    count: int,
    output_dir,
    api_key: str = None,
    _call_nim=None,
):
    """Generate lessons for a language and write to output files.

    Args:
        language: Target language (python, c, java).
        count: Number of lessons to generate.
        output_dir: Path to the data directory.
        api_key: NVIDIA NIM API key (not used when _call_nim is provided).
        _call_nim: Callable for NIM API (injected for testing).

    Returns:
        List of lesson dicts that were written.
    """
    prompt = f"""Generate {count} lessons for learning {language} programming.

Each lesson must be either a "theory" or "exercise" type.

Return a JSON array. Each lesson must have these exact fields:
  - id: unique string slug (e.g. "py-loops-exercise")
  - course_id: "{language}-fundamentals"
  - module_id: module this belongs to (use consistent module IDs for the language)
  - title: string
  - type: "theory" or "exercise"
  - content: markdown lesson body
  - order: integer (pick up from existing lessons)
  - starter_code: string or null (required for exercises)
  - test_cases: array of {{"input": string, "expected_output": string, "description": string}} or null (required for exercises)
  - language: "{language}"

Return ONLY the JSON array, no other text."""

    if _call_nim:
        response = _call_nim(prompt, api_key or "test", "meta/llama-3.1-8b-instruct")
    else:
        response = _call_nvidia_with_retry(prompt, api_key, "meta/llama-3.1-8b-instruct")

    try:
        lessons = json.loads(response)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse NIM response as JSON: {e}\nResponse preview: {response[:200]}"
        ) from e
    lessons_file = os.path.join(str(output_dir), "lessons.json")
    existing = []
    if os.path.exists(lessons_file):
        with open(lessons_file, "r") as f:
            data = json.load(f)
            existing = data.get("items", data) if isinstance(data, dict) else data

    existing_ids = {l["id"] for l in existing}
    new_lessons = [l for l in lessons if l["id"] not in existing_ids]
    all_lessons = existing + new_lessons

    with open(lessons_file, "w", encoding="utf-8") as f:
        json.dump({"items": all_lessons}, f, indent=2, default=str)

    logger.info(f"Wrote {len(new_lessons)} new lessons to {lessons_file}")
    return new_lessons


def _call_nvidia_with_retry(prompt: str, api_key: str, model: str):
    import httpx

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a programming curriculum generator. Return ONLY valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 8192,
        "temperature": 0.7,
        "top_p": 0.9,
        "stream": False,
    }

    with httpx.Client(timeout=120.0) as client:
        response = client.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate programming curriculum lessons")
    parser.add_argument("--language", required=True, choices=["python", "c", "java"])
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--output-dir", default="data")
    args = parser.parse_args()

    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        logger.error("NVIDIA_API_KEY environment variable is required")
        sys.exit(1)

    generate_lessons(
        language=args.language,
        count=args.count,
        output_dir=args.output_dir,
        api_key=api_key,
    )
