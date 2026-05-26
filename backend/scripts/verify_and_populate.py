import os
import sys
import json
import re
import logging
import argparse
from typing import List, Optional, Callable, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

VERIFICATION_CRITERIA = [
    "test_cases",
    "test_case_coverage",
    "description",
    "difficulty",
    "category",
    "starter_code",
    "solution",
    "hints",
    "constraints",
    "thematic_coherence",
    "boundary_edge_cases",
]

QUESTIONS_FILE = os.path.join(
    os.path.dirname(__file__), "..", "questions", "sample_questions.json"
)

REJECTED_FILE = os.path.join(
    os.path.dirname(__file__), "..", "questions", "rejected_questions.json"
)


def build_verification_prompt(question: dict) -> str:
    criteria_descriptions = {
        "test_cases": "Do the test case expected outputs match the problem description? Are there any contradictions or incorrect expected outputs?",
        "test_case_coverage": "Does the question have at least 12 test cases covering edge cases, normal cases, boundary conditions, and hidden validation cases? Are the test cases structurally diverse rather than repeated with trivial differences?",
        "description": "Is the problem statement clear, unambiguous, and complete? Does it include all necessary context?",
        "difficulty": "Is the difficulty rating (easy/medium/hard) appropriate given the problem complexity?",
        "category": "Does this problem belong in the stated DSA category? Is the categorization correct?",
        "starter_code": "Are the function signatures correct, idiomatic, and consistent across all three languages (Python, JavaScript, Java)?",
        "solution": "Does the provided solution approach correctly solve the problem? Is the algorithm sound?",
        "hints": "Are the hints helpful and progressive without revealing the full solution? Do they guide rather than give away?",
        "constraints": "Are the input constraints realistic, reasonable, and useful for bounding the solution space?",
        "thematic_coherence": "If the question uses a real-world scenario (e.g. LLM context windows, drone routing, GPU scheduling), does the scenario make logical sense? Are the technical details accurate and consistent with the algorithmic requirements? Do the examples and test cases align with the scenario framing?",
        "boundary_edge_cases": "Do the test cases thoroughly cover maximum constraint boundaries (e.g. n=10^5, extreme values, overflow conditions)? Are there tests for empty input, single-element input, and worst-case scenarios? Do the hidden test cases stress-test time/space complexity assumptions?",
    }

    test_cases_str = json.dumps(question.get("test_cases", []), indent=2)
    examples_str = json.dumps(question.get("examples", []), indent=2)

    return f"""You are a strict QA reviewer for coding interview questions. Your job is to critically evaluate each question and identify any issues. Be harsh — a score of 100 means perfect, 80 means good but has minor issues, 60 means major issues, below 40 means fundamentally broken.

Question to evaluate:
---
Title: {question.get("title", "")}
Difficulty: {question.get("difficulty", "")}
Category: {question.get("category", "")}
Description: {question.get("description", "")}

Examples:
{examples_str}

Test Cases:
{test_cases_str}

Hints: {json.dumps(question.get("hints", []))}
Solution: {question.get("solution", "")}
Time Complexity: {question.get("time_complexity", "")}
Space Complexity: {question.get("space_complexity", "")}
Constraints: {json.dumps(question.get("constraints", []))}
---

Rate each criterion on a scale of 0-100:
{chr(10).join(f"- {k}: {v}" for k, v in criteria_descriptions.items())}

Return ONLY a JSON object with no other text:
{{
  "criteria_scores": {{
    "test_cases": <int 0-100>,
    "test_case_coverage": <int 0-100>,
    "description": <int 0-100>,
    "difficulty": <int 0-100>,
    "category": <int 0-100>,
    "starter_code": <int 0-100>,
    "solution": <int 0-100>,
    "hints": <int 0-100>,
    "constraints": <int 0-100>,
    "thematic_coherence": <int 0-100>,
    "boundary_edge_cases": <int 0-100>
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


def compute_average_score(rounds: List[dict]) -> float:
    if not rounds:
        return 0.0
    scores = [
        r["overall"] for r in rounds if isinstance(r.get("overall"), (int, float))
    ]
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def filter_questions_by_score(
    questions: List[dict], threshold: float = 90
) -> Tuple[List[dict], List[dict]]:
    passed = []
    rejected = []
    for q in questions:
        score = q.get("_score", 0)
        if score > threshold:
            passed.append(q)
        else:
            rejected.append(q)
    return passed, rejected


def merge_with_existing(existing: List[dict], new: List[dict]) -> List[dict]:
    existing_ids = {q["id"] for q in existing if "id" in q}
    merged = list(existing)

    for q in new:
        qid = q.get("id", "")
        if qid in existing_ids:
            counter = 2
            while f"{qid}-{counter}" in existing_ids:
                counter += 1
            q["id"] = f"{qid}-{counter}"
            existing_ids.add(q["id"])
        else:
            existing_ids.add(qid)
        merged.append(q)

    return merged


def load_existing_questions(filepath: str) -> List[dict]:
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data.get("questions", [])
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, IOError):
        return []


def save_questions(filepath: str, questions: List[dict]):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({"questions": questions}, f, indent=2)


def evaluate_question_quality(
    question: dict,
    call_nvidia_fn: Callable,
    api_key: str,
    model: str,
    rounds: int = 4,
) -> Tuple[float, List[dict]]:
    round_results = []
    for r in range(rounds):
        prompt = build_verification_prompt(question)
        raw = call_nvidia_fn(prompt, api_key, model)
        if not raw:
            logger.warning(f"  Round {r + 1}/{rounds}: API call failed, skipping")
            continue
        result = parse_verification_response(raw)
        round_results.append(result)

    score = compute_average_score(round_results)
    return score, round_results


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
                "content": "You are a strict QA reviewer for coding interview questions. Return ONLY valid JSON.",
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


def export_prompts(questions: List[dict], output_path: str, rounds: int = 4):
    entries = []
    for i, q in enumerate(questions, 1):
        prompt = build_verification_prompt(q)
        entry = {
            "index": i,
            "title": q.get("title", "unknown"),
            "difficulty": q.get("difficulty", ""),
            "category": q.get("category", ""),
            "prompt": prompt,
            "score": None,
            "round_scores": [None] * rounds,
            "issues": None,
            "question_data": q,
        }
        entries.append(entry)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)
    logger.info(f"Exported {len(entries)} prompts to {output_path}")


def import_scores(
    input_path: str, threshold: float = 90
) -> Tuple[List[dict], List[dict]]:
    with open(input_path, "r", encoding="utf-8") as f:
        entries = json.load(f)

    passed = []
    rejected = []

    for entry in entries:
        score = entry.get("score")
        question_data = entry.get("question_data")
        if not question_data:
            rejected.append(
                {
                    "title": entry.get("title", "unknown"),
                    "_score": 0,
                    "_issues": ["Missing question_data in export"],
                }
            )
            continue

        q = dict(question_data)
        q["_score"] = score if score is not None else 0
        q["_rounds"] = entry.get("round_scores", [])
        q["_issues"] = entry.get("issues", [])

        if score is not None and score > threshold:
            passed.append(q)
        else:
            rejected.append(q)

    return passed, rejected


def export_prompts_only(args):
    questions = (
        load_existing_questions(args.input)
        if args.input
        else load_existing_questions(QUESTIONS_FILE)
    )
    if not questions:
        logger.error("No questions to export!")
        sys.exit(1)
    output = args.export_prompts
    export_prompts(questions, output, rounds=args.rounds)


def import_scores_only(args):
    passed, rejected = import_scores(args.import_scores, threshold=args.threshold)
    logger.info(f"Imported: {len(passed)} passed, {len(rejected)} rejected")

    existing = load_existing_questions(QUESTIONS_FILE)
    logger.info(f"Existing questions in bank: {len(existing)}")

    for q in passed:
        q.pop("_score", None)
        q.pop("_rounds", None)
        q.pop("_issues", None)

    merged = merge_with_existing(existing, passed)
    save_questions(QUESTIONS_FILE, merged)
    logger.info(f"Saved {len(merged)} questions to {QUESTIONS_FILE}")

    if rejected:
        rejected_dir = os.path.dirname(REJECTED_FILE)
        os.makedirs(rejected_dir, exist_ok=True)
        with open(REJECTED_FILE, "w", encoding="utf-8") as f:
            json.dump({"rejected": rejected, "threshold": args.threshold}, f, indent=2)
        logger.info(f"Saved {len(rejected)} rejected questions to {REJECTED_FILE}")


def main():
    parser = argparse.ArgumentParser(
        description="Verify and populate coding questions with AI quality gate"
    )
    parser.add_argument(
        "--api-key", help="NVIDIA API key (default: NVIDIA_API_KEY env var)"
    )
    parser.add_argument(
        "--model", default="meta/llama-3.1-8b-instruct", help="NVIDIA model"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=90,
        help="Minimum average score (default: 90)",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=4,
        help="Number of verification rounds per question (default: 4)",
    )
    parser.add_argument(
        "--input",
        help="Input JSON file with generated questions (if not provided, uses generate_questions.py)",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate questions first using generate_questions.py",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print results without saving"
    )
    parser.add_argument(
        "--export-prompts",
        help="Export verification prompts to a JSON file (no API calls) and exit",
    )
    parser.add_argument(
        "--import-scores",
        help="Import scored prompts JSON file, filter by threshold, and populate",
    )
    args = parser.parse_args()

    if args.export_prompts:
        export_prompts_only(args)
        return

    if args.import_scores:
        import_scores_only(args)
        return

    api_key = args.api_key or os.getenv("NVIDIA_API_KEY")
    if not api_key:
        logger.error("NVIDIA_API_KEY not set. Use --api-key or set env var.")
        sys.exit(1)

    questions = []

    if args.generate:
        logger.info("Generating questions...")
        from scripts.generate_questions import generate_questions as gen_core

        generated = gen_core(api_key, args.model)
        if not generated:
            logger.error("No questions generated!")
            sys.exit(1)
        logger.info(f"Generated {len(generated)} new questions")
        new_questions = generated
    elif args.input:
        questions = load_existing_questions(args.input)
        logger.info(f"Loaded {len(questions)} questions from {args.input}")
        new_questions = questions
    else:
        logger.info("Loading existing questions from bank for re-verification...")
        questions = load_existing_questions(QUESTIONS_FILE)
        logger.info(f"Loaded {len(questions)} existing questions")
        new_questions = questions

    if not new_questions:
        logger.error("No questions to verify!")
        sys.exit(1)

    logger.info(
        f"\n=== Verifying {len(new_questions)} questions ({args.rounds} rounds each) ==="
    )
    logger.info(f"Threshold: > {args.threshold}")

    verified = []
    total = len(new_questions)

    for i, q in enumerate(new_questions, 1):
        title = q.get("title", "unknown")
        logger.info(f"\n[{i}/{total}] Evaluating: {title}")

        score, rounds = evaluate_question_quality(
            q, call_nvidia, api_key, args.model, rounds=args.rounds
        )
        q["_score"] = score
        q["_rounds"] = rounds

        scores_str = ", ".join(str(r.get("overall", 0)) for r in rounds)
        logger.info(f"  Scores: [{scores_str}] | Average: {score:.1f}")
        verified.append(q)

        if i % 10 == 0:
            logger.info(f"\n--- Checkpoint: {i}/{total} evaluated ---")

    passed, rejected = filter_questions_by_score(verified, threshold=args.threshold)

    logger.info("\n=== Results ===")
    logger.info(f"Passed (> {args.threshold}): {len(passed)}/{total}")
    logger.info(f"Rejected: {len(rejected)}/{total}")
    if rejected:
        logger.info("\nRejected questions:")
        for q in rejected:
            logger.info(
                f"  - {q.get('title', 'unknown')} (score: {q.get('_score', 0):.1f})"
            )

    if args.dry_run:
        logger.info(
            f"\nDry run — would save {len(passed)} questions to {QUESTIONS_FILE}"
        )
        if passed:
            logger.info("\nPassed questions preview:")
            for q in passed:
                logger.info(
                    f"  - {q.get('title', 'unknown')} (score: {q.get('_score', 0):.1f})"
                )
        return

    existing = load_existing_questions(QUESTIONS_FILE)
    logger.info(f"\nExisting questions in bank: {len(existing)}")

    for q in passed:
        q.pop("_score", None)
        q.pop("_rounds", None)

    merged = merge_with_existing(existing, passed)

    save_questions(QUESTIONS_FILE, merged)
    logger.info(f"Saved {len(merged)} questions to {QUESTIONS_FILE}")

    if rejected:
        rejected_dir = os.path.dirname(REJECTED_FILE)
        os.makedirs(rejected_dir, exist_ok=True)
        with open(REJECTED_FILE, "w", encoding="utf-8") as f:
            json.dump({"rejected": rejected, "threshold": args.threshold}, f, indent=2)
        logger.info(f"Saved {len(rejected)} rejected questions to {REJECTED_FILE}")

    logger.info("\nDone!")


if __name__ == "__main__":
    main()
