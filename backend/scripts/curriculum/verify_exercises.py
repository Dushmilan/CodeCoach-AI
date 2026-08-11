#!/usr/bin/env python3
"""Verify every exercise's starter code passes its own test cases via Piston.

Usage:
    python scripts/curriculum/verify_exercises.py [--course intro-to-r] [--language r]
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import httpx

from app.adapters.code_wrappers import build_runner, get_wrapper
from app.services.static_code_validator import get_file_extension

_LANG_VERSION = {
    "python": "3.10.0",
    "javascript": "18.15.0",
    "java": "15.0.2",
    "c": "10.2.0",
    "r": "4.1.1",
    "bash": "5.2.0",
}

_PISTON_LANG = {"c": "gcc", "r": "rscript"}


async def _execute(client, lang, code, stdin=""):
    wrapper = get_wrapper(lang)
    code_to_run = wrapper.wrap(code) if wrapper else code
    payload = {
        "language": _PISTON_LANG.get(lang, lang),
        "version": _LANG_VERSION.get(lang, "latest"),
        "files": [{"name": f"main.{get_file_extension(lang)}", "content": code_to_run}],
        "stdin": stdin,
        "args": [],
        "compile_timeout": 10000,
        "run_timeout": 3000,
    }
    resp = await client.post("http://localhost:2000/api/v2/execute", json=payload)
    data = resp.json()
    run = data.get("run") or {}
    return run.get("stdout", ""), run.get("stderr", ""), run.get("code")


def _iter_courses(course_filter=None):
    base = Path(__file__).parent.parent.parent / "data" / "courses"
    for lang_dir in sorted(base.iterdir()):
        if not lang_dir.is_dir():
            continue
        for course_dir in sorted(lang_dir.iterdir()):
            if not course_dir.is_dir():
                continue
            lessons_path = course_dir / "lessons.json"
            if not lessons_path.exists():
                continue
            course_data = json.load(open(course_dir / "course.json", encoding="utf-8"))
            if course_filter and course_data["id"] != course_filter:
                continue
            lessons = json.load(open(lessons_path, encoding="utf-8"))
            items = lessons.get("items", lessons) if isinstance(lessons, dict) else lessons
            yield course_data, items


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--course", type=str, default=None)
    parser.add_argument("--language", type=str, default=None)
    args = parser.parse_args()

    async with httpx.AsyncClient(timeout=90) as client:
        failures = 0
        checked = 0
        for course, lessons in _iter_courses(args.course):
            for lesson in lessons:
                if lesson.get("type") != "exercise":
                    continue
                if not lesson.get("starter_code") or not lesson.get("test_cases"):
                    continue
                lang = lesson.get("language")
                if args.language and lang != args.language:
                    continue
                if get_wrapper(lang) is None:
                    continue
                code = lesson["starter_code"]
                test_cases = [
                    {
                        "input": tc.get("input", ""),
                        "expected_output": tc.get("expected_output", ""),
                        "hidden": tc.get("hidden", False),
                    }
                    for tc in lesson["test_cases"]
                ]

                # Path 1: run path — one execution per test with stdin = input
                # (this is exactly how the lesson exercise UI submits).
                run_ok = True
                for tc in test_cases:
                    stdout, stderr, exit_code = await _execute(
                        client, lang, code, stdin=tc["input"]
                    )
                    actual = stdout.strip()
                    expected = tc["expected_output"].strip()
                    if actual != expected:
                        run_ok = False
                        print(f"FAIL(run) {course['id']}/{lesson['id']} [{lang}]")
                        print(f"  input: {tc['input']!r}")
                        print(f"  expected: {expected!r} actual: {actual!r}")
                        print(f"  stderr: {stderr[:200]}")
                        break

                # Path 2: suite path — used by linked-question submissions.
                runner = build_runner(lang, code, test_cases)
                payload = {
                    "language": _PISTON_LANG.get(lang, lang),
                    "version": _LANG_VERSION.get(lang, "latest"),
                    "files": [
                        {"name": f"main.{get_file_extension(lang)}", "content": runner}
                    ],
                    "stdin": "",
                    "args": [],
                    "compile_timeout": 10000,
                    "run_timeout": 3000,
                }
                resp = await client.post("http://localhost:2000/api/v2/execute", json=payload)
                data = resp.json()
                run = data.get("run") or {}
                stdout = run.get("stdout", "")
                stderr = run.get("stderr", "")
                marker = "@@SUITE_RESULT@@"
                suite_ok = marker in stdout
                if suite_ok:
                    try:
                        suite_results = json.loads(
                            stdout[stdout.find(marker) + len(marker): stdout.rfind(marker)]
                        )
                        suite_ok = all(r.get("passed") for r in suite_results)
                    except (json.JSONDecodeError, ValueError):
                        suite_ok = False
                if not suite_ok:
                    print(f"FAIL(suite) {course['id']}/{lesson['id']} [{lang}]")
                    print(f"  stderr: {stderr[:200]}")
                    print(f"  stdout: {stdout[:300]}")

                if run_ok and suite_ok:
                    checked += 1
                    print(f"OK {course['id']}/{lesson['id']}")
                else:
                    failures += 1
        print(f"\n{checked} exercises passing, {failures} failures")


asyncio.run(main())
