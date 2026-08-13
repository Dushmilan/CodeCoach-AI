"""Full-inventory animation coverage runner.

Queries every question in the Supabase questions table, resolves its canonical
algorithm, executes the traced optimal solution against examples[0].input in
Piston, compiles the trace with the family compiler and validates the scene.

Run inside the backend container (needs DATABASE_URL + Piston reachable):

    docker compose up -d --build backend
    docker exec codecoach-backend python scripts/animate_coverage.py

Exits non-zero if any question fails to produce a valid animation.
"""

import asyncio
import sys

from sqlalchemy import select

from app.core.database import async_session_maker
from app.models.orm import QuestionORM
from app.services.piston_service import PistonService
from app.services.solution_animation_service import SolutionAnimationService
from app.services.reference_solutions import (
    get_reference_solution,
    resolve_algorithm,
)


async def main() -> int:
    async with async_session_maker() as session:
        rows = (
            (await session.execute(select(QuestionORM).order_by(QuestionORM.title)))
            .scalars()
            .all()
        )

    service = SolutionAnimationService(executor=PistonService())
    results = []
    failures = []

    for row in rows:
        question = {
            "id": row.id,
            "title": row.title,
            "category": row.category,
            "description": row.description,
            "examples": row.examples or [],
            "test_cases": row.test_cases or [],
            "constraints": row.constraints or [],
        }
        algorithm = resolve_algorithm(question)
        family = (
            get_reference_solution(algorithm).get("family")
            if algorithm and get_reference_solution(algorithm)
            else "unresolved"
        )
        try:
            animation = await service.build_animation(question)
        except Exception as exc:  # noqa: BLE001 - report and continue
            failures.append((row.id, row.title, f"exception: {exc}"))
            results.append((row.id, row.title, family, "FAIL"))
            continue
        if animation is None:
            failures.append((row.id, row.title, "no scene"))
            results.append((row.id, row.title, family, "FAIL"))
        else:
            results.append((row.id, row.title, family, "OK"))

    by_family: dict = {}
    for _qid, _title, family, status in results:
        by_family.setdefault(family, {"ok": 0, "fail": 0})
        by_family[family]["ok" if status == "OK" else "fail"] += 1

    print("=" * 72)
    print("ANIMATION COVERAGE")
    print("=" * 72)
    for family, counts in sorted(by_family.items()):
        print(f"  {family:12s} ok={counts['ok']:3d} fail={counts['fail']:3d}")
    total_ok = sum(v["ok"] for v in by_family.values())
    total = len(results)
    print("-" * 72)
    print(f"TOTAL {total_ok}/{total} questions produce a validated animation")
    if failures:
        print("-" * 72)
        print("FAILURES:")
        for qid, title, reason in failures:
            print(f"  {qid} | {title} | {reason}")

    unresolved = [r for r in results if r[2] == "unresolved"]
    if unresolved:
        print("-" * 72)
        print(f"UNRESOLVED ({len(unresolved)}):")
        for qid, title, _f, _s in unresolved:
            print(f"  {qid} | {title}")

    return 0 if not failures else 1


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except Exception as exc:  # noqa: BLE001
        print(f"coverage runner crashed: {exc}", file=sys.stderr)
        sys.exit(2)
