import os
import sys
import json
import re
import time
import asyncio
import logging
import argparse
import httpx
from typing import List, Optional, Tuple


class RateLimiter:
    def __init__(self, max_per_minute: int):
        self.min_interval = 60.0 / max_per_minute
        self.last_call = 0.0
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.monotonic()
            since_last = now - self.last_call
            if since_last < self.min_interval:
                await asyncio.sleep(self.min_interval - since_last)
            self.last_call = time.monotonic()

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

CHECKPOINT_FILE = os.path.join(
    os.path.dirname(__file__), "..", "questions", ".generation_checkpoint.json"
)

VALID_TOPICS_SET = frozenset(TOPICS)

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


def _difficulty_calibration_examples(difficulty: str) -> str:
    examples = {
        "easy": '''Easy example: "Two Sum" — given array [2,7,11,15] and target 9, return [0,1]. Simple O(n) hash map solution. 1-2 data structure concepts. Straightforward input/output mapping.''',
        "medium": '''Medium example: "Longest Substring Without Repeating Characters" — given "abcabcbb", return 3 ("abc"). Requires sliding window with hash set. Multiple edge cases (empty string, all repeats, all unique). Non-trivial but common pattern.''',
        "hard": '''Hard example: "Median of Two Sorted Arrays" — given [1,3] and [2], return 2.0. Requires O(log(min(n,m))) binary search partition. Complex edge cases — different sized arrays, negative values, duplicates. Multiple advanced concepts needed.''',
    }
    return examples.get(difficulty, examples["medium"])


def build_classic_prompt(topic: str, difficulty: str, count: int) -> str:
    calibration = _difficulty_calibration_examples(difficulty)
    return f"""Generate {count} classic coding interview questions about "{topic}" at "{difficulty}" difficulty.

Each question must be a pure algorithmic problem framed as a traditional technical interview question (like LeetCode or HackerRank). Focus on the data structure and algorithm — no elaborate story, just the problem.

CRITICAL RULE — category field MUST be exactly "{topic}". Do NOT use any other category name.

Calibration for "{difficulty}" difficulty:
{calibration}

Return a JSON array. Each question must have these exact fields:
  - title: string (concise, like "Two Sum" or "Maximum Subarray")
  - difficulty: "{difficulty}"
  - category: "{topic}"  (MUST be exactly this value)
  - company_tags: array of strings (real companies that ask this)
  - description: detailed problem description (2-3 paragraphs with input/output format, constraints, and edge cases)
  - examples: array of {{"input": string, "output": string, "explanation": string}} (2-3 examples covering edge cases)
  - test_cases: array of EXACTLY 12 objects with {{"input": string, "expected_output": string, "description": string, "hidden": bool}}
    - 3 edge cases (empty input, single element, max bounds, negative values, or duplicates)
    - 3 standard cases (typical inputs)
    - 6 hidden validation cases (marked "hidden": true, stress edge and boundary conditions)
  - starter: {{"python": string, "javascript": string, "java": string}} (function signature with correct types, no body)
    Use "def <function_name>(<args>):\\n    pass" for Python
    Use "function <functionName>(<args>) {{\\n    \\n}}" for JavaScript
    Use "public class Solution {{\\n    public <return_type> <methodName>(<args>) {{\\n        return <default>;\\n    }}\\n}}" for Java
  - hints: array of 3 hint strings (progressive: gentle → specific → near-spoiler)
  - solution: detailed explanation of the optimal solution approach
  - time_complexity: string like "O(n)"
  - space_complexity: string like "O(1)"
  - constraints: array of 4-6 constraint strings covering input bounds

IMPORTANT: You MUST include EXACTLY 12 test cases (3 edge + 3 standard + 6 hidden) with correct expected_output values matching the problem description. Each test case must be structurally distinct — do NOT repeat the same input format with trivial changes. The test case descriptions must be detailed strings like "Large input — 10^5 elements with negative values".

Return ONLY the JSON array, no other text."""


