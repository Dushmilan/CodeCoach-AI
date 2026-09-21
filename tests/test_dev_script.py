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


def test_dev_script_frees_default_ports_before_bind():
    # Issue #217: dev.sh owns the default ports — a stale server holding
    # :3000/:8000/:9000 must be reclaimed, not worked around.
    src = _read()
    for port in ("3000", "8000", "9000"):
        assert port in src, f"dev.sh must manage default port {port}"
    assert "free_port" in src or "fuser -k" in src or "lsof -ti" in src, (
        "dev.sh must reclaim occupied ports before binding"
    )


def test_dev_script_starts_viewer_by_default():
    # Issue #217: plain ./dev.sh starts everything including the
    # motion-canvas viewer; --no-viewer opts out.
    src = _read()
    assert "WITH_VIEWER=1" in src, "viewer must be on by default"
    assert "--no-viewer" in src, "opt-out flag --no-viewer missing"


def test_dev_script_forces_localhost_piston_url():
    # Issue #228: .env carries the docker-internal PISTON_API_URL
    # (http://piston:2000/...) for the containerized backend, but dev.sh
    # runs the backend on the host where `piston` does not resolve
    # (Errno -3). Local dev must force the localhost default, same as
    # NEXT_PUBLIC_API_URL above.
    src = _read()
    assert "PISTON_API_URL" in src
    assert 'export PISTON_API_URL="http://localhost:2000/api/v2"' in src, (
        "local backend must export the localhost Piston URL, not the "
        "docker-internal hostname from .env"
    )


def test_dev_script_starts_infra_via_compose_only():
    # Issue #228: bare `docker start` by container name bypasses compose
    # reconciliation (env/network/healthcheck) and fails silently.
    # Infra must come up through one idempotent compose path.
    src = _read()
    assert "docker compose up -d --no-build postgres redis piston" in src, (
        "infra must start via a single idempotent compose up"
    )
    assert "docker start" not in src, (
        "must not bypass compose with bare `docker start`"
    )


def test_dev_script_leaves_infra_running_on_exit():
    # Issue #228: normal exit stopped postgres/redis/piston, so a manual
    # `docker ps` after any run always showed Piston down. Only --down
    # stops the shared infra; the foreground exit stops just the backend.
    src = _read()
    assert "docker compose stop" in src, "--down must keep the full stop"
    tail = src.split("# ---- Frontend (foreground) ----", 1)[1]
    assert "teardown" not in tail, (
        "normal exit must not stop infra containers (only --down does)"
    )
    assert "stop_backend" in tail, "normal exit must still stop the backend"


def test_gitignore_excludes_harness_dirs():
    # Issue #217: session scaffolding stays untracked, never committed.
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for entry in (".agents/", ".claude/", ".freebuff/"):
        assert entry in gitignore, f".gitignore missing {entry}"
