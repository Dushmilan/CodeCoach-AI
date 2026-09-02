#!/usr/bin/env python3
"""Snapshot current measured coverage as the regression-floor baseline.

Reads a Cobertura coverage.xml and writes qa/coverage-baseline.json for the
modules listed in qa/coverage-budget.json. Run this only after a deliberate,
verified coverage improvement — the snapshot is what CI holds you to.

Usage:
    python qa/snapshot_coverage_baseline.py \
        --xml backend/coverage.xml \
        --budget qa/coverage-budget.json \
        --out qa/coverage-baseline.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def _normalize(path: str) -> str:
    return path.replace("\\", "/").lstrip("/").removeprefix("app/")


def _trunc1(value: float) -> float:
    """Truncate to 1 decimal so the floor never exceeds raw measured coverage."""
    return math.floor(value * 10.0 + 1e-9) / 10.0


def parse_coverage(xml_path: Path) -> dict[str, tuple[float, float]]:
    root = ET.parse(xml_path).getroot()
    out: dict[str, tuple[float, float]] = {}
    for cls in root.iter("class"):
        filename = (cls.get("filename") or "").replace("\\", "/")
        if not filename:
            continue
        out[filename] = (
            float(cls.get("line-rate") or 0.0) * 100.0,
            float(cls.get("branch-rate") or 0.0) * 100.0,
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml", required=True)
    parser.add_argument("--budget", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    budget = json.loads(Path(args.budget).read_text())
    measurements = parse_coverage(Path(args.xml))
    exception_patterns = {exc["pattern"] for exc in budget.get("exceptions", [])}

    modules: dict[str, dict[str, float]] = {}
    exceptions: dict[str, dict[str, float]] = {}
    not_measured: list[str] = []

    for key in list(budget.get("modules", {})) + list(exception_patterns):
        normalized = _normalize(key)
        value = measurements.get(key) or measurements.get(normalized)
        if value is None:
            not_measured.append(key)
            continue
        entry = {"lines": _trunc1(value[0]), "branches": _trunc1(value[1])}
        if key in exception_patterns:
            exceptions[key] = entry
        else:
            modules[key] = entry

    out = {
        "version": 1,
        "comment": (
            "Regression floors captured at snapshot time. CI fails when a budgeted "
            "module's measured coverage drops below these floors. Regenerate only "
            "after a deliberate, verified coverage improvement."
        ),
        "generated_at": "2026-08-09",
        "modules": modules,
        "exceptions": exceptions,
    }
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n")
    print(
        f"[snapshot] wrote {args.out} ({len(modules)} modules, "
        f"{len(exceptions)} exceptions)"
    )
    if not_measured:
        print(f"[snapshot] WARNING — not measured by this run: {not_measured}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
