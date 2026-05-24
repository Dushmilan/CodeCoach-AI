import os
import sys
import json
import re
import logging
import argparse
from typing import List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

TOPICS = [
    "Arrays & Hashing",
    "Two Pointers",
    "Sliding Window",
    "Stack",
    "Binary Search",
    "Linked List",
    "Trees",
    "Tries",
    "Heap / Priority Queue",
    "Backtracking",
    "Graphs",
    "Dynamic Programming",
    "Greedy",
    "Intervals",
]

QUESTIONS_FILE = os.path.join(
    os.path.dirname(__file__), "..", "questions", "sample_questions.json"
)

EXISTING_IDS: set = set()


def load_existing_ids():
    global EXISTING_IDS
    if not os.path.exists(QUESTIONS_FILE):
        return
    with open(QUESTIONS_FILE, "r") as f:
        data = json.load(f)
    questions = data.get("questions", data) if isinstance(data, dict) else data
    EXISTING_IDS = {q["id"] for q in questions}
    logger.info(f"Loaded {len(EXISTING_IDS)} existing question IDs")


def slugify(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s-]+", "-", s)
    if s in EXISTING_IDS:
        counter = 2
        while f"{s}-{counter}" in EXISTING_IDS:
            counter += 1
        s = f"{s}-{counter}"
    return s


def build_prompt(topic: str, difficulty: str, count: int) -> str:
    return f"""Generate {count} coding interview questions about "{topic}" at "{difficulty}" difficulty.
Return a JSON array. Each question must have these exact fields:
  - title: string
  - difficulty: "{difficulty}"
  - category: "{topic}"
  - company_tags: array of strings (real companies that ask this)
  - description: detailed problem description (2-3 paragraphs)
  - examples: array of {{"input": string, "output": string, "explanation": string}}
  - test_cases: array of {{"input": string, "expected_output": string, "description": string, "hidden": bool}} (include 2 hidden test cases)
  - starter: {{"python": string, "javascript": string, "java": string}} (function signature only, no body)
  - hints: array of 2-3 hint strings
  - solution: explanation of optimal solution
  - time_complexity: string like "O(n)"
  - space_complexity: string like "O(1)"
  - constraints: array of constraint strings

Return ONLY the JSON array, no other text."""


def call_nvidia(prompt: str, api_key: str, model: str) -> Optional[str]:
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
                "content": "You are a coding question generator. Return ONLY valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 4000,
        "temperature": 0.7,
        "top_p": 0.9,
        "stream": False,
    }

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
        if response.status_code != 200:
            logger.error(f"API error {response.status_code}: {response.text[:200]}")
            return None
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Request failed: {e}")
        return None


def parse_questions(raw: str) -> List[dict]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                logger.error("Could not parse JSON from response")
                return []
        else:
            logger.error("No JSON array found in response")
            return []

    if not isinstance(data, list):
        data = [data]

    validated = []
    for q in data:
        if not isinstance(q, dict) or "title" not in q or "description" not in q:
            logger.warning(f"Skipping malformed question: {q.get('title', 'unknown')}")
            continue
        q["id"] = slugify(q["title"])
        q.setdefault("company_tags", [])
        q.setdefault("examples", [])
        q.setdefault("test_cases", [])
        q.setdefault("hints", [])
        q.setdefault("constraints", [])
        q.setdefault("solution", None)
        q.setdefault("time_complexity", None)
        q.setdefault("space_complexity", None)
        if "starter" not in q or not isinstance(q["starter"], dict):
            q["starter"] = {
                "python": f"def {q['id'].replace('-', '_')}():\n    pass",
                "javascript": f"function {q['id'].replace('-', '_')}() {{}}",
                "java": f"class Solution {{\n    public void {q['id'].replace('-', '_')}() {{}}\n}}",
            }
        EXISTING_IDS.add(q["id"])
        validated.append(q)

    return validated


def save_questions(questions: List[dict]):
    if not os.path.exists(QUESTIONS_FILE):
        existing = []
    else:
        with open(QUESTIONS_FILE, "r") as f:
            existing = json.load(f)
    if isinstance(existing, dict):
        existing = existing.get("questions", existing)

    existing.extend(questions)

    with open(QUESTIONS_FILE, "w") as f:
        json.dump(existing, f, indent=2)
    logger.info(f"Saved {len(questions)} questions to {QUESTIONS_FILE}")


def generate_questions(
    api_key: str,
    model: str = "meta/llama-3.1-8b-instruct",
    target: int = 90,
    questions_per_topic: int = 6,
) -> List[dict]:
    load_existing_ids()

    all_questions = []
    total = 0

    for topic in TOPICS:
        for difficulty in ["easy", "medium", "hard"]:
            if total >= target:
                break

            remaining = target - total
            per_diff = min(questions_per_topic, remaining)

            logger.info(
                f"\n=== Generating {per_diff} {difficulty} questions: {topic} ==="
            )
            prompt = build_prompt(topic, difficulty, per_diff)
            raw = call_nvidia(prompt, api_key, model)
            if not raw:
                logger.warning(f"Failed to generate for {topic}/{difficulty}, skipping")
                continue

            questions = parse_questions(raw)
            if not questions:
                logger.warning(f"No valid questions parsed for {topic}/{difficulty}")
                continue

            all_questions.extend(questions)
            total += len(questions)
            logger.info(
                f"Generated {len(questions)} valid questions (total: {total}/{target})"
            )

        if total >= target:
            break

    return all_questions


def main(args_list: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(
        description="Generate coding questions using NVIDIA NIM"
    )
    parser.add_argument(
        "--api-key", help="NVIDIA API key (default: NVIDIA_API_KEY env var)"
    )
    parser.add_argument(
        "--model", default="meta/llama-3.1-8b-instruct", help="NVIDIA model"
    )
    parser.add_argument(
        "--questions-per-topic", type=int, default=6, help="Questions per topic"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print questions without saving"
    )
    args = parser.parse_args(args_list)

    api_key = args.api_key or os.getenv("NVIDIA_API_KEY")
    if not api_key:
        logger.error("NVIDIA_API_KEY not set. Use --api-key or set env var.")
        sys.exit(1)

    all_questions = generate_questions(
        api_key, args.model, questions_per_topic=args.questions_per_topic
    )

    if not all_questions:
        logger.error("No questions generated!")
        sys.exit(1)

    logger.info(f"\n=== Generated {len(all_questions)} questions total ===")

    if args.dry_run:
        print(json.dumps(all_questions, indent=2))
    else:
        save_questions(all_questions)
        logger.info("Done!")


if __name__ == "__main__":
    main()
