"""Contract tests for the one-button local starter (./dev.sh, issue #215).

dev.sh is repo tooling, not app code, so these live at the repo root
(outside the backend tiers that require a live DB at conftest import).
Run explicitly:  python -m pytest tests/test_dev_script.py -v
"""

import os
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEV_SH = ROOT / "dev.sh"


def _read() -> str:
    return DEV_SH.read_text(encoding="utf-8")


def test_dev_script_exists_and_is_executable():
    assert DEV_SH.is_file(), "dev.sh missing at repo root"
    mode = os.stat(DEV_SH).st_mode
    assert mode & stat.S_IXUSR, "dev.sh is not executable"


def test_dev_script_syntax_valid():
    proc = subprocess.run(
        ["bash", "-n", str(DEV_SH)], capture_output=True, text=True, timeout=30
    )
    assert proc.returncode == 0, f"bash -n failed: {proc.stderr}"


def test_dev_script_help_lists_modes():
    proc = subprocess.run(
        ["bash", str(DEV_SH), "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, f"--help failed: {proc.stderr}"
    for flag in ("--down", "--with-viewer", "--install"):
        assert flag in proc.stdout, f"--help missing {flag}"


def test_dev_script_never_builds_images_or_wipes_next_cache():
    src = _read()
    assert "--build" not in src, "must start infra, never build images (data cost)"
    assert "rm -rf .next" not in src, "must not wipe the Next.js cache"


def test_dev_script_forces_same_origin_api_base():
    # An absolute NEXT_PUBLIC_API_URL baked into the client bundle breaks
    # CSP connect-src on every request; local dev must stay same-origin.
    src = _read()
    assert "NEXT_PUBLIC_API_URL" in src
    assert 'NEXT_PUBLIC_API_URL=""' in src or "NEXT_PUBLIC_API_URL=''" in src


def test_dev_script_has_health_gates_and_teardown():
    src = _read()
    assert "/health/" in src, "backend health gate missing"
    assert "pg_isready" in src, "postgres readiness check missing"
    assert "--down" in src, "teardown mode missing"
