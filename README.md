# CodeCoach AI

> **A private, AI-powered coding practice platform for university students.**
> DSA practice, language curricula, and real-time AI coaching — all on a local-first PostgreSQL setup (one database per git branch, versioned promotion to live).

[![Node](https://img.shields.io/badge/node-%3E%3D20-339933?logo=node.js&logoColor=white)](./frontend/package.json)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](./backend/requirements.txt)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)](./frontend)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi)](./backend)
[![Docker](https://img.shields.io/badge/docker-compose-ready-2496ED?logo=docker&logoColor=white)](./docker-compose.yml)
[![License](https://img.shields.io/badge/license-Proprietary-red)](#license)

Private, proprietary project — no public fork/PR intake. Students work here through
assigned Issues + branches (see [Git workflow for students](#git-workflow-for-students)).
Full mandatory rules live in [AGENTS.md](./AGENTS.md).

---

## New here? Start here (10 minutes)

You are a uni student joining this repo. Do this first:

1. **Read this page**, then [CONTRIBUTING.md](./CONTRIBUTING.md) (how we work).
2. **Get the stack running** with Docker (below) — frontend `:3000`, API `:8000`, docs `:8000/docs`.
3. **Pick an Issue** (or ask for one), create your own branch + worktree, make a small change,
   run the quality gates, open a PR that says `Closes #<number>`.

```bash
cp .env.example .env          # fill GROQ_API_KEY, JWT_SECRET_KEY, DATABASE_URL (local branch DB)
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Animation viewer | http://localhost:9000 (`pnpm dev:all` boots Next.js + viewer together) |
| Piston (code execution) | http://localhost:2000/api/v2/runtimes |
| Redis | `localhost:6379` |

> The compose stack runs `backend`, `frontend`, `postgres`, `redis`, `piston`.
> PostgreSQL runs locally — each git branch gets its own database
> (`codecoach_<slug>`, see `backend/scripts/branch_db.py` + AGENTS.md).

---

## Table of Contents

- [New here? Start here (10 minutes)](#new-here-start-here-10-minutes)
- [What is CodeCoach AI?](#what-is-codecoach-ai)
- [Current state (Sep 2026)](#current-state-sep-2026)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Data Model](#data-model)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Git workflow for students](#git-workflow-for-students)
- [Mandatory rules (plain language)](#mandatory-rules-plain-language)
- [Testing & quality gates](#testing--quality-gates)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [Security](#security)
- [Roadmap & known gaps](#roadmap--known-gaps)
- [Docs map](#docs-map)
- [License](#license)

---

## What is CodeCoach AI?

An AI-assisted coding practice platform for university students:

- **DSA practice** — 107 live questions across a 26-skill taxonomy (21 roadmap buckets in
  NeetCode order + 5 supporting skills), with Python, JavaScript, and Java starter code, seeded in PostgreSQL.
- **Language curriculum** — Python Fundamentals (5 modules, 36 lessons) plus C and Java
  (5 modules, 35 lessons each), served from `/learn`.
- **AI coaching** — hint, review, explain, debug, freeform, and animate (six modes) via Groq,
  with SSE streaming and structured JSON. Runs on a platform-owned key with per-user daily caps —
  students never supply their own API keys.
- **Submit & grade** — isolated Piston execution against visible + hidden test cases.
- **Skill graph + Practice Next** — learning events → per-skill mastery
  (`new/learning/developing/strong/needs_review`) with decay, prerequisites, and a deterministic
  recommendation queue (`GET /api/skills/me/recommended-questions`).
- **Mistake-memory** — every graded submit is persisted (`submissions`), turned into an error graph
  and an SM-2 spaced-repetition rotation over your own past bugs; a forgetting-curve **Memory Graph**
  powers the student `/dashboard`.
- **Solution animations** — canonical-solution traces compiled into step animations
  (`AnimationPlayer`, Motion Canvas `viewer.html` on `:9000`).

| Audience | Need |
|---|---|
| **Struggling CS students** | Hand-holding through basics, structured learning |
| **Interview grinders** | Coached practice across 100+ target problems |
| **Non-CS majors** | Learn programming from scratch |
| **Professors** | Curriculum-aligned tool to recommend to a whole class |

---

## Current state (Sep 2026)

Living status lives in [Progress.md](./Progress.md); backlog in [Ideas.md](./Ideas.md).
Snapshot of what is actually in the code right now:

- **107 live questions**, 107/107 skill-mapped (26 skills: 21 roadmap + 5 supporting).
- **Curricula live:** Python 5/36, C 5/35, Java 5/35 lessons.
- **Coaching:** 6 modes, lesson-aware + learner-aware (weakest-3 skills + last-3 attempts injected),
  `surface=questions` (graph-aware) vs `surface=learn` (graph-free), background warm via `POST /api/coach/warm`.
- **Dashboard:** memory-first entry (`MemoryGraph` + rescue/review queues + plateau signals);
  skill graph now renders as SVG inside the **settings gear → skills tab** (guest-gated).
- **Animation viewer:** timeline is locked to the **real animation duration** (not the demo loop);
  spec `animation.steps >= 3` enforced.
- **Migrations head:** `b4c5d6e7f8a1` (Alembic; live schema moves via `alembic upgrade head` only).
- **`pnpm dev:all`** boots Next.js + the `:9000` Motion Canvas viewer together (for animation/E2E work).

Details per feature (Built / Partial / Planned) live in [Progress.md](./Progress.md) — this README
stays short on purpose.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11+, FastAPI 0.110+, Pydantic v2, Uvicorn |
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript 5 |
| **Editor** | Monaco Editor (`@monaco-editor/react`) |
| **Styling** | Tailwind CSS 3, `tailwind-merge`, `clsx`, shadcn/ui |
| **Animation** | Motion Canvas (Vite viewer on `:9000`) + `AnimationPlayer` |
| **Code Execution** | Piston (self-hosted Docker, `PistonService` adapter) |
| **AI Coach** | Groq (`openai/gpt-oss-120b` / `openai/gpt-oss-20b`, animate override) |
| **Database** | Local PostgreSQL (async SQLAlchemy), one database per git branch — **the only database** |
| **Cache / Limits** | Redis 7 — rate/request tracking, learner-context, workspace (7d), course list (30s + lock), question detail, Piston runtimes |
| **Auth** | JWT (python-jose), bcrypt, username/password |
| **Migrations** | Alembic (`backend/alembic/`) |
| **Testing** | pytest (backend), Vitest + Testing Library + MSW (frontend), Playwright (E2E) |
| **Deploy** | Docker Compose + Cloudflare Workers (OpenNext) |
| **Observability** | Structured logs, `/health` dependency checks, `X-Usage-*` headers |

---

## Architecture

**Backend — Clean Architecture / Hexagonal (Ports/Adapters).**

```
backend/app/
  api/            Thin FastAPI route handlers (auth, coach, run, submit, questions, courses,
                  progress, skills, submissions, rescue, reviews, memory, mistakes, analytics,
                  workspace, admin, health)
  services/       Business logic (groq, piston, skill_graph, sm2, memory_graph, error_graph,
                  rescue, review, animations + scene_planner, usage, submissions, course,
                  question_bank, workspace, learner_context, adapter_state_recovery …)
  ports/          Abstract interfaces (ABCs) — repositories, code executor, coaching provider
  repositories/   SQLAlchemy impls (sql_*) — PostgreSQL only
  adapters/       Concrete adapters (code_wrappers, coaching_prompts, execution_adapter,
                  submit_grading_service, response parser, formatter)
  use_cases/      Single-responsibility validation (incl. the ANIMATION gate)
  models/         Pydantic schemas (request/response + domain enums)
  core/           Database engine/session (async_session_maker), settings, security (JWT/bcrypt)
  middleware/     Rate limiting (in-process limiter), security headers (CSP, HSTS, X-Frame-Options)
  dependencies/   FastAPI Depends() injection wiring (app/api/dependencies.py)
```

**Frontend — feature-based.**

```
frontend/src/
  app/            Next.js App Router — /, /problems/[id], /learn, /dashboard, /admin, /login, /privacy …
  features/       {auth, coaching, code-execution, question, curriculum, skill-graph,
                   rescue, review, memory, analytics, animation, usage, workspace} → {hook, service, types, *.test.*}
  components/     Reusable UI (editor, chat, sidebar, header incl. gear menu, layout, rescue, visualization, admin, ui/*)
  lib/            HTTP client port/adapter (FetchClient / HttpClient), shuffle, fetch-client
  hooks/          Shared hooks (useLocalStorage, useDebounce, useWorkspaceMode)
  providers/      Theme, Auth, Toast, Usage
  e2e/            Playwright specs (auth, settings, curriculum, code-execution, animate, viewer)
```

**Key decisions**

- **PostgreSQL is the single source of truth** — questions, courses/modules/lessons,
  users, progress, submissions, coaching_interactions, execution_jobs, review_cards, rescue_queue,
  usage, and skill-graph state all live in PostgreSQL. The app never reads content from the
  filesystem at runtime. Committed JSON under `backend/data/courses/{c,java}/` is a transient
  bootstrap source for `sync_local_to_db.py` only. See
  [backend/docs/CURRICULUM_DEPLOYMENT.md](./backend/docs/CURRICULUM_DEPLOYMENT.md).
- **Platform-owned Groq key** — server-side key; per-user input/output tokens metered with daily caps.
- **Deterministic skill graph & analytics** — pure, unit-tested rules
  (`skill_graph_rules.py`, `sm2_rules.py`, `error_graph_rules.py`, `learning_analytics_rules.py`);
  analytics is bounded (1000 recent submissions, 7-day window) and fail-safe.
- **Code wrapping** — every Piston language has a `_wrap_<language>_code` adapter
  (stdin→call→stdout harness).
- **Dependency injection** — FastAPI `Depends()` + constructor injection; fully mockable for tests.
- **CSP hardening** — `default-src 'self'` with `frame-src` viewer allowlist,
  `worker-src blob:` (Monaco), `connect-src 'self' https: wss:`.
- **Idempotent sync** — seed/sync scripts are re-runnable upserts; migrations are forward-only.

---

## Data Model

| Table | Purpose |
|---|---|
| `users` | Accounts (auth, roles `user`/`admin`, plans `free`/`pro`, refresh tokens, OAuth) |
| `questions` | Bank (difficulty, category, starter_code JSON, test_cases, hints, company_tags GIN) |
| `courses`, `modules`, `lessons` | Curriculum (language, order, theory/exercise, linked question) |
| `course_progress` | Per-user lesson progress (continue-where-you-left-off) |
| `submissions` | Attempt history (code, passed, error_signature, attempt_index, status, idempotency_key) |
| `coaching_interactions`, `execution_jobs` | Adapter-state audit (`sent/completed/failed` per coach + exec call) |
| `review_cards` | SM-2 cards (unique per user+question+signature, ease, interval, due_at) |
| `rescue_queue` | Abandoned-problem re-surface (unique partial open per user+question, `due_at` 09:00) |
| `usage_*`, `rate_limit_events`, `user_daily_usage` | AI usage events, daily counters, rate-limit tracking (Redis-backed) |
| `skills`, `question_skills`, `learning_events`, `user_skill_states` | Skill graph (definitions, question↔skill, per-user events + mastery) |

Migrations in `backend/alembic/versions/` (head `b4c5d6e7f8a1`).
Tests use an isolated `codecoach_test` schema (`DATABASE_SEARCH_PATH`; per-worker
`codecoach_test_gwN` under xdist) — never production.

---

## Getting Started

### Prerequisites

- Docker + Docker Compose
- Node 20+ and `pnpm` 9+ (frontend)
- Python 3.11+ and `pip` (backend)
- A local PostgreSQL server and a Groq API key

### Quick start with Docker (recommended)

```bash
cp .env.example .env          # fill GROQ_API_KEY, JWT_SECRET_KEY, DATABASE_URL (local branch DB)
docker compose up --build
```

Then open http://localhost:3000 (app) and http://localhost:8000/docs (API).
Rebuild the affected image after code changes before you commit.

### Manual backend setup

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt -r tests/test_requirements.txt
cp .env.example .env   # or rely on root .env via python-dotenv
# Edit .env with GROQ_API_KEY and your local branch DATABASE_URL
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Manual frontend setup

```bash
cd frontend
pnpm install
cp .env.example .env.local   # set NEXT_PUBLIC_API_URL
pnpm dev                     # http://localhost:3000
pnpm dev:all                 # Next.js + Motion Canvas viewer (:9000) together
pnpm build && pnpm start     # production
```

### Piston (code execution)

```bash
docker run -d -p 2000:2000 --name piston ghcr.io/engineer-man/piston
# compose already runs piston with PISTON_DISABLE_NETWORK_ACCESS=true and PISTON_OUTPUT_MAX_SIZE=65536
```

### Seeding data

Content lives in the database. Bootstrap idempotently from committed JSON:

```bash
cd backend
python scripts/sync_local_to_db.py                 # upserts questions/courses/modules/lessons (ANIMATION gate enforced)
python scripts/seed_admin.py                       # promote auditadmin → admin
python scripts/seed_skill_graph.py                 # rescues skill graph after mapping changes
python scripts/backfill_skill_graph.py             # idempotent backfill of learning events from submissions
python scripts/seed_e2e.py                         # E2E question bank
DATABASE_URL=postgresql://... python scripts/verify_course_exercises.py  # 30/30 Piston checks for C/Java
```

See [backend/docs/CURRICULUM_DEPLOYMENT.md](./backend/docs/CURRICULUM_DEPLOYMENT.md) for
source-of-truth, seed scripts, and test-schema behavior.

---

## Environment Variables

> **Current wiring is local-first: each branch works on its own PostgreSQL database; live is written only via the versioned `branch_db.py` promotion.**
> See [Docs/TEST_ENVIRONMENT.md](./Docs/TEST_ENVIRONMENT.md).

### Backend (`.env` / process env — `backend/app/core/config.py`)

```
# Required
GROQ_API_KEY=your_groq_api_key_here
JWT_SECRET_KEY=your_jwt_secret_key                 # ≥32 chars, not committed
DATABASE_URL=postgresql://codecoach:codecoach@127.0.0.1:5432/codecoach_<branch-slug>
# Live PostgreSQL (promotion target only — never daily work):
# LIVE_DATABASE_URL=postgresql://user:password@live-host:5432/postgres

# Optional (defaults shown)
# GROQ_MODEL_EASY=openai/gpt-oss-20b
# GROQ_MODEL_MEDIUM=openai/gpt-oss-120b
# GROQ_MODEL_HARD=openai/gpt-oss-120b
# GROQ_MODEL_STREAM=openai/gpt-oss-20b
# GROQ_MODEL_ANIMATE=openai/gpt-oss-120b
DAILY_TOKEN_INPUT_CAP=250000
DAILY_TOKEN_OUTPUT_CAP=125000
USER_RATE_LIMIT_PER_MINUTE=60
COACH_WARM_ENABLED=true
COURSE_LIST_TTL_SECONDS=30
REDIS_TTL_WORKSPACE=604800                         # 7d — draft code + last-visited
REDIS_TTL_CHAT=604800                              # 7d — per-question chat history
REDIS_TTL_LAST_EXEC=604800                         # 7d — last execution / submit snapshot
WORKSPACE_CODE_MAX_BYTES=51200
CHAT_HISTORY_MAX_MESSAGES=20
PISTON_API_URL=http://localhost:2000/api/v2        # compose sets http://piston:2000/api/v2
REDIS_URL=redis://redis:6379/0
ENVIRONMENT=production                             # or testing / development
```

### Frontend (`.env.local` / Docker build args)

```
NEXT_PUBLIC_API_URL=http://localhost:8000         # browser-reachable API base (empty → same-origin /api rewrite)
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_ANIMATION_VIEWER_URL=http://localhost:9000
API_URL=http://backend:8000                        # server-side rewrite target (Docker network)
```

`NEXT_PUBLIC_*` is **inlined at build time** — rebuild after changes:
`docker compose up -d --build frontend`.

---

## Git workflow for students

Every change follows the same path. No exceptions, no work on `main`.

```bash
# 1. See who owns what, and where you are
git worktree list
git branch --show-current && git status --porcelain

# 2. Pick an Issue (or create one first — every branch needs an Issue number)
gh issue list --state open
gh issue create --title "Short description" --body "What + why"

# 3. Give yourself an isolated worktree + branch off latest main
git fetch origin
git worktree add ../CodeCoach-AI-<slug> -b <type>/<issue>-<slug> origin/main
cd ../CodeCoach-AI-<slug>
# types: feat | fix | chore | docs | refactor | test
# e.g. git worktree add ../CodeCoach-AI-42-anim -b feat/42-ai-animation-viewer origin/main

# 4. Do the work in small steps: failing test first (TDD), then the smallest fix
# 5. Before committing: explore with graphify first, then run the gates
graphify query "<what are you changing and why>"

# backend gates
cd backend && ruff check . && ruff format . --check && python -m pytest tests/unit
# frontend gates
cd frontend && pnpm lint && pnpm typecheck && pnpm test:run

# 6. Commit (caveman-review runs on the staged diff before every commit)
git add <files>
git diff --staged
# load the caveman-review skill, fix every bug:/risk:/nit: finding, re-stage, re-verify
git commit -m "feat(scope): what changed and why"
git push -u origin <type>/<issue>-<slug>

# 7. Open a PR that closes the Issue
gh pr create --fill --body "Closes #<issue-number>"
```

When merged/abandoned, clean up from the main checkout:

```bash
git worktree remove ../CodeCoach-AI-<slug>
git worktree prune
```

Rules that trip up newcomers most:

- **One Issue = one branch = one worktree.** Never share a worktree, never switch branches
  with a dirty tree — create a new worktree instead.
- **Never commit or push to `main`.** Always branch from latest `origin/main`.
- **Keep PRs small** and preserve API contracts (HTTPException → 4xx, unexpected → 5xx).

---

## Mandatory rules (plain language)

These are release-blocking. [AGENTS.md](./AGENTS.md) is the full version.

1. **Production-first** — reliable and maintainable beats quick hacks. Preserve API contracts,
   validate input at boundaries, never log or commit secrets, degrade gracefully.
2. **TDD always** — red (failing test) → green (smallest fix) → refactor.
   Bug fixes start with a regression test. Docs-only changes are the only exception.
3. **Local PostgreSQL is the only database** — no SQLite/MySQL. Each branch gets its
   own database; tests use isolated schemas/dbs only.
4. **Every question must be visualizable** — new questions need `examples[0].input`,
   a resolvable algorithm, a compilable family
   (`array/backtrack/stack/linked_list/tree/graph/grid/intervals`), and `animation.steps >= 3`.
   The `ANIMATION` gate is not skippable (except local offline tests without Piston).
5. **Graphify-first exploration** — `graphify query` / `path` / `explain` before grep/read;
   `graphify update .` after code changes.
6. **Review before every commit** — run the `caveman-review` skill on the staged diff and fix
   **all** findings (including nits) before committing.

---

## Testing & quality gates

CI runs the same gates. Keep the whole suite green before finishing any change.

### Backend (pytest — `backend/tests/README.md`)

```bash
cd backend
pip install -r requirements.txt -r tests/test_requirements.txt
DATABASE_URL=postgresql://codecoach:codecoach@127.0.0.1:5433/codecoach_test \
  python -m pytest tests/unit/            # 82 files
python -m pytest tests/integration/       # 33 files (needs isolated Postgres schema)
python -m pytest tests/contract/          # 1 file (OpenAPI response contracts)
python -m pytest tests/security/          # 5 files
python -m pytest tests/performance/       # 2 files
python -m pytest tests/migrations/        # 2 files
python -m pytest tests/simulation/        # 2 files (skill-graph)
python -m pytest                          # all tiers; coverage via qa/enforce_coverage_budget.py
ruff check . && ruff format . --check     # lint gate
```

Shared auth builders live in `tests/fixtures/auth_helpers.py`; the seed bank +
107 live ids (`fixtures/live_question_ids.json`) come from `conftest.py`.
Flaky tests belong in the quarantine manifest (`tests/enforce_flaky_quarantine.py`), not the suite.

### Frontend (Vitest)

```bash
cd frontend
pnpm install
pnpm test:run                    # 80 files (Vitest + Testing Library + MSW)
pnpm lint                        # ESLint (0 warnings)
pnpm typecheck                   # tsc --noEmit (0 errors)
```

### E2E (Playwright)

```bash
cd frontend
pnpm exec playwright install --with-deps
# needs backend :8000 + frontend :3000 + Motion Canvas viewer :9000 (use pnpm dev:all)
npx playwright test --project=chromium   # 15 specs (viewer specs need :9000)
```

---

## API Reference

Interactive docs at `/docs` (Swagger) and `/redoc`. Selected routes:

| Area | Method & Path | Auth | Notes |
|---|---|---|---|
| **Health** | `GET /health`, `GET /health/` | — | Dependency checks (`questions_db`, `piston`, `redis`) |
| **Auth** | `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/refresh` | — / Bearer | JWT username/password |
| **Questions** | `GET /api/questions`, `GET /api/questions/{id}`, `GET /api/questions/search?q=` | — | Paginated list + summary-column search |
| **Run** | `POST /api/run` (+ `question_id` optional crash capture) | Optional | Piston; validation `POST /api/run/validate` |
| **Submit** | `POST /api/submit` | Bearer | Grades + submission + SM-2 observe + adapter-state tracking |
| **Submissions** | `GET /api/submissions/me` | Bearer | Own attempt history |
| **Coach** | `POST /api/coach`, `POST /api/coach/stream` (SSE), `POST /api/coach/warm`, `GET /api/coach/interactions` | Bearer | 6 modes, per-user daily caps, `X-Usage-*` headers |
| **Skills** | `GET /api/skills/graph`, `GET /api/skills/me/skills`, `GET /api/skills/boilerplate`, `GET /api/skills/me/recommended-questions` | Bearer | Mastery + roadmap view + Practice Next |
| **Mistakes** | `GET /api/mistakes/graph` | Bearer | Error graph from attempt history |
| **Reviews** | `GET /api/reviews/due`, `POST /api/reviews/{id}/grade` | Bearer | SM-2 queue |
| **Memory** | `GET /api/memory/graph` | Bearer | Forgetting-curve topics |
| **Analytics** | `GET /api/analytics/signals` | Bearer | Plateau signals (7d window) |
| **Rescue** | `GET /api/rescue/due`, `POST /api/rescue/{id}/abandon\|complete\|dismiss` | Bearer | Re-surface queue ("Back tomorrow") |
| **Courses** | `GET /api/courses`, `GET /api/courses/{id}`, lessons, progress | Bearer (list also anonymous, cached) | Curriculum + `/api/progress` |
| **Workspace** | `PUT/GET/DELETE /api/workspace/code/{id}`, `GET /api/workspace/last-visited`, `GET /api/workspace/chat/{id}`, `GET /api/workspace/meta/{id}` | Bearer | Redis-persisted drafts, chat, resume (7d) |
| **Admin** | `GET /api/admin/*` (stats, users, questions, courses, usage, validation) | Admin | Role-gated `admin`/`super_admin` |
| **Debug** | `GET /debug/*` | — | Dev-only diagnostics (404 in production) |

Error semantics: `HTTPException` → 4xx client, unexpected → 5xx via global handler;
rate-limit 429 via in-process limiter + `usage` middleware.

---

## Project Structure

```
CodeCoach-AI/
├── backend/
│   ├── app/
│   │   ├── api/               # coach, run, submit, submissions, questions, skills, mistakes,
│   │   │                      # reviews, memory, rescue, courses, progress, workspace, admin, auth, health, debug
│   │   ├── adapters/          # code_wrappers, coaching_prompts, execution_adapter,
│   │   │                      # submit_grading_service, response parser, formatter
│   │   ├── use_cases/         # question validation (structure, tests, starter, solution, animation gate …)
│   │   ├── services/          # groq, piston, skill_graph, sm2, memory_graph, error_graph,
│   │   │                      # rescue, review, animations + scene_planner, usage, submissions, course,
│   │   │                      # question_bank, workspace, learner_context, adapter_state_recovery …
│   │   ├── repositories/      # sql_* (PostgreSQL only)
│   │   ├── ports/             # Abstract interfaces (ABCs)
│   │   ├── models/            # Pydantic schemas + domain enums
│   │   ├── core/              # database (async engine), config (get_settings), security (JWT/bcrypt)
│   │   ├── middleware/        # rate_limit (in-process limiter), security_headers (CSP)
│   │   └── dependencies/      # FastAPI Depends() wiring (app/api/dependencies.py)
│   ├── alembic/               # migrations (head b4c5d6e7f8a1)
│   ├── scripts/               # sync_local_to_db, seed_admin, seed_skill_graph, backfill_skill_graph,
│   │                            # seed_e2e, verify_course_exercises, animate_coverage
│   ├── tests/                 # unit, integration, contract, security, performance, simulation, migrations
│   └── docs/                  # CURRICULUM_DEPLOYMENT.md
├── frontend/
│   └── src/
│       ├── app/               # /, /problems, /problems/[id], /learn, /dashboard, /admin, /login, /privacy …
│       ├── features/          # auth, coaching, code-execution, question, curriculum, skill-graph,
│       │                      # rescue, review, memory, animation, usage → {hook, service, types, *.test.*}
│       ├── components/        # editor (Monaco), chat, sidebar, header (gear menu), layout, rescue, visualization, admin, ui/*
│       ├── lib/               # http-client (FetchClient), fetch-client, shuffle, utils
│       ├── hooks/             # useLocalStorage, useDebounce, useWorkspaceMode …
│       ├── providers/         # Theme, Auth, Toast, Usage
│       └── e2e/               # Playwright specs (auth, settings, curriculum, code-execution, animate, viewer)
├── motion-canvas-lab/         # Motion Canvas project (viewer.html, scenes) — Vite on :9000
├── graphify-out/              # Code knowledge graph artifacts (graph.json, GRAPH_REPORT.md, wiki/)
├── docker-compose.yml         # backend, frontend, postgres, redis, piston
├── docker-compose.dev.yml     # dev override
└── Makefile                   # test, lint, graphify shortcuts
```

---

## Deployment

- **Docker Compose (production):** `docker compose up -d --build` builds `pip install` /
  `npm run build` into images. No volume mounts; `PistonService` + `Redis` + `Postgres` wired via env.
- **Cloudflare Workers (frontend):** OpenNext build — `NEXT_PUBLIC_*` must be set as build args,
  not runtime env.
- **Live migrations:** `alembic upgrade head` (live schema moves via migrations only).
- **Health:** `GET /health` checks `questions_db`, `piston`, `redis`; Docker `HEALTHCHECK` gates `backend`.

---

## Security

- Input validated at API boundaries (Pydantic); auth via JWT + bcrypt; role-gated admin routes.
- Rate limiting via in-process limiter (`middleware/rate_limit.py`) + `UsageService` token caps;
  429 → `Retry-After` + `X-Usage-*`.
- Security headers: `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy`,
  `Permissions-Policy`, and CSP (`default-src 'self'` + viewer allowlist, `worker-src blob:` for Monaco).
- Secrets only from `.env` / env — never committed or logged; least privilege on all auth/authz paths.
- See `backend/tests/security/` for 5 committed security suites.

---

## Roadmap & known gaps

Short version — full status in [Progress.md](./Progress.md), ideas in [Ideas.md](./Ideas.md):

- **Done:** 107 questions, skill graph + Practice Next, mistake-memory (submissions + error graph +
  SM-2 + Memory Graph + analytics), rescue contract, learner-aware coaching + warm prefetch,
  workspace persistence (7d Redis), adapter-state durability, C + Java curricula.
- **Missing:** attempt-journey animated replay (Idea #5), interview theater session engine (Idea #6),
  generic time-travel debugging for student code (Idea #7), classroom/professor dashboard (Idea #2),
  DBMS/SQL, OOP/Design Patterns, Web Dev, MCQ question type.
- **Next cheapest win:** reverse interview (`CoachingMode.SENIOR`, Idea #8).

---

## Docs map

| Doc | What it is |
|---|---|
| README (this page) | Onboarding + current state |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | How we work day-to-day (setup, branches, tests, conventions) |
| [AGENTS.md](./AGENTS.md) | Mandatory rules (production, TDD, local-first DB, worktrees, review) |
| [Progress.md](./Progress.md) | Living status — kept in sync with code |
| [Ideas.md](./Ideas.md) | Backlog — 9 numbered ideas + honourable mentions |
| [backend/docs/CURRICULUM_DEPLOYMENT.md](./backend/docs/CURRICULUM_DEPLOYMENT.md) | Curriculum source-of-truth + seed scripts |
| [Docs/TEST_ENVIRONMENT.md](./Docs/TEST_ENVIRONMENT.md) | Local-first DB wiring + verification |
| [backend/tests/README.md](./backend/tests/README.md) | How to run each backend test tier |

- **Issues:** internal tracker only (no public GitHub Issues intake).
- **Contact:** see `.env.example` / `Docs/TEST_ENVIRONMENT.md` for TEST refs; ask a maintainer
  for anything else.

---

## License

Proprietary — closed source. No public distribution, forking, or external contribution.
Internal use only for the CodeCoach AI team and its university partners.
