import os
import sys
import json
import re
import logging
import argparse
from typing import List, Optional, Tuple

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

ARCHETYPES = ["classic", "creative_2026"]

QUESTIONS_FILE = os.path.join(
    os.path.dirname(__file__), "..", "questions", "sample_questions.json"
)

EXISTING_IDS: set = set()

SCENARIO_SEEDS = {
    "Arrays & Hashing": (
        "FRAME THE PROBLEM AS: A real-time fraud detection system processing millions of "
        "credit card transactions per second must identify suspicious patterns. "
        "The data streams in as arrays of transaction records and the system must hash "
        "and compare against known fraud signatures in O(n) time."
    ),
    "Two Pointers": (
        "FRAME THE PROBLEM AS: A real-time collaborative AR editing application (used for "
        "architectural planning in smart city projects) uses CRDTs to merge concurrent edits. "
        "Two engineers edit the same spatial model simultaneously — the system must reconcile "
        "conflicting state vectors using a two-pointer merge to produce a consistent view."
    ),
    "Sliding Window": (
        "FRAME THE PROBLEM AS: Your AI startup deploys an LLM chatbot that must stay within a "
        "fixed context window of 4096 tokens. The conversation history is streaming in — you need "
        "to find the optimal sliding subsequence of previous turns that maximizes relevance signals "
        "while fitting inside the context budget."
    ),
    "Stack": (
        "FRAME THE PROBLEM AS: A next-gen WebAssembly runtime needs to validate nested "
        "control-flow blocks (loops, if-else, try-catch) in a new Systems Programming Language. "
        "The parser emits tokens in sequence — use a stack to ensure every opening construct "
        "has a matching close in the correct order."
    ),
    "Binary Search": (
        "FRAME THE PROBLEM AS: An autonomous delivery vehicle uses LIDAR point clouds to "
        "navigate. Its onboard obstacle detection returns a sorted array of distances. "
        "The vehicle must find the closest obstacle within a given angular sector — "
        "use binary search to locate the nearest hazard in O(log n) time so the braking "
        "system can react before the next sensor tick."
    ),
    "Linked List": (
        "FRAME THE PROBLEM AS: A lightweight blockchain ledger for IoT sensor data stores "
        "transactions as a linked list of blocks. Each block points to the previous hash. "
        "A network audit tool needs to detect loops (fork attacks) in the chain and find the "
        "point of divergence between two competing chains."
    ),
    "Trees": (
        "FRAME THE PROBLEM AS: A streaming service&apos;s content recommendation engine organizes "
        "genre categories in a tree structure. When a user watches a video, the system must "
        "traverse the category tree to find all related sub-genres and surface personalized "
        "recommendations within milliseconds."
    ),
    "Tries": (
        "FRAME THE PROBLEM AS: A mobile keyboard&apos;s next-word prediction engine needs to "
        "support real-time autocomplete with fuzzy prefix matching. The model loads a trie "
        "of the top 100k English words (weighted by usage frequency). As the user types each "
        "character, return the top-3 most likely completions in O(k) time."
    ),
    "Heap / Priority Queue": (
        "FRAME THE PROBLEM AS: A distributed GPU cluster for training large language models "
        "receives training jobs with varying priority levels and GPU-hour requirements. "
        "The cluster scheduler must always run the highest-priority job that fits remaining "
        "capacity. Manage the job queue with a priority queue and handle job preemption."
    ),
    "Backtracking": (
        "FRAME THE PROBLEM AS: An AI-powered travel planner for a 2026 Mars colonization "
        "program must generate all feasible mission schedules given constraints: crew "
        "availability, supply windows, fuel budgets, and planetary alignment. Use backtracking "
        "to enumerate valid schedules and prune branches that violate constraints."
    ),
    "Graphs": (
        "FRAME THE PROBLEM AS: A drone delivery network serving a smart city must route "
        "packages through dynamic no-fly zones (temporary airspace restrictions from events, "
        "emergencies, or weather). Each drone has a battery range. Find the shortest obstacle-avoiding "
        "path between two delivery hubs, updating when new no-fly zones are published."
    ),
    "Dynamic Programming": (
        "FRAME THE PROBLEM AS: A smart city&apos;s solar-plus-battery energy grid must decide "
        "how much energy to store vs sell at each hour over the next 48 hours. Solar generation "
        "forecast, real-time pricing, and battery degradation are known. Use DP to maximize "
        "revenue while keeping the battery within safe charge levels."
    ),
    "Greedy": (
        "FRAME THE PROBLEM AS: A last-mile logistics startup uses gig-economy couriers who "
        "accept delivery routes greedily. Each courier can carry up to a weight limit. "
        "Packages arrive with deadlines and penalties for late delivery. Schedule the most "
        "valuable subset of packages that can be delivered on time, using a greedy approach."
    ),
    "Intervals": (
        "FRAME THE PROBLEM AS: A hybrid-work office booking system manages hot-desk reservations. "
        "Employees book desks in time intervals. The system must detect overlaps, merge adjacent "
        "bookings by the same person, and report the busiest time blocks each day."
    ),
}


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


