#!/usr/bin/env bash
#
# dev.sh — start all CodeCoach-AI services with one command.
#
#   ./dev.sh          Start postgres + redis + piston (Docker), backend
#                     (uvicorn --reload :8000), frontend (:3000) + Motion
#                     Canvas viewer (:9000). Ctrl-C stops everything.
#   ./dev.sh --down   Stop everything without starting.
#
# Localhost-portable wiring (PISTON_API_URL, REDIS_URL) is defaulted when
# unset; secrets (DATABASE_URL, JWT_SECRET_KEY) are fail-closed.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$ROOT/.dev-pids"
BACKEND_PID="$PID_DIR/backend.pid"

# Sane local defaults — only applied when the caller/.env has not set them.
DEFAULT_PISTON_API_URL="http://localhost:2000/api/v2"
DEFAULT_REDIS_URL="redis://localhost:6379/0"

BACKEND_URL="http://localhost:8000"
PISTON_RUNTIMES_URL="http://localhost:2000/api/v2/runtimes"

log()  { printf '[dev.sh] %s\n' "$*"; }
fail() { printf '[dev.sh] ERROR: %s\n' "$*" >&2; exit 1; }
warn() { printf '[dev.sh] WARN: %s\n' "$*" >&2; }

teardown() {
  log "Stopping services..."
  if [[ -f "$BACKEND_PID" ]]; then
    local pid
    pid="$(cat "$BACKEND_PID")"
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      log "Backend (pid $pid) stopped."
    fi
    rm -f "$BACKEND_PID"
  fi
  (cd "$ROOT" && docker compose stop postgres redis piston >/dev/null 2>&1) || true
  log "Docker infra (postgres, redis, piston) stopped."
}

usage() {
  sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "${1:-}" == "--down" || "${1:-}" == "down" ]]; then
  teardown
  exit 0
fi

# ---- Preflight -------------------------------------------------------------
command -v docker >/dev/null 2>&1 || fail "docker not found — install Docker first."
command -v pnpm >/dev/null 2>&1 || fail "pnpm not found — install pnpm first."
command -v python3 >/dev/null 2>&1 || fail "python3 not found."
python3 -c "import uvicorn, fastapi" 2>/dev/null \
  || fail "Backend Python deps missing — run: cd backend && pip install -r requirements.txt"
docker info >/dev/null 2>&1 || fail "Docker daemon not reachable — start Docker first."
[[ -f "$ROOT/.env" ]] || fail "Missing .env — run: cp .env.example .env  (then fill in values)"

# Load .env (entries override any same-named shell variables).
set -a
# shellcheck disable=SC1091
source "$ROOT/.env"
set +a

# Fail-closed on secrets / required wiring.
[[ -n "${DATABASE_URL:-}" ]] || fail "DATABASE_URL is unset. Create a branch DB:
  cd backend && python3 scripts/branch_db.py init --url postgresql://codecoach:codecoach@127.0.0.1:5432/codecoach_<branch-slug>"
[[ -n "${JWT_SECRET_KEY:-}" && "${JWT_SECRET_KEY:-}" != "generate_with_openssl_rand_hex_32" ]] \
  || fail "JWT_SECRET_KEY is missing or still the placeholder from .env.example."
[[ "${GROQ_API_KEY:-}" == "" || "${GROQ_API_KEY:-}" == "your_groq_api_key_here" ]] \
  && warn "GROQ_API_KEY not set — backend will boot, AI coaching endpoints will degrade."

# Localhost-portable defaults (dev only; never override explicit values).
export PISTON_API_URL="${PISTON_API_URL:-$DEFAULT_PISTON_API_URL}"
export REDIS_URL="${REDIS_URL:-$DEFAULT_REDIS_URL}"

mkdir -p "$PID_DIR"
trap teardown INT TERM

# ---- Infra (Docker): postgres + redis + piston ------------------------------
# Reuse containers by name when they already exist (e.g. started from another
# checkout) — `compose up` would fail with a name conflict instead.
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
  (cd "$ROOT" && docker compose up -d postgres redis piston)
fi

log "Waiting for infra health (60s timeout)..."
for i in $(seq 1 60); do
  if docker exec codecoach-postgres pg_isready -U codecoach >/dev/null 2>&1 \
    && docker exec codecoach-redis redis-cli ping 2>/dev/null | grep -q PONG \
    && python3 -c "import urllib.request; urllib.request.urlopen('$PISTON_RUNTIMES_URL', timeout=3)" >/dev/null 2>&1; then
    log "Infra healthy (postgres, redis, piston)."
    break
  fi
  if [[ "$i" == "60" ]]; then
    fail "Infra did not become healthy in 60s — run: docker compose ps && docker compose logs postgres redis piston"
  fi
  sleep 2
done

# ---- Backend (local uvicorn) -------------------------------------------------
log "Starting backend (uvicorn --reload :8000)..."
(cd "$ROOT/backend" && nohup python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 \
  > "$PID_DIR/backend.log" 2>&1 & echo $! > "$BACKEND_PID")

log "Waiting for backend health (60s timeout)..."
for i in $(seq 1 30); do
  if python3 -c "import json, urllib.request; d=json.load(urllib.request.urlopen('$BACKEND_URL/health/', timeout=3)); assert d['status'] == 'ok'" >/dev/null 2>&1; then
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

# ---- Frontend + Motion Canvas viewer (foreground) ----------------------------
# JS dependencies are installed on first run only (node_modules is gitignored,
# so fresh clones/worktrees start without it).
if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  log "Installing frontend dependencies (first run, may take a few minutes)..."
  (cd "$ROOT/frontend" && pnpm install --prefer-offline)
fi
if [[ ! -d "$ROOT/motion-canvas-lab/node_modules" ]]; then
  log "Installing motion-canvas-lab dependencies (first run)..."
  (cd "$ROOT/motion-canvas-lab" && pnpm install --prefer-offline)
fi

trap teardown INT TERM
log "Starting frontend (:3000) + Motion Canvas viewer (:9000)..."
log ""
log "  Backend API:      $BACKEND_URL  (docs: $BACKEND_URL/docs)"
log "  Frontend:         http://localhost:3000"
log "  Motion viewer:    http://localhost:9000"
log "  Piston:           http://localhost:2000"
log ""
log "Press Ctrl-C to stop everything."
(cd "$ROOT/frontend" && pnpm dev:all) || _rc=$?
teardown
exit "${_rc:-0}"
