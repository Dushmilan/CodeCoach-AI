#!/usr/bin/env python3
"""Validate the flaky-quarantine manifest (tests/flaky-quarantine.json).

Rules enforced:
- Every quarantined entry has node_id, reason, owner, and fix_by (YYYY-MM-DD).
- No duplicate node_ids.
- The manifest is a well-formed JSON document matching the schema.

The quarantine manifest exists so known-flaky tests never silently fail CI:
they are excluded from normal runs (see .github/workflows/ci.yml), tracked
here with an owner + fix-by date, and re-enabled when fixed. This gate is the
"release valve" — it guarantees the list cannot grow without accountability.

Usage:
    python tests/enforce_flaky_quarantine.py \
        [--manifest tests/flaky-quarantine.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path


def _parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def validate(manifest_path: Path) -> int:
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[flaky-quarantine] FAIL — cannot read {manifest_path}: {exc}")
        return 1

    if data.get("schema_version") != 1:
        print("[flaky-quarantine] FAIL — schema_version must be 1")
        return 1

    entries = data.get("quarantined", [])
    if not isinstance(entries, list):
        print("[flaky-quarantine] FAIL — 'quarantined' must be a list")
        return 1

    errors: list[str] = []
    seen: set[str] = set()

    today = date.today()

    for i, entry in enumerate(entries):
        node_id = entry.get("node_id")
        if not node_id:
            errors.append(f"entry[{i}]: missing node_id")
            continue
        if node_id in seen:
            errors.append(f"entry[{i}]: duplicate node_id {node_id!r}")
        seen.add(node_id)

        for field in ("reason", "owner"):
            if not entry.get(field):
                errors.append(f"entry[{i}] ({node_id}): missing {field!r}")

        fix_by = entry.get("fix_by")
        if not fix_by:
            errors.append(f"entry[{i}] ({node_id}): missing fix_by (YYYY-MM-DD)")
        else:
            try:
                fix_date = _parse_date(fix_by).date()
                if fix_date < today:
                    errors.append(
                        f"entry[{i}] ({node_id}): fix_by {fix_by} is in the past — "
                        "the test must be fixed and un-quarantined"
                    )
            except ValueError:
                errors.append(
                    f"entry[{i}] ({node_id}): fix_by {fix_by!r} is not YYYY-MM-DD"
                )

    if errors:
        print("[flaky-quarantine] FAIL — manifest is invalid:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(
        f"[flaky-quarantine] OK — {len(entries)} quarantined test(s), "
        "all with owner + fix_by"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        default=Path(__file__).with_name("flaky-quarantine.json"),
        help="path to flaky-quarantine.json",
    )
    args = parser.parse_args()
    return validate(Path(args.manifest))


if __name__ == "__main__":
    sys.exit(main())