def build_creative_prompt(topic: str, difficulty: str, count: int) -> str:
    scenario = SCENARIO_SEEDS.get(topic, "Frame this as a modern real-world software engineering problem.")
    calibration = _difficulty_calibration_examples(difficulty)

    return f"""Generate {count} creative real-world coding interview questions about "{topic}" at "{difficulty}" difficulty.

Each question must wrap the DSA concept in a believable 2025/2026 real-world scenario. The scenario should be specific, modern, and technically accurate — not generic or forced.

SCENARIO FRAMING INSTRUCTION:
{scenario}

CRITICAL RULE — category field MUST be exactly "{topic}". Do NOT use any other category name.

Calibration for "{difficulty}" difficulty:
{calibration}

The problem should still be solvable with standard DSA techniques — the scenario is the packaging, not the core algorithm.

Return a JSON array. Each question must have these exact fields:
  - title: string (descriptive, reflecting the real-world context, e.g. "LLM Context Window Optimizer")
  - difficulty: "{difficulty}"
  - category: "{topic}"  (MUST be exactly this value)
  - company_tags: array of strings (real companies or startup sectors relevant to this scenario)
  - description: detailed problem description (3-4 paragraphs — first paragraph sets up the real-world scenario, second explains the technical challenge, third specifies the exact function signature and I/O format, fourth notes edge cases)
  - examples: array of {{"input": string, "output": string, "explanation": string}} (2-3 examples that both explain the scenario context and the algorithm)
  - test_cases: array of EXACTLY 12 objects with {{"input": string, "expected_output": string, "description": string, "hidden": bool}}
    - 3 edge cases (empty, single, max bounds, extreme values, or error conditions)
    - 3 standard cases (typical real-world inputs)
    - 6 hidden validation cases (marked "hidden": true, stress boundary and large-scale inputs)
  - starter: {{"python": string, "javascript": string, "java": string}} (function signature with scenario-appropriate naming, no body)
    Use "def <function_name>(<args>):\\n    pass" for Python
    Use "function <functionName>(<args>) {{\\n    \\n}}" for JavaScript
    Use "public class Solution {{\\n    public <return_type> <methodName>(<args>) {{\\n        return <default>;\\n    }}\\n}}" for Java
  - hints: array of 3 hint strings (contextual hints that tie back to the scenario)
  - solution: explanation of optimal solution, mentioning both the DSA technique AND how it maps to the real-world scenario
  - time_complexity: string like "O(n log n)"
  - space_complexity: string like "O(n)"
  - constraints: array of 4-6 strings describing realistic bounds

IMPORTANT: You MUST include EXACTLY 12 test cases (3 edge + 3 standard + 6 hidden) with correct expected_output values matching the problem description. Each test case must be structurally distinct — do NOT repeat the same input format with trivial changes. The test case descriptions must reference the scenario context.

Return ONLY the JSON array, no other text."""


def build_prompt(topic: str, difficulty: str, count: int, archetype: str = "classic") -> str:
    if archetype == "creative_2026":
        return build_creative_prompt(topic, difficulty, count)
    return build_classic_prompt(topic, difficulty, count)


def call_nvidia_with_retry(
    prompt: str, api_key: str, model: str, max_retries: int = 3
) -> Optional[str]:
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
            "max_tokens": 8192,
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


async def call_nvidia_async(
    prompt: str, api_key: str, model: str, client: "httpx.AsyncClient", max_retries: int = 3
) -> Optional[str]:
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
            "max_tokens": 8192,
            "temperature": 0.7,
            "top_p": 0.9,
            "stream": False,
        }

        try:
            response = await client.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            if response.status_code != 200:
                logger.error(f"  API error {response.status_code} on attempt {attempt}")
                if attempt < max_retries:
                    await asyncio.sleep(1)
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
                    await asyncio.sleep(1)
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
                await asyncio.sleep(1)
                continue
            return None

    return None


