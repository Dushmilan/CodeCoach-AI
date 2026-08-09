#!/usr/bin/env python3
"""Enforce per-module coverage budgets from a Cobertura coverage.xml report.

Quality gate: a PR fails when a budgeted module's measured line/branch coverage
drops below its regression floor (qa/coverage-baseline.json), and remains below
the staged target in qa/coverage-budget.json.

Effective floor for each module:
    floor = min(target_tier, baseline[module] if present else target_tier)

So currently-under-covered modules are held to their snapshot (no backsliding)
while already-covered modules are held to the tier target. Improve coverage,
run qa/snapshot_coverage_baseline.py, and the floor rises.

Usage:
    python qa/enforce_coverage_budget.py \
        --xml backend/coverage.xml \
        --budget qa/coverage-budget.json \
        --baseline qa/coverage-baseline.json
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Floor:
    lines: float
    branches: float


@dataclass(frozen=True)
class Measurement:
    lines: float
    branches: float


def _normalize(path: str) -> str:
    return path.replace("\\", "/").lstrip("/").removeprefix("app/")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def parse_coverage(xml_path: Path) -> dict[str, Measurement]:
    root = ET.parse(xml_path).getroot()
    measurements: dict[str, Measurement] = {}
    for cls in root.iter("class"):
        filename = (cls.get("filename") or "").replace("\\", "/")
        if not filename:
            continue
        measurements[filename] = Measurement(
            lines=float(cls.get("line-rate") or 0.0) * 100.0,
            branches=float(cls.get("branch-rate") or 0.0) * 100.0,
        )
    return measurements


def _lookup(values: dict[str, Any], module_path: str) -> Any:
    normalized = _normalize(module_path)
    for key, value in values.items():
        if _normalize(key) == normalized:
            return value
    return None


def resolve_floor(
    module_path: str,
    budget: dict[str, Any],
    baseline: dict[str, Any],
) -> tuple[Floor, str]:
    normalized = _normalize(module_path)
    targets = budget["targets"]

    configured = _lookup(budget.get("modules", {}), module_path)
    if configured is not None:
        tier = configured.get("tier", "core")
        target = targets.get(tier, targets["core"])
        reason = f"tier={tier} (target {target['lines']}/{target['branches']})"
    else:
        exc = next(
            (
                e
                for e in budget.get("exceptions", [])
                if _normalize(e.get("pattern", "")) == normalized
            ),
            None,
        )
        if exc is not None:
            target = {"lines": float(exc["lines"]), "branches": float(exc["branches"])}
            reason = "documented exception"
        else:
            return None, "not budgeted"

    snapshot = _lookup(baseline.get("modules", {}), module_path)
    if snapshot is None:
        snapshot = _lookup(baseline.get("exceptions", {}), module_path)
    if snapshot is not None:
        floor = Floor(
            lines=min(float(target["lines"]), float(snapshot["lines"])),
            branches=min(float(target["branches"]), float(snapshot["branches"])),
        )
    else:
        floor = Floor(
            lines=float(target["lines"]), branches=float(target["branches"])
        )
    return floor, reason


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml", required=True, help="Path to Cobertura coverage.xml")
    parser.add_argument("--budget", required=True, help="qa/coverage-budget.json")
    parser.add_argument(
        "--baseline",
        default=Path(__file__).with_name("coverage-baseline.json"),
        help="qa/coverage-baseline.json (regression floors)",
    )
    args = parser.parse_args()

    budget = load_json(Path(args.budget))
    baseline = load_json(Path(args.baseline))
    measurements = parse_coverage(Path(args.xml))

    failures: list[str] = []
    enforced: list[str] = []
    skipped: list[str] = []

    for module_path in sorted(measurements):
        floor, reason = resolve_floor(module_path, budget, baseline)
        if floor is None:
            skipped.append(module_path)
            continue
        measured = measurements[module_path]
        enforced.append(module_path)
        if (
            measured.lines < floor.lines - 1e-9
            or measured.branches < floor.branches - 1e-9
        ):
            failures.append(
                f"{module_path}: lines {measured.lines:.1f}% / branches "
                f"{measured.branches:.1f}% — need >= {floor.lines:.1f}% / "
                f"{floor.branches:.1f}% ({reason})"
            )

    for key in list(budget.get("modules", {})) + [
        e["pattern"] for e in budget.get("exceptions", [])
    ]:
        if _normalize(key) not in {_normalize(m) for m in measurements}:
            failures.append(f"{key}: NOT MEASURED by coverage run")

    print(f"[coverage-budget] enforced {len(enforced)} budgeted modules "
          f"({len(skipped)} unmanaged/unbudgeted skipped)")
    if failures:
        print("[coverage-budget] FAIL — budgeted modules below regression floor:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("[coverage-budget] OK — all budgeted modules at/above floors")
    return 0


if __name__ == "__main__":
    sys.exit(main())