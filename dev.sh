#!/usr/bin/env bash
#
# dev.sh — one-button local start for CodeCoach-AI (issue #215, #217).
#
#   ./dev.sh                Start everything: infra + backend (:8000) +
#                           frontend (:3000) + Motion Canvas viewer (:9000).
#   ./dev.sh --no-viewer    Skip the Motion Canvas viewer.
#   ./dev.sh --with-viewer  Same as the default (kept for compatibility).
#   ./dev.sh --install      Allow pnpm installs when node_modules is missing
#                           (otherwise fail closed to protect metered data).
#   ./dev.sh --down         Stop everything without starting.
#
# Data-light by design: infra containers are started, never rebuilt or
# pulled; the Next.js cache (.next) is never wiped; installs are opt-in.
# Test: python -m pytest tests/test_dev_script.py -v
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$ROOT/.dev-pids"
BACKEND_PID="$PID_DIR/backend.pid"

DEFAULT_PISTON_API_URL="http://localhost:2000/api/v2"
DEFAULT_REDIS_URL="redis://localhost:6379/0"

BACKEND_URL="http://localhost:8000"
PISTON_RUNTIMES_URL="http://localhost:2000/api/v2/runtimes"

WITH_VIEWER=1
ALLOW_INSTALL=0

log()  { printf '[dev.sh] %s\n' "$*"; }
fail() { printf '[dev.sh] ERROR: %s\n' "$*" >&2; exit 1; }
warn() { printf '[dev.sh] WARN: %s\n' "$*" >&2; }

# Issue #217: dev.sh owns the default ports. A stale server from a previous
# run (or a sibling checkout's leftover) holding :3000/:8000/:9000 is
# reclaimed so the fresh stack always binds where the docs say it will.
# Only these three host dev ports are touched — docker-mapped ports
# (postgres/redis/piston) are managed by compose, never killed here.
free_port() {
  local port="$1" pids=""
  if command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -ti :"$port" 2>/dev/null || true)"
  elif command -v ss >/dev/null 2>&1; then
    pids="$(ss -tlnp 2>/dev/null | grep ":$port " | grep -o 'pid=[0-9]*' | cut -d= -f2 | sort -u || true)"
  elif command -v fuser >/dev/null 2>&1; then
    log "Port $port may be occupied — reclaiming via fuser."
    fuser -k "$port"/tcp >/dev/null 2>&1 || true
    return 0
  else
    warn "No lsof/ss/fuser found — cannot check port $port; hoping it is free."
    return 0
  fi
  if [[ -n "$pids" ]]; then
    # shellcheck disable=SC2086
    log "Port $port in use (pids: $pids) — stopping stale dev server."
    # shellcheck disable=SC2086
    kill $pids 2>/dev/null || true
    sleep 2
    local remaining=""
    if command -v lsof >/dev/null 2>&1; then
      remaining="$(lsof -ti :"$port" 2>/dev/null || true)"
    elif command -v ss >/dev/null 2>&1; then
      remaining="$(ss -tlnp 2>/dev/null | grep ":$port " | grep -o 'pid=[0-9]*' | cut -d= -f2 | sort -u || true)"
    fi
    if [[ -n "$remaining" ]]; then
      fail "Port $port still occupied (pids: $remaining) — stop it manually and re-run."
    fi
  fi
}

stop_backend() {
  if [[ -f "$BACKEND_PID" ]]; then
    local pid
    pid="$(cat "$BACKEND_PID")"
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      log "Backend (pid $pid) stopped."
    fi
    rm -f "$BACKEND_PID"
  fi
}

teardown() {
  log "Stopping services..."
  stop_backend
  (cd "$ROOT" && docker compose stop postgres redis piston >/dev/null 2>&1) || true
  log "Docker infra (postgres, redis, piston) stopped."
}

usage() {
  sed -n '/^# dev.sh/,/^# Test:/p' "$0" | sed 's/^# \{0,1\}//'
}

for arg in ${@+"$@"}; do
  case "$arg" in
    -h|--help) usage; exit 0 ;;
    --down|down) teardown; exit 0 ;;
    --with-viewer) WITH_VIEWER=1 ;;
    --no-viewer) WITH_VIEWER=0 ;;
    --install) ALLOW_INSTALL=1 ;;
    *) fail "Unknown argument: $arg (see --help)" ;;
  esac
done

# ---- Preflight -------------------------------------------------------------
command -v docker >/dev/null 2>&1 || fail "docker not found — install Docker first."
command -v pnpm >/dev/null 2>&1 || fail "pnpm not found — install pnpm first."
docker info >/dev/null 2>&1 || fail "Docker daemon not reachable — start Docker first."
[[ -f "$ROOT/.env" ]] || fail "Missing .env — run: cp .env.example .env  (then fill in values)"

# Backend interpreter: project venv first, system python3 as fallback.
if [[ -x "$ROOT/backend/venv/bin/python" ]]; then
  PY="$ROOT/backend/venv/bin/python"
else
  PY="python3"
fi
command -v "$PY" >/dev/null 2>&1 || fail "python3 not found."
"$PY" -c "import uvicorn, fastapi" 2>/dev/null \
  || fail "Backend Python deps missing — run: cd backend && pip install -r requirements.txt"

# Load .env (entries override same-named shell variables).
set -a
# shellcheck disable=SC1091
source "$ROOT/.env"
set +a

[[ -n "${DATABASE_URL:-}" ]] || fail "DATABASE_URL is unset. Create a branch DB:
  cd backend && python3 scripts/branch_db.py init --url postgresql://codecoach:codecoach@127.0.0.1:5432/codecoach_<branch-slug>"