async def call_google_async(
    prompt: str, api_key: str, model: str, client: "httpx.AsyncClient", max_retries: int = 3
) -> Optional[str]:
    models = [m.strip() for m in model.split(",") if m.strip()]
    if not models:
        models = ["gemini-2.5-flash-lite"]

    for model_name in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

        for attempt in range(1, max_retries + 1):
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 8192,
                    "responseMimeType": "application/json",
                },
            }

            try:
                response = await client.post(url, json=payload)
                if response.status_code == 429:
                    logger.warning(f"  {model_name} quota exceeded (429), trying next model if available")
                    break

                if response.status_code != 200:
                    body = await response.aread()
                    logger.error(f"  Google API error {response.status_code} on {model_name} attempt {attempt}: {body[:200]}")
                    if attempt < max_retries:
                        await asyncio.sleep(2)
                        continue
                    break

                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]

                parsed = parse_questions(text)
                if not parsed:
                    parse_error = "JSON parse failed or empty array returned"
                    logger.warning(f"  {parse_error} on {model_name} attempt {attempt}")
                    if attempt < max_retries:
                        prompt = prompt + (
                            f"\n\nYour previous response was not valid JSON or did not contain valid questions. "
                            f"ERROR: {parse_error}. Please return ONLY a valid JSON array following the exact format specified above."
                        )
                        await asyncio.sleep(1)
                        continue
                    return text

                return text

            except (json.JSONDecodeError, httpx.RequestError, KeyError, IndexError) as e:
                logger.warning(f"  Attempt {attempt} on {model_name} failed: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(2)
                    continue
                break

    logger.error(f"  All models exhausted for Google API call")
    return None


async def _generate_one_task(
    topic: str,
    difficulty: str,
    arch: str,
    count: int,
    api_key: str,
    model: str,
    client: "httpx.AsyncClient",
    semaphore: asyncio.Semaphore,
    rate_limiter: RateLimiter,
    label: str,
    caller,
) -> Tuple[str, List[dict]]:
    """Generate questions for one topic/difficulty/archetype combo. Returns (label, questions)."""
    async with semaphore:
        await rate_limiter.acquire()
        prompt = build_prompt(topic, difficulty, count, archetype=arch)
        raw = await caller(prompt, api_key, model, client)
        if not raw:
            logger.warning(f"  Failed to generate for {label}")
            return label, []

        questions = parse_questions(raw)
        if not questions:
            logger.warning(f"  No valid questions parsed for {label}")
            return label, []

        questions = questions[:count]
        for q in questions:
            q["_archetype"] = arch

        pre_validated = []
        for q in questions:
            err = pre_validate_question(q, topic)
            if err:
                logger.warning(f"  Pre-validation failed for '{q.get('title', '?')}': {err}")
                continue
            pre_validated.append(q)

        logger.info(f"  [{label}] Generated {len(pre_validated)} valid questions")
        return label, pre_validated


def generate_questions(
    api_key: str,
    model: str = "gemini-2.5-flash-lite,gemini-3.1-flash-lite,gemini-3.5-flash",
    target: int = 90,
    questions_per_topic: int = 6,
    archetype: str = "mixed",
    topics: Optional[List[str]] = None,
    checkpoint_interval: int = 10,
    resume: bool = False,
    concurrency: int = 4,
    provider: str = "google",
) -> List[dict]:
    load_existing_ids()

    if topics is None:
        topics = list(TOPICS)

    completed_labels = set()
    checkpoint = load_checkpoint() if resume else None
    if checkpoint:
        completed_labels = set(checkpoint.get("completed_labels", []))
        logger.info(f"Resuming from checkpoint: {checkpoint.get('total', 0)} questions already generated")

    tasks_to_run = []
    for topic in topics:
        for difficulty in ["easy", "medium", "hard"]:
            remaining = target - len(tasks_to_run) * (questions_per_topic // 2)
            if remaining <= 0:
                break

            per_diff = min(questions_per_topic, remaining)

            if archetype == "mixed":
                half = max(1, per_diff // 2)
                arch_pairs = [("classic", half), ("creative_2026", per_diff - half)]
            else:
                arch_pairs = [(archetype, per_diff)]

            for arch, count_for_arch in arch_pairs:
                if count_for_arch < 1:
                    continue
                label = f"{topic}/{difficulty}/{arch}"
                if label in completed_labels:
                    logger.info(f"  Skipping already-completed: {label}")
                    continue
                tasks_to_run.append((topic, difficulty, arch, count_for_arch, label))

    PROVIDER_DISPATCH = {
        "google": call_google_async,
        "nvidia": call_nvidia_async,
    }
    caller = PROVIDER_DISPATCH.get(provider)
    if caller is None:
        logger.error(f"Unknown provider: {provider}. Use 'google' or 'nvidia'.")
        return []

    logger.info(f"\n=== Generating {len(tasks_to_run)} batches with concurrency={concurrency} ===")
    logger.info(f"  Provider: {provider}, Model: {model}")
    logger.info(f"  Target: {target} questions total")

    rpm = {"google": 15, "nvidia": 30}.get(provider, 15)
    semaphore = asyncio.Semaphore(concurrency)
    rate_limiter = RateLimiter(max_per_minute=rpm)
    all_questions = []
    total = 0

    async def _run_all():
        nonlocal total, all_questions
        async with httpx.AsyncClient(timeout=120.0) as client:
            batch_size = concurrency * 2
            for batch_start in range(0, len(tasks_to_run), batch_size):
                batch = tasks_to_run[batch_start:batch_start + batch_size]
                coros = [
                    _generate_one_task(t, d, a, c, api_key, model, client, semaphore, rate_limiter, l, caller)
                    for t, d, a, c, l in batch
                ]
                results = await asyncio.gather(*coros, return_exceptions=True)

                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"  Task exception: {result}")
                        continue
                    label, questions = result
                    completed_labels.add(label)
                    if questions:
                        all_questions.extend(questions)
                        total += len(questions)
                        logger.info(f"  [{label}] {len(questions)} valid (total: {total}/{target})")

                if total >= target:
                    break

                if total % checkpoint_interval < len(batch) * (questions_per_topic // 2):
                    save_checkpoint({
                        "questions": all_questions,
                        "total": total,
                        "completed_labels": list(completed_labels),
                    })

    asyncio.run(_run_all())

    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        logger.info("Checkpoint cleared after successful generation")

    return all_questions[:target]


def _json_loads_lenient(text: str):
    decoder = json.JSONDecoder(strict=False)
    try:
        return decoder.decode(text)
    except json.JSONDecodeError:
        return None


def parse_questions(raw: str) -> List[dict]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    data = _json_loads_lenient(text)
    if data is None:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            data = _json_loads_lenient(match.group(0))
        if data is None:
            logger.error("Could not parse JSON from response")
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
        if tc_count < 12:
            logger.warning(
                f"  Question '{q['title']}' has only {tc_count} test cases (want 12)"
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


def pre_validate_question(q: dict, expected_category: str) -> Optional[str]:
    """Programmatic pre-validation. Returns None if valid, error string if invalid."""
    if not q.get("title"):
        return "Missing 'title'"
    if not q.get("description") or len(q["description"]) < 100:
        return f"Description too short ({len(q.get('description', ''))} chars, need 100+)"
    if q.get("difficulty") not in ("easy", "medium", "hard"):
        return f"Invalid difficulty: {q.get('difficulty')}"
    if q.get("category") != expected_category:
        return f"Category mismatch: got '{q.get('category')}', expected '{expected_category}'"
    tcs = q.get("test_cases", [])
    if len(tcs) != 12:
        return f"Expected 12 test cases, got {len(tcs)}"
    hidden_count = sum(1 for tc in tcs if tc.get("hidden"))
    if hidden_count < 3:
        return f"Expected at least 3 hidden test cases, got {hidden_count}"
    if not isinstance(q.get("starter"), dict):
        return "Missing or invalid 'starter' object"
    for lang in ("python", "javascript", "java"):
        if lang not in q["starter"]:
            return f"Missing starter code for '{lang}'"
    if not q.get("solution"):
        return "Missing 'solution'"
    if not q.get("time_complexity"):
        return "Missing 'time_complexity'"
    if not q.get("space_complexity"):
        return "Missing 'space_complexity'"
    if not q.get("constraints") or len(q["constraints"]) < 2:
        return f"Only {len(q.get('constraints', []))} constraints (need 2+)"
    return None


def save_checkpoint(state: dict):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(state, f, indent=2)
    logger.info(f"Checkpoint saved ({state.get('total', 0)} questions so far)")


def load_checkpoint() -> Optional[dict]:
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return None


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


def main(args_list: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(
        description="Generate coding questions using AI providers"
    )
    parser.add_argument(
        "--provider",
        choices=["google", "nvidia"],
        default="google",
        help="AI provider: google (default, fast + reliable) or nvidia (llama-3.1-70b)",
    )
    parser.add_argument(
        "--api-key", help="API key for the provider (default: GOOGLE_API_KEY or NVIDIA_API_KEY env var)"
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name (default: 'gemini-2.5-flash-lite,gemini-3.1-flash-lite,gemini-3.5-flash' for google, "
             "'meta/llama-3.1-70b-instruct' for nvidia). "
             "For google, comma-separated fallback chain is supported.",
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
        "--categories",
        nargs="+",
        help="Specific categories to generate for (default: all 14 DSA topics). "
             f"Valid: {', '.join(TOPICS)}",
    )
    parser.add_argument(
        "--target-per-category",
        type=int,
        default=0,
        help="Generate this many questions per category regardless of --target (overrides target)",
    )
    parser.add_argument(
        "--checkpoint-interval",
        type=int,
        default=10,
        help="Save checkpoint every N questions (default: 10)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=None,
        help="Max concurrent API calls (default: 4 for google, 3 for nvidia)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print questions without saving"
    )
    args = parser.parse_args(args_list)

    provider = args.provider

    if provider == "google":
        api_key = args.api_key or os.getenv("GOOGLE_API_KEY")
        model = args.model or "gemini-2.5-flash-lite,gemini-3.1-flash-lite,gemini-3.5-flash"
        concurrency = args.concurrency or 2
        if not api_key:
            logger.error("GOOGLE_API_KEY not set. Use --api-key or set env var.")
            sys.exit(1)
    else:
        api_key = args.api_key or os.getenv("NVIDIA_API_KEY")
        model = args.model or "meta/llama-3.1-70b-instruct"
        concurrency = args.concurrency or 3
        if not api_key:
            logger.error("NVIDIA_API_KEY not set. Use --api-key or set env var.")
            sys.exit(1)

    topics = None
    if args.categories:
        invalid = [c for c in args.categories if c not in VALID_TOPICS_SET]
        if invalid:
            logger.error(f"Invalid categories: {invalid}. Valid options: {TOPICS}")
            sys.exit(1)
        topics = args.categories
        logger.info(f"Generating for {len(topics)} specific categories: {topics}")

    all_questions = generate_questions(
        api_key,
        model,
        questions_per_topic=args.questions_per_topic,
        archetype=args.archetype,
        topics=topics,
        checkpoint_interval=args.checkpoint_interval,
        resume=args.resume,
        concurrency=concurrency,
        provider=provider,
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
