import os
import sys
import json
import re
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

VERIFICATION_CRITERIA = [
    "clarity",
    "correctness",
    "pedagogical_value",
]

LESSONS_FILE = os.path.join(
    os.path.dirname(__file__), "..", "data", "lessons.json"
)

REJECTED_FILE = os.path.join(
    os.path.dirname(__file__), "..", "data", "rejected_lessons.json"
)


def build_verification_prompt(lesson: dict) -> str:
    test_cases_str = json.dumps(lesson.get("test_cases", []), indent=2)

    return f"""You are a strict QA reviewer for programming lessons. Your job is to critically evaluate each lesson and identify any issues. Be harsh — a score of 100 means perfect, 80 means good but has minor issues, 60 means major issues, below 40 means fundamentally broken.

Lesson to evaluate:
---
Title: {lesson.get("title", "")}
Type: {lesson.get("type", "")}
Language: {lesson.get("language", "")}
Content:
{lesson.get("content", "")}
Starter Code: {lesson.get("starter_code", "N/A")}
Test Cases:
{test_cases_str}
---

Rate each criterion on a scale of 0-100:
- clarity: Is the lesson content clear, well-structured, and appropriate for beginners? Are the explanations easy to follow?
- correctness: Are the code examples, explanations, and test cases correct? Are there any technical errors or misleading statements?
- pedagogical_value: Does the lesson effectively teach the intended concept? Are the exercises well-designed for learning? Is the difficulty appropriate?

Return ONLY a JSON object with no other text:
{{
  "criteria_scores": {{
    "clarity": <int 0-100>,
    "correctness": <int 0-100>,
    "pedagogical_value": <int 0-100>
  }},
  "overall": <int 0-100>,
  "issues": <list of strings describing any problems found>
}}"""


def _json_loads_lenient(text: str):
    decoder = json.JSONDecoder(strict=False)
    try:
        return decoder.decode(text)
    except json.JSONDecodeError:
        return None


def parse_verification_response(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    data = _json_loads_lenient(text)
    if data is None:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            data = _json_loads_lenient(match.group(0))
        if data is None:
            return {
                "overall": 0,
                "criteria_scores": {},
                "issues": ["Failed to parse AI response"],
            }

    criteria_scores = data.get("criteria_scores", {})
    for criterion in VERIFICATION_CRITERIA:
        if criterion not in criteria_scores:
            criteria_scores[criterion] = 0

    overall = data.get("overall")
    if overall is None:
        scores = [v for v in criteria_scores.values() if isinstance(v, (int, float))]
        overall = round(sum(scores) / len(scores)) if scores else 0

    return {
        "overall": overall,
        "criteria_scores": criteria_scores,
        "issues": data.get("issues", []),
    }


def compute_average_score(rounds: list) -> float:
    if not rounds:
        return 0.0
    scores = [
        r["overall"] for r in rounds if isinstance(r.get("overall"), (int, float))
    ]
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def filter_lessons_by_score(
    lessons: list, threshold: float = 80
) -> tuple:
    passed = []
    rejected = []
    for lesson in lessons:
        score = lesson.get("_score", 0)
        if score > threshold:
            passed.append(lesson)
        else:
            rejected.append(lesson)
    return passed, rejected


def evaluate_lesson_quality(
    lesson: dict,
    call_nvidia_fn,
    api_key: str,
    model: str,
    rounds: int = 3,
) -> tuple:
    round_results = []
    for r in range(rounds):
        prompt = build_verification_prompt(lesson)
        raw = call_nvidia_fn(prompt, api_key, model)
        if not raw:
            continue
        result = parse_verification_response(raw)
        round_results.append(result)

    score = compute_average_score(round_results)
    return score, round_results


def call_nvidia(prompt: str, api_key: str, model: str):
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
                "content": "You are a strict QA reviewer for programming lessons. Return ONLY valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 2000,
        "temperature": 0.3,
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


def load_lessons(filepath: str) -> list:
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data.get("items", [])
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, IOError):
        return []


