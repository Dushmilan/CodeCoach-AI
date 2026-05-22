#!/usr/bin/env bash
set -euo pipefail

echo "=== Ruff Check ==="
ruff check .

echo "=== Ruff Format Check ==="
ruff format . --check

echo "=== MyPy ==="
mypy app/

echo "=== Pytest with Coverage ==="
python -m pytest --cov=app --cov-report=term-missing -v
