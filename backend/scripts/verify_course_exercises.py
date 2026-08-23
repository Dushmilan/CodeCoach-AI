#!/usr/bin/env python3
"""Verify authored course exercises against the local Piston sandbox.

For every ``type=exercise`` lesson in ``data/courses/**`` this tool fills the
starter code's TODO markers with the curated reference solution, compiles and
runs it in Piston for EACH stored test case, and compares output using the
same normalization as app/adapters/code_wrappers/output_comparator.py.

Usage:
    python scripts/verify_course_exercises.py [--piston URL] [--lang c,java]

Exit code 0 iff every test case of every solved exercise passes.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

import httpx

BASE_DIR = Path(__file__).resolve().parent.parent

RUNTIMES = {"c": "10.2.0", "java": "15.0.2"}

# Java exercises whose starter declares helper classes before Main;
# Piston runs the FIRST declared class, so Main must be hoisted.
HOIST_MAIN = {
    "java-exercise-rectangle",
    "java-exercise-bank",
    "java-exercise-shape",
}

# Reference solutions.
#   lesson_id -> list[str]            : snippets replacing consecutive
#                                       TODO-marker lines (indent-aware)
#   lesson_id -> {"replace": [...]}   : literal (old, new) string pairs
SOLUTIONS: dict[str, list[str] | dict] = {
    # ---------------- C ----------------
    "c-exercise-hello-name": {
        "replace": [
            (
                "// Read the name and age here",
                'scanf("%s %d", name, &age);',
            ),
            (
                "// Print the greeting here",
                'printf("Hello, %s! You are %d today.\\n", name, age);',
            ),
        ]
    },
    "c-exercise-temperature": ["return (f - 32) * 5 / 9;"],
    "c-exercise-simple-calculator": [
        "if (op == '+') return a + b;\nif (op == '-') return a - b;\n"
        "if (op == '*') return a * b;\n"
        "if (op == '/') return b != 0 ? a / b : INT_MIN;\nreturn INT_MIN;",
    ],
    "c-exercise-even-odd": ["return n % 2 == 0;"],
    "c-exercise-fizzbuzz": [
        'for (int i = 1; i <= n; i++) {\nif (i % 15 == 0) printf("FizzBuzz\\n");\n'
        'else if (i % 3 == 0) printf("Fizz\\n");\nelse if (i % 5 == 0) printf("Buzz\\n");\n'
        'else printf("%d\\n", i);\n}',
    ],
    "c-exercise-sum-to-n": [
        'for (int i = 0; i < n; i++) {\nint x;\nscanf("%d", &x);\nsum += x;\n}',
    ],
    "c-exercise-max-three": ["int m = a > b ? a : b;\nreturn m > c ? m : c;"],
    "c-exercise-factorial": [
        "long long result = 1;\nfor (int i = 2; i <= n; i++) result *= i;\nreturn result;",
    ],
    "c-exercise-swap": ["int tmp = *a;\n*a = *b;\n*b = tmp;"],
    "c-exercise-array-sum": [
        "int total = 0;\nfor (int i = 0; i < n; i++) total += arr[i];\nreturn total;",
    ],
    "c-exercise-reverse-string": [
        "int i = 0, j = strlen(s) - 1;\nwhile (i < j) {\nchar t = s[i];\n"
        "s[i++] = s[j];\ns[j--] = t;\n}",
    ],
    "c-exercise-struct-average": [
        'printf("%s: %.2f\\n", s.name, (s.score1 + s.score2 + s.score3) / 3.0);',
    ],
    "c-exercise-dynamic-sum": [
        "int *arr = malloc(n * sizeof(int));\nif (arr == NULL) return 1;",
        'for (int i = 0; i < n; i++) {\nscanf("%d", &arr[i]);\nsum += arr[i];\n}',
        "free(arr);",
    ],
    "c-exercise-file-sum": ['int x;\nwhile (scanf("%d", &x) == 1) sum += x;'],
    "c-exercise-macro-square": ["#define SQUARE(x) ((x) * (x))"],
    # ---------------- Java ----------------
    "java-exercise-greeting": [
        "String name = scanner.next();\nint age = scanner.nextInt();",
        'System.out.println("Hello, " + name + "! You are " + age + " today.");',
    ],
    "java-exercise-temperature": ["return (f - 32) * 5 / 9;"],
    "java-exercise-calculator": [
        "if (op == '/' && b == 0) return Integer.MIN_VALUE;\n"
        "switch (op) {\ncase '+': return a + b;\ncase '-': return a - b;\n"
        "case '*': return a * b;\ncase '/': return a / b;\n"
        "default: return Integer.MIN_VALUE;\n}",
    ],
    "java-exercise-even-odd": ['return n % 2 == 0 ? "even" : "odd";'],
    "java-exercise-fizzbuzz": [
        'for (int i = 1; i <= n; i++) {\nif (i % 15 == 0) System.out.println("FizzBuzz");\n'
        'else if (i % 3 == 0) System.out.println("Fizz");\n'
        'else if (i % 5 == 0) System.out.println("Buzz");\n'
        "else System.out.println(i);\n}",
    ],
    "java-exercise-sum-numbers": [
        "for (int i = 0; i < n; i++) sum += scanner.nextInt();",
    ],
    "java-exercise-rectangle": [
        "private int width;\nprivate int height;\n\n"
        "public Rectangle(int width, int height) {\nthis.width = width;\n"
        "this.height = height;\n}\n\npublic int area() {\nreturn width * height;\n}",
    ],
    "java-exercise-bank": ["balance += amount;", "balance -= amount;"],
    "java-exercise-shape": [
        "public double area() {\nreturn 3.14159 * r * r;\n}",
        "public double area() {\nreturn s * s;\n}",
        "public double area() {\nreturn w * h;\n}",
    ],
    "java-exercise-reverse-string": [
        "return new StringBuilder(s).reverse().toString();",
    ],
    "java-exercise-vowel-count": [
        "int count = 0;\nfor (char c : s.toCharArray()) {\n"
        'if ("aeiou".indexOf(c) >= 0) count++;\n}\nreturn count;',
    ],
    "java-exercise-frequency": [
        "Map<Character, Integer> counts = new LinkedHashMap<>();\n"
        "for (char c : word.toCharArray()) {\ncounts.merge(c, 1, Integer::sum);\n}\n"
        "for (Map.Entry<Character, Integer> e : counts.entrySet()) {\n"
        'System.out.println(e.getKey() + ":" + e.getValue());\n}',
    ],
    "java-exercise-uppercase": [
        "while (scanner.hasNextLine()) {\n"
        "System.out.println(scanner.nextLine().toUpperCase());\n}",
    ],
    "java-exercise-generic-max": [
        "public static <T extends Comparable<T>> T max(T a, T b) {\n"
        "return a.compareTo(b) >= 0 ? a : b;\n}",
    ],
    "java-exercise-filter-positives": [
        "for (int v : numbers) {\nif (v > 0) System.out.println(v);\n}",
    ],
}


def _apply_replace(code: str, pairs) -> str:
    for old, new in pairs:
        if old not in code:
            raise ValueError(f"replacement anchor not found: {old[:50]}")
        code = code.replace(old, new, 1)
    return code


def _hoist_main(code: str) -> str:
    """Move `public class Main` above helper classes so Piston's entry
    detection finds main()."""
    idx = code.find("public class Main")
    if idx <= 0:
        return code
    depth = 0
    opened = False
    end = len(code)
    for pos in range(idx, len(code)):
        ch = code[pos]
        if ch == "{":
            depth += 1
            opened = True
        elif ch == "}":
            depth -= 1
            if opened and depth == 0:
                end = pos + 1
                break
    block = code[idx:end]
    before = code[:idx] + code[end:]

    # Split leading import/package header off `before`.
    header_lines = []
    body_lines = []
    for ln in before.split("\n"):
        if not body_lines and (
            ln.startswith("import ") or ln.startswith("package ") or ln.strip() == ""
        ):
            header_lines.append(ln)
        else:
            body_lines.append(ln)
    header = "\n".join(header_lines).strip("\n")
    helpers = "\n".join(body_lines).strip("\n")

    parts = [p for p in (header, block, helpers) if p]
    return "\n\n".join(parts) + "\n"


def fill_todos(starter: str, snippets: list[str]) -> str:
    """Replace TODO comment blocks with snippet blocks (indent-aware).

    A TODO block is the line containing ``TODO`` plus any immediately
    following pure-comment continuation lines (e.g. " //       in
    first-appearance order").
    """
    lines = starter.split("\n")
    out: list[str] = []
    used = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        if "TODO" in line and used < len(snippets):
            indent = line[: len(line) - len(line.lstrip())]
            out.append(indent + snippets[used].replace("\n", "\n" + indent))
            used += 1
            i += 1
            while i < len(lines) and lines[i].lstrip().startswith("//"):
                i += 1
        else:
            out.append(line)
            i += 1
    if used != len(snippets):
        raise ValueError(f"expected {len(snippets)} TODOs, found {used}")
    return "\n".join(out)


def _norm(text: str) -> str:
    return text[:-1] if text.endswith("\n") else text


def outputs_match(actual: str, expected: str) -> bool:
    """Mirror of output_comparator.outputs_match (single-trailing-newline)."""
    a, e = _norm(actual or ""), _norm(expected or "")

    def decode(t):
        try:
            return json.loads(t)
        except (ValueError, TypeError):
            return None

    ej, aj = decode(e), decode(a)
    if isinstance(ej, str):
        return a == ej or aj == ej
    if ej is not None:
        return aj == ej
    return a == e


async def run_in_piston(
    client: httpx.AsyncClient, piston_url: str, language: str, code: str, stdin: str
) -> tuple[str, str]:
    resp = await client.post(
        f"{piston_url}/api/v2/execute",
        json={
            "language": language,
            "version": RUNTIMES[language],
            "files": [{"content": code}],
            "stdin": stdin,
            "compile_timeout": 10000,
            "run_timeout": 3000,
        },
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"piston {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    compile_out = (data.get("compile") or {}).get("stderr") or ""
    run = data.get("run") or {}
    stdout = run.get("stdout") or ""
    stderr = run.get("stderr") or ""
    if run.get("code") not in (0, None) and stderr:
        raise RuntimeError(f"runtime error: {stderr[:200]}")
    if compile_out.strip():
        raise RuntimeError(f"compile error: {compile_out[:500]}")
    return stdout, stderr


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--piston", default="http://localhost:2000")
    parser.add_argument("--lang", default="c,java")
    args = parser.parse_args()

    courses_dir = BASE_DIR / "data" / "courses"
    passed = failed = skipped = 0
    failures: list[str] = []

    async with httpx.AsyncClient() as client:
        for lang in args.lang.split(","):
            lang_dir = courses_dir / lang
            for course_dir in sorted(lang_dir.iterdir()):
                lessons = json.loads(
                    (course_dir / "lessons.json").read_text(encoding="utf-8")
                )["items"]
                for ex in [ls for ls in lessons if ls.get("type") == "exercise"]:
                    lid = ex["id"]
                    if lid not in SOLUTIONS:
                        skipped += 1
                        print(f"SKIP {lid} (no reference solution)")
                        continue
                    try:
                        entry = SOLUTIONS[lid]
                        code = (
                            _apply_replace(ex["starter_code"], entry["replace"])
                            if isinstance(entry, dict)
                            else fill_todos(ex["starter_code"], entry)
                        )
                        if ex["language"] == "java" and ex["id"] in HOIST_MAIN:
                            code = _hoist_main(code)
                    except ValueError as exc:
                        failed += 1
                        failures.append(f"{lid}: {exc}")
                        continue
                    ok = True
                    for tc in ex["test_cases"]:
                        try:
                            stdout, _ = await run_in_piston(
                                client,
                                args.piston,
                                ex["language"],
                                code,
                                tc["input"],
                            )
                        except Exception as exc:
                            ok = False
                            failures.append(f"{lid}: {exc}")
                            break
                        if not outputs_match(stdout, tc["expected_output"]):
                            ok = False
                            failures.append(
                                f"{lid}: got {stdout!r} want {tc['expected_output']!r}"
                                f" (stdin={tc['input']!r})"
                            )
                            break
                    if ok:
                        passed += 1
                        print(f"PASS {lid}")
                    else:
                        failed += 1

    print(f"\npassed={passed} failed={failed} skipped={skipped}")
    for f in failures:
        print("FAIL:", f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