[[ -n "${JWT_SECRET_KEY:-}" && "${JWT_SECRET_KEY:-}" != "generate_with_openssl_rand_hex_32" ]] \
  || fail "JWT_SECRET_KEY is missing or still the placeholder from .env.example."
[[ "${GROQ_API_KEY:-}" == "" || "${GROQ_API_KEY:-}" == "your_groq_api_key_here" ]] \
  && warn "GROQ_API_KEY not set — backend will boot, AI coaching endpoints will degrade."

export PISTON_API_URL="${PISTON_API_URL:-$DEFAULT_PISTON_API_URL}"
export REDIS_URL="${REDIS_URL:-$DEFAULT_REDIS_URL}"

# CSP guard: local dev must stay same-origin (/api rewrite). An absolute
# http base inlined into the client bundle is blocked by connect-src on
# every request — force it empty and warn if .env disagrees.
if [[ -n "${NEXT_PUBLIC_API_URL:-}" ]]; then
  warn "NEXT_PUBLIC_API_URL='${NEXT_PUBLIC_API_URL}' ignored — forcing same-origin for local dev."
fi
export NEXT_PUBLIC_API_URL=""

mkdir -p "$PID_DIR"
# Ctrl-C stops the backend but leaves shared infra running for sibling
# checkouts; --down is the explicit full stop.
trap stop_backend INT TERM

# ---- Infra (Docker): postgres + redis + piston ------------------------------
# Containers are started by name when they exist; compose (no build) only
# fills in whichever are missing. Never builds or pulls (metered-data safe).
log "Starting Docker infra (postgres, redis, piston)..."
docker volume inspect piston-data >/dev/null 2>&1 \
  || docker volume create piston-data >/dev/null
need_compose=0
for _svc in postgres redis piston; do
  _cname="codecoach-$_svc"
  if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$_cname"; then
    log "$_cname already running — reusing."
  elif docker ps -a --format '{{.Names}}' 2>/dev/null | grep -qx "$_cname"; then
    log "Starting existing container $_cname..."
    docker start "$_cname" >/dev/null
  else
    need_compose=1
  fi
done
if [[ "$need_compose" == "1" ]]; then
  (cd "$ROOT" && docker compose up -d --no-build postgres redis piston)
fi

log "Waiting for infra health (60s timeout)..."
for i in $(seq 1 60); do
  if docker exec codecoach-postgres pg_isready -U codecoach >/dev/null 2>&1 \
    && docker exec codecoach-redis redis-cli ping 2>/dev/null | grep -q PONG \
    && "$PY" -c "import urllib.request; urllib.request.urlopen('$PISTON_RUNTIMES_URL', timeout=3)" >/dev/null 2>&1; then
    log "Infra healthy (postgres, redis, piston)."
    break
  fi
  if [[ "$i" == "60" ]]; then
    fail "Infra did not become healthy in 60s — run: docker compose ps && docker compose logs postgres redis piston"
  fi
  sleep 2
done

# ---- Backend (local uvicorn) -------------------------------------------------
free_port 8000
log "Starting backend (uvicorn --reload :8000)..."
(cd "$ROOT/backend" && nohup "$PY" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 \
  > "$PID_DIR/backend.log" 2>&1 & echo $! > "$BACKEND_PID")

log "Waiting for backend health (60s timeout)..."
for i in $(seq 1 30); do
  if "$PY" -c "import json, urllib.request; d=json.load(urllib.request.urlopen('$BACKEND_URL/health/', timeout=3)); assert d['status'] == 'ok'" >/dev/null 2>&1; then
    log "Backend healthy at $BACKEND_URL."
    break
  fi
  if ! kill -0 "$(cat "$BACKEND_PID")" 2>/dev/null; then
    fail "Backend died during startup — see backend log: $PID_DIR/backend.log"
  fi
  if [[ "$i" == "30" ]]; then
    fail "Backend did not become healthy in 60s — see backend log: $PID_DIR/backend.log"
  fi
  sleep 2
done

# ---- Frontend (foreground) ---------------------------------------------------
# node_modules is gitignored; on a metered connection installs are opt-in.
for _dir in frontend motion-canvas-lab; do
  if [[ "$_dir" == "motion-canvas-lab" && "$WITH_VIEWER" == "0" ]]; then
    continue
  fi
  if [[ ! -d "$ROOT/$_dir/node_modules" ]]; then
    if [[ "$ALLOW_INSTALL" == "1" ]]; then
      log "Installing $_dir dependencies (--install, may use data)..."
      (cd "$ROOT/$_dir" && pnpm install --prefer-offline)
    else
      fail "Missing $ROOT/$_dir/node_modules — re-run with --install (uses data) or install manually."
    fi
  fi
done

log ""
log "  Backend API:      $BACKEND_URL  (docs: $BACKEND_URL/docs)"
log "  Frontend:         http://localhost:3000"
if [[ "$WITH_VIEWER" == "1" ]]; then
  log "  Motion viewer:    http://localhost:9000"
fi
log "  Piston:           http://localhost:2000"
log ""
free_port 3000
if [[ "$WITH_VIEWER" == "1" ]]; then
  free_port 9000
fi
log "Press Ctrl-C to stop everything."
if [[ "$WITH_VIEWER" == "1" ]]; then
  (cd "$ROOT/frontend" && pnpm dev:all) || _rc=$?
else
  (cd "$ROOT/frontend" && pnpm dev) || _rc=$?
fi
teardown
exit "${_rc:-0}"