def build_classic_prompt(topic: str, difficulty: str, count: int) -> str:
    return f"""Generate {count} classic coding interview questions about "{topic}" at "{difficulty}" difficulty.

Each question must be a pure algorithmic problem framed as a traditional technical interview question (like LeetCode or HackerRank). Focus on the data structure and algorithm — no elaborate story, just the problem.

Return a JSON array. Each question must have these exact fields:
  - title: string (concise, like "Two Sum" or "Maximum Subarray")
  - difficulty: "{difficulty}"
  - category: "{topic}"
  - company_tags: array of strings (real companies that ask this)
  - description: detailed problem description (2-3 paragraphs with input/output format, constraints, and edge cases)
  - examples: array of {{"input": string, "output": string, "explanation": string}} (2-3 examples covering edge cases)
  - test_cases: array of EXACTLY 20 objects with {{"input": string, "expected_output": string, "description": string, "hidden": bool}}
    - 5 edge cases (empty input, single element, max bounds, negative values, duplicates)
    - 5 standard cases (typical inputs)
    - 10 hidden validation cases (marked "hidden": true)
  - starter: {{"python": string, "javascript": string, "java": string}} (function signature with correct types, no body)
    Use "def <function_name>(<args>):\\n    pass" for Python
    Use "function <functionName>(<args>) {{\\n    \\n}}" for JavaScript
    Use "public class Solution {{\\n    public <return_type> <methodName>(<args>) {{\\n        return <default>;\\n    }}\\n}}" for Java
  - hints: array of 3 hint strings (progressive: gentle → specific → near-spoiler)
  - solution: detailed explanation of the optimal solution approach
  - time_complexity: string like "O(n)"
  - space_complexity: string like "O(1)"
  - constraints: array of 4-6 constraint strings covering input bounds

IMPORTANT: You MUST include EXACTLY 20 test cases (5 edge + 5 standard + 10 hidden) with correct expected_output values matching the problem description. The test case descriptions must be detailed strings like "Large input — 10^5 elements with negative values".

Return ONLY the JSON array, no other text."""


def build_creative_prompt(topic: str, difficulty: str, count: int) -> str:
    scenario = SCENARIO_SEEDS.get(topic, "Frame this as a modern real-world software engineering problem.")

    return f"""Generate {count} creative real-world coding interview questions about "{topic}" at "{difficulty}" difficulty.

Each question must wrap the DSA concept in a believable 2025/2026 real-world scenario. The scenario should be specific, modern, and technically accurate — not generic or forced.

SCENARIO FRAMING INSTRUCTION:
{scenario}

The problem should still be solvable with standard DSA techniques — the scenario is the packaging, not the core algorithm.

Return a JSON array. Each question must have these exact fields:
  - title: string (descriptive, reflecting the real-world context, e.g. "LLM Context Window Optimizer")
  - difficulty: "{difficulty}"
  - category: "{topic}"
  - company_tags: array of strings (real companies or startup sectors relevant to this scenario)
  - description: detailed problem description (3-4 paragraphs — first paragraph sets up the real-world scenario, second explains the technical challenge, third specifies the exact function signature and I/O format, fourth notes edge cases)
  - examples: array of {{"input": string, "output": string, "explanation": string}} (2-3 examples that both explain the scenario context and the algorithm)
  - test_cases: array of EXACTLY 20 objects with {{"input": string, "expected_output": string, "description": string, "hidden": bool}}
    - 5 edge cases (empty, single, max bounds, extreme values, error conditions)
    - 5 standard cases (typical real-world inputs)
    - 10 hidden validation cases (marked "hidden": true) that test boundary conditions and large-scale inputs
  - starter: {{"python": string, "javascript": string, "java": string}} (function signature with scenario-appropriate naming, no body)
    Use "def <function_name>(<args>):\\n    pass" for Python
    Use "function <functionName>(<args>) {{\\n    \\n}}" for JavaScript
    Use "public class Solution {{\\n    public <return_type> <methodName>(<args>) {{\\n        return <default>;\\n    }}\\n}}" for Java
  - hints: array of 3 hint strings (contextual hints that tie back to the scenario)
  - solution: explanation of optimal solution, mentioning both the DSA technique AND how it maps to the real-world scenario
  - time_complexity: string like "O(n log n)"
  - space_complexity: string like "O(n)"
  - constraints: array of 4-6 strings describing realistic bounds

IMPORTANT: You MUST include EXACTLY 20 test cases (5 edge + 5 standard + 10 hidden) with correct expected_output values matching the problem description. The test case descriptions must reference the scenario context.

Return ONLY the JSON array, no other text."""


