#!/usr/bin/env python3
"""Build all curriculum courses from the content modules into data/courses/.

Usage:
    python scripts/curriculum/build_all.py [--course intro-to-r] [--dry-run]
"""

import argparse
import importlib
import pkgutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.curriculum.builder import write_course


def main():
    parser = argparse.ArgumentParser(description="Build curriculum JSON files")
    parser.add_argument("--course", type=str, default=None, help="Build only this course id")
    parser.add_argument("--dry-run", action="store_true", help="Validate content without writing")
    args = parser.parse_args()

    courses_dir = Path(__file__).parent / "courses"
    built = 0
    for module_info in sorted(pkgutil.iter_modules([str(courses_dir)])):
        if module_info.name.startswith("_"):
            continue
        mod = importlib.import_module(f"scripts.curriculum.courses.{module_info.name}")
        if args.course and mod.COURSE["id"] != args.course:
            continue
        if args.dry_run:
            write_course(mod.COURSE["language"], mod.COURSE, mod.MODULES, mod.LESSONS)
            print(f"  validated: {mod.COURSE['id']}")
        else:
            course_dir = write_course(mod.COURSE["language"], mod.COURSE, mod.MODULES, mod.LESSONS)
            print(f"  wrote: {course_dir}")
        built += 1

    print(f"Done. {built} course(s).")


if __name__ == "__main__":
    main()