def save_lessons(filepath: str, lessons: list):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({"items": lessons}, f, indent=2)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Verify and populate programming lessons with AI quality gate"
    )
    parser.add_argument("--api-key", help="NVIDIA API key (default: NVIDIA_API_KEY env var)")
    parser.add_argument("--model", default="meta/llama-3.1-8b-instruct", help="NVIDIA model")
    parser.add_argument("--threshold", type=float, default=80, help="Minimum average score (default: 80)")
    parser.add_argument("--rounds", type=int, default=3, help="Number of verification rounds per lesson (default: 3)")
    parser.add_argument("--dry-run", action="store_true", help="Print results without saving")
    parser.add_argument("--input", help="Input JSON file with generated lessons (default: data/lessons.json)")
    args = parser.parse_args()

    api_key = args.api_key or os.getenv("NVIDIA_API_KEY")
    if not api_key:
        logger.error("NVIDIA_API_KEY not set. Use --api-key or set env var.")
        sys.exit(1)

    input_path = args.input or LESSONS_FILE
    lessons = load_lessons(input_path)
    if not lessons:
        logger.error(f"No lessons found in {input_path}")
        sys.exit(1)

    unverified = [l for l in lessons if not l.get("verified", False)]
    if not unverified:
        logger.info("All lessons are already verified!")
        return

    logger.info(f"\n=== Verifying {len(unverified)} lessons ({args.rounds} rounds each) ===")
    logger.info(f"Threshold: > {args.threshold}")

    verified = []
    total = len(unverified)

    for i, lesson in enumerate(unverified, 1):
        title = lesson.get("title", "unknown")
        logger.info(f"\n[{i}/{total}] Evaluating: {title}")

        score, rounds = evaluate_lesson_quality(
            lesson, call_nvidia, api_key, args.model, rounds=args.rounds
        )
        lesson["_score"] = score
        lesson["_rounds"] = rounds

        scores_str = ", ".join(str(r.get("overall", 0)) for r in rounds)
        logger.info(f"  Scores: [{scores_str}] | Average: {score:.1f}")
        verified.append(lesson)

    passed, rejected = filter_lessons_by_score(verified, threshold=args.threshold)

    logger.info("\n=== Results ===")
    logger.info(f"Passed (> {args.threshold}): {len(passed)}/{total}")
    logger.info(f"Rejected: {len(rejected)}/{total}")
    if rejected:
        logger.info("\nRejected lessons:")
        for l in rejected:
            logger.info(f"  - {l.get('title', 'unknown')} (score: {l.get('_score', 0):.1f})")

    if args.dry_run:
        logger.info(f"\nDry run — would mark {len(passed)} lessons as verified in {LESSONS_FILE}")
        return

    for lesson in passed:
        lesson["verified"] = True
        lesson.pop("_score", None)
        lesson.pop("_rounds", None)

    for lesson in rejected:
        lesson.pop("_score", None)
        lesson.pop("_rounds", None)

    all_lessons = load_lessons(input_path)
    updated = []
    for lesson in all_lessons:
        lid = lesson.get("id")
        passed_ids = {l["id"] for l in passed}
        if lid in passed_ids:
            updated_lesson = {k: v for k, v in lesson.items() if k not in ("verified",)}
            updated_lesson["verified"] = True
            updated.append(updated_lesson)
        else:
            updated.append(lesson)

    save_lessons(LESSONS_FILE, updated)
    logger.info(f"Saved {len(updated)} lessons to {LESSONS_FILE}")

    if rejected:
        os.makedirs(os.path.dirname(REJECTED_FILE) or ".", exist_ok=True)
        with open(REJECTED_FILE, "w", encoding="utf-8") as f:
            json.dump({"rejected": rejected, "threshold": args.threshold}, f, indent=2)
        logger.info(f"Saved {len(rejected)} rejected lessons to {REJECTED_FILE}")

    logger.info("\nDone!")


if __name__ == "__main__":
    main()
