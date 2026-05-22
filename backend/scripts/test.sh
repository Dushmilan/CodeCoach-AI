#!/usr/bin/env bash
set -euo pipefail

CATEGORY="${1:-all}"

case "$CATEGORY" in
  unit)
    echo "=== Unit Tests ==="
    python -m pytest tests/unit/ -v
    ;;
  integration)
    echo "=== Integration Tests ==="
    python -m pytest tests/integration/ -v
    ;;
  security)
    echo "=== Security Tests ==="
    python -m pytest tests/security/ -v
    ;;
  performance)
    echo "=== Performance Tests ==="
    python -m pytest tests/performance/ -v
    ;;
  all)
    echo "=== All Tests ==="
    python -m pytest --cov=app --cov-report=term-missing -v
    ;;
  *)
    echo "Usage: $0 {unit|integration|security|performance|all}"
    exit 1
    ;;
esac