def build_prompt(topic: str, difficulty: str, count: int, archetype: str = "classic") -> str:
    if archetype == "creative_2026":
        return build_creative_prompt(topic, difficulty, count)
    return build_classic_prompt(topic, difficulty, count)


def call_nvidia_with_retry(
    prompt: str, api_key: str, model: str, max_retries: int = 3
) -> Optional[str]:
    import httpx

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    for attempt in range(1, max_retries + 1):
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
                logger.error(f"  API error {response.status_code} on attempt {attempt}")
                if attempt < max_retries:
                    continue
                return None

            raw = response.json()["choices"][0]["message"]["content"]

            parsed = parse_questions(raw)
            if not parsed:
                parse_error = "JSON parse failed or empty array returned"
                logger.warning(f"  {parse_error} on attempt {attempt}")
                if attempt < max_retries:
                    prompt = prompt + (
                        f"\n\nYour previous response was not valid JSON or did not contain valid questions. "
                        f"ERROR: {parse_error}. Please return ONLY a valid JSON array following the exact format specified above."
                    )
                    continue
                return raw

            return raw

        except (json.JSONDecodeError, httpx.RequestError, KeyError) as e:
            logger.warning(f"  Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                prompt = prompt + (
                    f"\n\nYour previous response caused an error: {e}. "
                    f"Please return ONLY a valid JSON array. No markdown, no code fences, no extra text."
                )
                continue
            return None

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

        tc_count = len(q.get("test_cases", []))
        if tc_count < 20:
            logger.warning(
                f"  Question '{q['title']}' has only {tc_count} test cases (want 20)"
            )

        if "starter" not in q or not isinstance(q["starter"], dict):
            q["starter"] = {
                "python": f"def {q['id'].replace('-', '_')}():\n    pass",
                "javascript": f"function {q['id'].replace('-', '_')}() {{}}",
                "java": f"class Solution {{\n    public void {q['id'].replace('-', '_')}() {{}}\n}}",
            }
        else:
            for lang in ["python", "javascript", "java"]:
                if lang not in q["starter"]:
                    q["starter"][lang] = _default_starter(q["id"], lang)

        EXISTING_IDS.add(q["id"])
        validated.append(q)

    return validated


def _default_starter(qid: str, lang: str) -> str:
    name = qid.replace("-", "_")
    camel = re.sub(r"[-_]([a-z])", lambda m: m.group(1).upper(), f"x_{qid}").replace("x_", "")
    if lang == "python":
        return f"def {name}():\n    pass"
    elif lang == "javascript":
        return f"function {camel}() {{}}"
    else:
        return f"class Solution {{\n    public void {camel}() {{}}\n}}"


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
    archetype: str = "mixed",
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

            if archetype == "mixed":
                half = max(1, per_diff // 2)
                arch_pairs = [("classic", half), ("creative_2026", per_diff - half)]
            else:
                arch_pairs = [(archetype, per_diff)]

            for arch, count_for_arch in arch_pairs:
                if count_for_arch < 1 or total >= target:
                    continue

                label = f"{topic}/{difficulty}/{arch}"
                logger.info(f"\n=== Generating {count_for_arch} questions: {label} ===")

                prompt = build_prompt(topic, difficulty, count_for_arch, archetype=arch)
                raw = call_nvidia_with_retry(prompt, api_key, model)
                if not raw:
                    logger.warning(f"Failed to generate for {label}, skipping")
                    continue

                questions = parse_questions(raw)
                if not questions:
                    logger.warning(f"No valid questions parsed for {label}")
                    continue

                questions = questions[:count_for_arch]
                for q in questions:
                    q["_archetype"] = arch

                all_questions.extend(questions)
                total += len(questions)
                logger.info(f"  Generated {len(questions)} valid (total: {total}/{target})")

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
        "--archetype",
        choices=["classic", "creative_2026", "mixed"],
        default="mixed",
        help="Question archetype: classic, creative_2026, or mixed (default: mixed)",
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
        api_key,
        args.model,
        questions_per_topic=args.questions_per_topic,
        archetype=args.archetype,
    )

    if not all_questions:
        logger.error("No questions generated!")
        sys.exit(1)

    logger.info(f"\n=== Generated {len(all_questions)} questions total ===")

    archetype_counts = {}
    for q in all_questions:
        arch = q.get("_archetype", "unknown")
        archetype_counts[arch] = archetype_counts.get(arch, 0) + 1
    for arch, cnt in sorted(archetype_counts.items()):
        logger.info(f"  {arch}: {cnt}")

    if args.dry_run:
        for q in all_questions:
            q.pop("_archetype", None)
        print(json.dumps(all_questions, indent=2))
    else:
        for q in all_questions:
            q.pop("_archetype", None)
        save_questions(all_questions)
        logger.info("Done!")


if __name__ == "__main__":
    main()
