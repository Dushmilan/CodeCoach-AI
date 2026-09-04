# CodeCoach AI

> **A private, AI-powered coding practice platform for university students.**
> DSA practice, language curricula, and real-time AI coaching — all on a single Supabase/PostgreSQL database.

[![Node](https://img.shields.io/badge/node-%3E%3D20-339933?logo=node.js&logoColor=white)](./frontend/package.json)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](./backend/requirements.txt)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)](./frontend)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi)](./backend)
[![Docker](https://img.shields.io/badge/docker-compose-ready-2496ED?logo=docker&logoColor=white)](./docker-compose.yml)
[![License](https://img.shields.io/badge/license-Proprietary-red)](#license)

Private, proprietary project — no public fork/PR intake. See [AGENTS.md](./AGENTS.md) for production-first engineering rules.

---

## Table of Contents

- [What is CodeCoach AI?](#what-is-codecoach-ai)
- [Who is it for?](#who-is-it-for)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Data Model](#data-model)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Development](#development)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [Security](#security)
- [Roadmap](#roadmap)
- [Known Gaps](#known-gaps)
- [License](#license)

---

## What is CodeCoach AI?

CodeCoach AI is an AI-assisted coding practice platform for university students. It combines:

- **DSA practice** — 107 live questions (`backend/tests/fixtures/live_question_ids.json`) across a 26-skill taxonomy (21 roadmap buckets in NeetCode order + 5 supporting skills) with Python, JavaScript, and Java starter code, seeded in Supabase.
- **Language curriculum** — Python Fundamentals (5 modules, 36 lessons: 21 theory + 15 exercises) plus C Programming and Java Programming (5 modules, 35 lessons each: 20 theory + 15 exercises). All content is served from `/learn`; the data model supports arbitrary languages.
- **AI coaching** — hint, review, explain, debug, freeform, and animate (six modes) via Groq, with SSE streaming and structured JSON responses.
- **Submit & grade** — isolated Piston execution against visible + hidden test cases, with pass/fail reporting.
- **Skill graph** — learning events → per-skill mastery (new/learning/developing/strong/needs_review), decay, prerequisites, and a deterministic **Practice Next** recommendation queue.
- **Mistake-memory** — every graded submit is persisted (`submissions`), turned into an error graph and an SM-2 spaced-repetition rotation over the learner's own past bugs; a forgetting-curve **Memory Graph** powers the student `/dashboard`.

Coaching runs on a platform-owned Groq key with per-user daily token caps — students never supply their own API keys.

## Who is it for?

| Audience | Need |
|---|---|
| **Struggling CS students** | Hand-holding through basics, structured learning |
| **Interview grinders** | Coached practice across 100+ target problems |
| **Non-CS majors** | Learn programming from scratch |
| **Professors** | Curriculum-aligned tool to recommend to a whole class |

## Features

State is kept in sync with code — audited Sep 04, 2026 on branch `docs/no-issue-docs-sync` (see [Progress.md](./Progress.md) and [Ideas.md](./Ideas.md)).

### Built

| Feature | Description |
|---|---|
| **AI Coaching** | 6 modes (hint, review, explain, debug, freeform, animate) via Groq — structured JSON + SSE streaming (`POST /api/coach`, `POST /api/coach/stream`); lesson-aware + **learner-aware** (`LearnerContextService`: weakest-3 skills + last-3 attempts injected); `surface=questions` (graph-aware) vs `surface=learn` (graph-free); background warm via `POST /api/coach/warm` (`useCoachWarm`) |
| **Code Execution** | Piston container — Python, JavaScript, Java; smart code wrapping for stdin→call→stdout harness (`GET/POST /api/run`, `/api/run/validate`, `/api/run/languages`); runtime-version self-heal + result cache |
| **Submit & Grade** | `POST /api/submit` (idempotent `LearningEvent sub:{id}` → skill graph) and `POST /api/run` (optional `question_id` crash capture); visible + hidden cases, `GET /api/submissions/me` history; graded via `submit_grading_service` with adapter-state tracking |
| **Question Bank** | DSA questions with CRUD, search, filtering by difficulty/category/company tags + `/stats` aggregates (SQL `COUNT(*)` pushdown); paginated list + summary-column search; admin delete invalidates detail cache (`/api/questions`) |
| **Curriculum** | Python Fundamentals (5/36), C Programming (5/35), Java Programming (5/35) — `/learn` dashboard, module tree, lesson viewer, adjacent-lesson navigation, progress tracking; anonymous course list served from Redis (30s + stampede lock) |
| **Lesson-aware Coaching** | Lesson context injected into every AI prompt; theory vs exercise layouts; required for `surface=learn` |
| **Solution Animations** | Generate → validate → compile → play structured step animations (animate mode, canonical-solution `__trace` pipeline via `trace_instrumenter`/`trace_parser`/`SolutionAnimationService`, 8-family scene planner with complexity resolution + 96-step downsampling + `lint_quality` gate, flow-map retired; `AnimationPlayer`, Motion Canvas `viewer.html` on `:9000`) |
| **Skill Graph** | Learning events (run, submit, hint, diagnosis, review) → mastery/status, trends, decay, prerequisite-aware graphs (tables `skills`, `question_skills`, `learning_events`, `user_skill_states`; 26 skills = 21 roadmap + 5 supporting, 107/107 mapped) + idempotent `backfill_skill_graph.py` |
| **Practice Next** | `GET /api/skills/me/recommended-questions` deterministic queue respecting prerequisites (+ `GET /api/skills/boilerplate` roadmap view); `useRecommendedQuestions` on `/problems` with `learner-context-invalidated` silent refresh |
| **Rescue Contract** | Never-alone intervention: `useRescueContract` T1(4m)→T2(+5m AI hint)→T3(+5m re-plan), `RescueIntervention` + `ProblemFlowMap` (static checkpoint list via `rescue.checkpoints.ts`, flow-map retired), durable `rescue_queue` (`f2a3b4c5d6e7`; stored statuses `abandoned/completed/dismissed`, `due` derived) + `/api/rescue/*` re-surface (`Back tomorrow` on `/problems`) |
| **Adapter-State Durability** | Every coach/exec/submit call tracked `sent → completed/failed` (`coaching_interactions`, `execution_jobs`, `submissions.status`, migration `b4c5d6e7f8a1`); stale-row recovery worker; `GET /api/coach/interactions` audit |
| **Workspace Persistence** | Draft code + last-visited + AI chat + last exec/submit snapshot in Redis (7d TTL, caps 51KB / 20 msgs / 5k chars, degrade-open) via `WorkspaceService` + `PUT/GET/DELETE /api/workspace/*`; `useWorkspace` hydrate + 800ms debounce; last-visited resume on `/problems` |
| **Attempt History** | `submissions` table (`d9e1f2a3b4c5`, attempt_index, error_signature) — every graded submit + crashed `run?question_id`; foundation for #1/#3/#5 |
| **Error Graph** | `GET /api/mistakes/graph` — per-user mistake graph derived from attempt history (signatures, occurrences, affected questions, first/last seen, resolution) |
| **Spaced Repetition** | SM-2 rotation over own bugs (`review_cards` `a3b4c5d6e7f8`, `/api/reviews/due`, `POST /api/reviews/{id}/grade`); `run` and `submit` observe failures/passes best-effort |
| **Memory Graph** | Forgetting-curve dashboard — `GET /api/memory/graph` aggregates `review_cards` + `submissions` by `category` into per-topic `TopicMemory` (dueCount, avgInterval, daysSinceLastTouch, energyCostMinutes); `MemoryGraph.tsx` + student `/dashboard` |
| **Learning Analytics** | Plateau signals — `GET /api/analytics/signals` derives `AnalyticsSignal` (type `plateau`, skill, `evidence{failures,passes,window_days}`) from bounded recent `submissions` (1000, 7-day window); `LearningSignals.tsx` banner on `/dashboard` |
| **Auth** | JWT email/password (bcrypt, refresh tokens) + Supabase OAuth (Google) — `Continue with Google` |
| **Usage Metering** | Per-user daily input/output token caps, `X-Usage-*` headers, Redis-backed limits |
| **Plans & Gates** | Per-user plan field and quota-gated coaching (free 20 req/day, paid 500), usage bar, `UpgradeModal` |
| **Admin Panel** | Dashboard, users, questions, curriculum, validation, usage/rate-limit analytics, abuse reports; Header shows Dashboard + Admin links (role-gated) |
| **Workspace UX** | Monaco editor (CSP `worker-src blob:` fix `e51ddf4`), dark/light theme, resizable panels, onboarding tour, toasts, hydration guard, `/dashboard` memory-first entry, last-visited resume |
| **Infrastructure** | Docker Compose (backend, frontend, redis, piston), Alembic (head `b4c5d6e7f8a1`), Supabase as the single DB, Cloudflare Workers (OpenNext) build |
| **Learner-aware Coaching** | `LearnerContextService` + `cache_keys` central TTLs + `GroqService` v7 hash + prompt injection; invalidated on `submit`/`skills`; pre-warmed via `POST /api/coach/warm` |

### Partial / foundation

| Feature | What exists | What's missing |
|---|---|---|
| **Curriculum breadth** | Python, C, Java live (F5) | DBMS/SQL, OOP/Design Patterns, Web Dev, MCQ — Phase 3; `backend/data/courses` only `c/`+`java/` |
| **Attempt-journey replay** | `ProblemFlowMap` static list + `submissions` history persisted + workspace Redis journey (draft code, chat, last exec/submit); animation infra for canonical solutions only (8-family planner + `#141` gates) | Animated replay timeline over own journey + "where you errored" highlights (Idea #5) |
| **Interview theater** | SSE streaming + Monaco `onCodeChange` + coach `surface` split + `POST /api/coach/warm` prefetch | Session/event engine + `InterviewSessionService` + `InterviewTheater` UI (Idea #6) |
| **Time-travel debugging** | `trace_instrumenter`/`trace_parser` for `animate` only (now with complexity + downsample + `lint_quality` gates) | Generic AST tracing for student code + `POST /trace` + `TimelineScrubber` (Idea #7) |
| **Classroom / Segment moat** | Courses + progress tracking + anonymously cached course list | Professor/class dashboard, roster model (Idea #2) |

### Planned — audited Sep 04

| Phase | Scope |
|---|---|
| **Phase 1 — DSA** | Learner-context shipped; coach surfaces + warm landed; attempt-journey replay (unblocked by `submissions` + workspace journey); onboarding polish |
| **Phase 2 — Curriculum** | Context-aware coaching per lesson (now learner-aware); ML/PromptEng/R/JS source JSON parked |
| **Phase 3 — Expand** | DBMS/SQL, OOP/Design Patterns, Web Dev, theory/MCQ type, classroom dashboard (Idea #2) |
| **Next up** | **Idea #8 Reverse interview** (`CoachingMode.SENIOR` + junior persona) — cheapest win, validates persona engine for #6 |
| **Backlog** | See [Ideas.md](./Ideas.md) — 9 numbered ideas + honourable mentions (Idea #7 student-code `POST /trace`, #6 `InterviewTheater`, flow-map retired) |

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11+, FastAPI 0.110+, Pydantic v2, Uvicorn |
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript 5 |
| **Editor** | Monaco Editor (`@monaco-editor/react`) |
| **Styling** | Tailwind CSS 3, `tailwind-merge`, `clsx`, shadcn/ui |
| **Animation** | Motion Canvas (Vite viewer on `:9000`) + `AnimationPlayer` |
| **Code Execution** | Piston (self-hosted Docker, `PistonService` adapter) |
| **AI Coach** | Groq (`openai/gpt-oss-120b` / `openai/gpt-oss-20b`, animate override) via `api.groq.com/openai/v1` |
| **Database** | Supabase PostgreSQL (async SQLAlchemy) — **the only database** |
| **Cache / Limits** | Redis 7-alpine — rate/request tracking, learner-context, workspace (7d), anonymous course list (30s + lock), question detail, Piston runtimes |
| **Auth** | JWT (python-jose), bcrypt, Supabase OAuth (Google) |
| **Migrations** | Alembic (`backend/alembic/`) |
| **Testing** | pytest (backend), Vitest + Testing Library + MSW (frontend), Playwright (E2E) |
| **Deploy** | Docker Compose + Cloudflare Workers (OpenNext) |
| **Observability** | Structured logs, `/health` dependency checks, `X-Usage-*` headers |

## Architecture

**Backend — Clean Architecture / Hexagonal (Ports/Adapters).**

```
backend/app/
  ports/          Abstract interfaces (ABCs) — repositories, code executor, coaching provider
  adapters/       Concrete adapters (code_wrappers, coaching_prompts, coaching_adapter,
                  execution_adapter, submit_grading_service, response parser, formatter)
  use_cases/      Single-responsibility validation logic (question validation, incl. ANIMATION gate)
  services/       Business logic wrapping ports (Groq, Piston, skill_graph, sm2, memory_graph,
                   error_graph, learning_analytics, rescue, review, animations + scene_planner,
                   usage, submissions, course (cached), question_bank, workspace,
                   learner_context, adapter_state_recovery)
  repositories/   SQLAlchemy impls (sql_*) — Supabase/PostgreSQL only
  api/            Thin FastAPI route handlers (auth, coach, run, submit, questions, courses,
                   progress, skills, submissions, rescue, reviews, memory, mistakes, analytics,
                   workspace, admin, health)
  models/         Pydantic schemas (request/response + domain enums — TopicMemory, AnalyticsSignal, …)
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
                   (coaching includes `use-coach-warm`; skill-graph includes `SkillGraphInline`)
  components/     Reusable UI (editor, chat, sidebar, header, layout, rescue, visualization, admin, ui/*)
  lib/            HTTP client port/adapter (FetchClient / HttpClient), shuffle, fetch-client
  hooks/          Shared hooks (useLocalStorage, useDebounce, useWorkspaceMode)
  providers/      Theme, Auth, Toast, Usage
  e2e/            Playwright specs (auth, settings, curriculum, code-execution, animate, viewer)
```

**Key decisions**

- **Supabase/PostgreSQL is the single source of truth** — questions, courses/modules/lessons, users, progress, submissions, coaching_interactions, execution_jobs, review_cards, rescue_queue, usage, and skill-graph state all live in PostgreSQL; the app never reads content from the filesystem at runtime. Committed JSON under `backend/data/courses/{c,java}/` is a transient bootstrap source consumed by `sync_local_to_db.py` only. See [backend/docs/CURRICULUM_DEPLOYMENT.md](./backend/docs/CURRICULUM_DEPLOYMENT.md).
- **Platform-owned Groq key** — server-side key; per-user input/output tokens metered with daily caps on coach endpoints.
- **Deterministic skill graph & learning analytics** — mastery + plateau signals derived via pure, unit-tested rules (`skill_graph_rules.py`, `sm2_rules.py`, `error_graph_rules.py`, `learning_analytics_rules.py`); recommendations respect taxonomy prerequisites; analytics is bounded (1000 recent submissions, 7-day window) and fail-safe (500 → empty list).
- **Code wrapping** — every Piston language has a `_wrap_<language>_code` adapter converting bare function definitions into a stdin→call→stdout harness.
- **Dependency injection** — FastAPI `Depends()` + constructor injection for use-cases; fully mockable for tests.
- **CSP hardening** — `default-src 'self'` with `frame-src 'self' ${NEXT_PUBLIC_ANIMATION_VIEWER_URL||http://localhost:9000}` for the viewer iframe, `worker-src blob:`, `connect-src 'self' https: wss:` (see `frontend/next.config.js` + `backend/app/middleware/security_headers.py`).
- **Idempotent sync** — seed/sync scripts are re-runnable upserts; migrations are forward-only Alembic heads.

## Data Model

| Table | Purpose |
|---|---|
| `users` | Accounts (auth, roles `user`/`admin`, plans `free`/`pro`, refresh tokens, OAuth) |
| `questions` | Bank (difficulty, category, starter_code JSON, test_cases, hints, company_tags GIN) |
| `courses`, `modules`, `lessons` | Curriculum (language, order, theory/exercise, linked question) |
| `course_progress` | Per-user lesson progress (continue-where-you-left-off) |
| `submissions` | Attempt history (user_id, question_id, language, code, passed, error_signature, attempt_index, status, idempotency_key, execution_job_id, created_at) — `d9e1f2a3b4c5` + `b4c5d6e7f8a1` |
| `coaching_interactions`, `execution_jobs` | Adapter-state audit (sent/completed/failed per coach + exec call, stale-row recovery) — `b4c5d6e7f8a1` |
| `review_cards` | SM-2 cards (user_id, question_id, error_signature unique, state active/scheduled, ease, interval_days, lapses, due_at) — `a3b4c5d6e7f8` |
| `rescue_queue` | Abandoned-problem re-surface (user_id, question_id unique partial open, due_at 09:00, dismissed) — `f2a3b4c5d6e7` |
| `usage_*`, `rate_limit_events`, `user_daily_usage` | AI usage events, daily counters, rate-limit tracking (Redis-backed) |
| `skills`, `question_skills`, `learning_events`, `user_skill_states` | Skill graph (definitions, question↔skill, per-user events + mastery) — `5bb567dd8649` + taxonomy prune `c9d0e1f2a3b4` (26 skills: 21 roadmap + 5 supporting) |

> **Live DB (Supabase `qazpxjpcvsjbmgbzuxxp`, TEST, Sep 04, 2026 — audited):** `alembic current` = `b4c5d6e7f8a1` (head); `public` holds 107 live questions, `courses`/`modules`/`lessons` seeded (Python 5/36 + C 5/35 + Java 5/35), `review_cards`/`rescue_queue`/`coaching_interactions`/`execution_jobs` verified, 107/107 skill-mapped (F3; 26 skills: 21 roadmap + 5 supporting). No `class`/`roster`/`trace` tables. Flow-map retired. `CoachingMode` has 6 modes (no `SENIOR`).

Migrations in `backend/alembic/versions/` (initial, admin, usage, user plan, skill-graph, submissions, review_cards, rescue_queue, taxonomy prune, adapter-state). Tests use an isolated `codecoach_test` schema (`DATABASE_SEARCH_PATH`; per-worker `codecoach_test_gwN` under xdist).

## Getting Started

### Prerequisites

- Docker + Docker Compose
- Node 20+ and `pnpm` 9+ (frontend)
- Python 3.11+ and `pip` (backend)
- A Supabase project (PostgreSQL) and a Groq API key

### Quick start with Docker

```bash
cp .env.example .env          # fill GROQ_API_KEY, JWT_SECRET_KEY, DATABASE_URL, Supabase keys
docker compose up --build
```

- **Frontend:** http://localhost:3000 (CSP `frame-src` allows Motion Canvas viewer on `:9000`)
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Piston:** http://localhost:2000/api/v2/runtimes
- **Redis:** 6379

The compose stack provisions `backend`, `frontend`, `redis`, `piston`; PostgreSQL is external Supabase (or the local `codecoach_test` Postgres at `127.0.0.1:5433` for tests).

### Manual backend setup

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt -r tests/test_requirements.txt
cp .env.example .env   # or rely on root .env via python-dotenv
# Edit .env with GROQ_API_KEY and Supabase DATABASE_URL
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# or: python -m app.main
```

### Manual frontend setup

```bash
cd frontend
pnpm install
cp .env.example .env.local   # set NEXT_PUBLIC_API_URL, Supabase anon keys
pnpm dev                     # http://localhost:3000
pnpm build && pnpm start     # production
```

### Piston (code execution)

```bash
docker run -d -p 2000:2000 --name piston ghcr.io/engineer-man/piston
# compose already runs piston with PISTON_DISABLE_NETWORK_ACCESS=true and PISTON_OUTPUT_MAX_SIZE=65536
```

### Seeding data

Content lives in the database. Initial data can be bootstrapped idempotently from committed JSON:

```bash
cd backend
python scripts/sync_local_to_db.py                 # uses DATABASE_URL; upserts questions/courses/modules/lessons (ANIMATION full-validate gate enforced)
python scripts/seed_admin.py                       # promote auditadmin → admin
python scripts/seed_skill_graph.py                 # rescues skill graph after mapping changes (upserts taxonomy kinds)
python scripts/backfill_skill_graph.py             # idempotent backfill of learning events from submissions
python scripts/seed_e2e.py                         # E2E question bank
DATABASE_URL=postgresql://... python scripts/verify_course_exercises.py  # 30/30 Piston checks for C/Java
```

See [backend/docs/CURRICULUM_DEPLOYMENT.md](./backend/docs/CURRICULUM_DEPLOYMENT.md) for source-of-truth, seed scripts, and test-schema behavior.

## Environment Variables

> **Current TEST wiring is Supabase `qazpxjpcvsjbmgbzuxxp` (TEST DB + TEST OAuth). Production is NOT configured.** See [Docs/TEST_ENVIRONMENT.md](./Docs/TEST_ENVIRONMENT.md).

### Backend (`.env` / process env — `backend/app/core/config.py`)

```
# Required
GROQ_API_KEY=your_groq_api_key_here
JWT_SECRET_KEY=your_jwt_secret_key                 # ≥32 chars, not committed
DATABASE_URL=postgresql://postgres.<ref>.<region>.pooler.supabase.com:6543/postgres?pgbouncer=true
# Session-mode pooler for migrations/tooling (optional, used by alembic/scripts):
# DIRECT_URL=postgresql://postgres.<ref>.<region>.pooler.supabase.com:5432/postgres

# Optional Groq model overrides (defaults)
# GROQ_MODEL_EASY=openai/gpt-oss-20b
# GROQ_MODEL_MEDIUM=openai/gpt-oss-120b
# GROQ_MODEL_HARD=openai/gpt-oss-120b
# GROQ_MODEL_STREAM=openai/gpt-oss-20b
# GROQ_MODEL_ANIMATE=openai/gpt-oss-120b
DAILY_TOKEN_INPUT_CAP=250000
DAILY_TOKEN_OUTPUT_CAP=125000
USER_RATE_LIMIT_PER_MINUTE=60
COACH_WARM_ENABLED=true                          # background learner-context pre-warm on question enter
COURSE_LIST_TTL_SECONDS=30                       # anonymous course-list Redis cache
REDIS_TTL_WORKSPACE=604800                       # 7d — draft code + last-visited
REDIS_TTL_CHAT=604800                            # 7d — per-question chat history
REDIS_TTL_LAST_EXEC=604800                       # 7d — last execution / submit snapshot
WORKSPACE_CODE_MAX_BYTES=51200
CHAT_HISTORY_MAX_MESSAGES=20
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=sb_publishable_...              # publishable key (public)
PISTON_API_URL=http://localhost:2000/api/v2        # Docker compose sets http://piston:2000/api/v2
REDIS_URL=redis://redis:6379/0
ENVIRONMENT=production                             # or testing / development
```

> Supabase now issues `sb_publishable_...` (public) and `sb_secret_...` (server-only) instead of legacy `anon`/`service_role` JWTs. Dashboard → **Settings → API Keys**.

### Frontend (`.env.local` / Docker build args — `frontend/next.config.js`)

```
NEXT_PUBLIC_API_URL=http://localhost:8000         # browser-reachable API base (empty → same-origin /api rewrite)
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_...
NEXT_PUBLIC_ANIMATION_VIEWER_URL=http://localhost:9000  # CSP frame-src + viewer iframe (Vite :9000 in E2E)
API_URL=http://backend:8000                        # server-side rewrite target (Docker network)
```

`NEXT_PUBLIC_*` is **inlined at build time** — the frontend `Dockerfile` declares them and `docker-compose.yml` wires them from the root `.env`. Rebuild is required after changes: `docker compose up -d --build frontend`.

## API Reference

Interactive docs at `/docs` (Swagger) and `/redoc`. Selected routes:

| Area | Method & Path | Auth | Notes |
|---|---|---|---|
| **Health** | `GET /health`, `GET /health/` | — | Dependency checks (`questions_db`, `piston`, `redis`) |
| **Auth** | `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/refresh` | — / Bearer | JWT + Supabase OAuth callback |
| **Questions** | `GET /api/questions`, `GET /api/questions/{id}`, `GET /api/questions/search?q=` | — | Paginated list + summary-column search; trailing slash handled (`/api/questions` + `/api/questions/`) |
| **Run** | `POST /api/run` (+ `question_id` optional crash capture) | Optional | Piston; validation `POST /api/run/validate` |
| **Submit** | `POST /api/submit` | Bearer | Grades + best-effort submission + SM-2 observe + adapter-state tracking |
| **Submissions** | `GET /api/submissions/me` | Bearer | Own attempt history |
| **Coach** | `POST /api/coach`, `POST /api/coach/stream` (SSE), `POST /api/coach/warm` (202 pre-warm), `GET /api/coach/interactions` | Bearer | 6 modes (`surface=questions|learn`), per-user daily caps, `X-Usage-*` headers |
| **Skills** | `GET /api/skills/graph`, `GET /api/skills/me/skills`, `GET /api/skills/boilerplate`, `GET /api/skills/me/recommended-questions` | Bearer | Mastery + roadmap view + Practice Next |
| **Mistakes** | `GET /api/mistakes/graph` | Bearer | Error graph from attempt history |
| **Reviews** | `GET /api/reviews/due`, `POST /api/reviews/{id}/grade` | Bearer | SM-2 queue |
| **Memory** | `GET /api/memory/graph` | Bearer | Forgetting-curve topics (Idea #3) |
| **Analytics** | `GET /api/analytics/signals` | Bearer | Plateau signals (recursion plateau etc., 7d window) |
| **Rescue** | `GET /api/rescue/due`, `POST /api/rescue/{id}/abandon|complete|dismiss` | Bearer | Re-surface queue |
| **Courses** | `GET /api/courses`, `GET /api/courses/{id}`, lessons, progress | Bearer (list also anonymous, cached) | Curriculum + `/api/progress` |
| **Workspace** | `PUT/GET/DELETE /api/workspace/code/{id}`, `GET /api/workspace/last-visited`, `GET /api/workspace/chat/{id}`, `GET /api/workspace/meta/{id}` | Bearer | Redis-persisted drafts, chat, resume |
| **Admin** | `GET /api/admin/*` (stats, users, questions, courses, usage, validation) | Admin | Role-gated `admin`/`super_admin`; writes invalidate course/question caches |
| **Debug** | `GET /debug/*` | — | Dev-only diagnostics (404 in production) |

Error semantics: `HTTPException` → 4xx client, unexpected → 5xx via global handler; rate-limit 429 via in-process limiter + `usage` middleware.

## Testing

### Backend (pytest — `backend/tests/README.md`)

```bash
cd backend
pip install -r requirements.txt -r tests/test_requirements.txt
DATABASE_URL=postgresql://codecoach:codecoach@127.0.0.1:5433/codecoach_test \
  python -m pytest tests/unit/            # 82 files (incl. memory_graph, animation quality, adapter-state)
python -m pytest tests/integration/       # 33 files (needs isolated Postgres schema)
python -m pytest tests/contract/          # 1 file (OpenAPI response contracts)
python -m pytest tests/security/          # 5 files
python -m pytest tests/performance/       # 2 files
python -m pytest tests/migrations/        # 2 files
python -m pytest tests/simulation/        # 2 files (skill-graph)
python -m pytest                          # all tiers; coverage via qa/enforce_coverage_budget.py
ruff check . && ruff format . --check     # lint gate
```

Tests use an isolated `codecoach_test` schema (`DATABASE_SEARCH_PATH`; per-worker `codecoach_test_gwN` under xdist); never touch production. Shared auth builders live in `tests/fixtures/auth_helpers.py`; the 50-question seed bank + 107 live ids (`fixtures/live_question_ids.json`) come from `conftest.py`. Flaky tests are quarantined via `tests/enforce_flaky_quarantine.py`.

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
# needs backend :8000 + frontend :3000 + Motion Canvas viewer :9000
npx playwright test --project=chromium   # 15 specs (51 chromium; viewer specs need :9000)
# config: playwright.config.ts — warmup 180s, expect 10s, url http://localhost:3000,
# webServer backend :8000 + vite :9000 (viewer.html)
```

Quality gates (CI): `ruff` + `ruff format` + `pytest` tiers + `pnpm lint/typecheck/test:run` + `playwright` + `qa/enforce_coverage_budget.py`.

## Development

This is a private, closed project — no external maintainers or MIT-style licensing.

**Standard workflow (AGENTS.md):** `inspect → plan → failing test → implement → verify → production-readiness review`.

1. **Branch** off `main` (`feat/*`, `fix/*`). Keep PRs small and reviewable.
2. **TDD** — red → green → refactor. No source change without a failing test. Bugs get a regression test first.
3. **Graphify-first exploration** — `graphify query "<question>"` / `path` / `explain` before grep/read when `graphify-out/graph.json` exists; run `graphify update .` after code changes.
4. **Production-first** — preserve API contracts, validate at boundaries, no secrets in logs, degrade gracefully, add observability for behavioral changes.
5. **Supabase-only DB** — no SQLite/MySQL/local Postgres for runtime; only `postgresql://` / `postgresql+asyncpg://` against Supabase (or the isolated `codecoach_test` schema for tests).
6. **Layering** — `api → services → ports → sql_*` repositories; DI via `app/api/dependencies.py`; Pydantic at boundaries; async engine (`async_session_maker`).
7. **Quality gates** before commit: `ruff check + format --check`, `pnpm lint`, `pnpm typecheck`, relevant `pytest`/`vitest`/`playwright` tiers, and coverage budget.
8. **Caveman-review** before every commit: capture `git diff --staged`, load the `caveman-review` skill, fix all `bug:`/`risk:`/`nit:` findings, re-stage, re-verify, then commit.

See [AGENTS.md](./AGENTS.md) for the full mandatory rules and [Progress.md](./Progress.md) for recent changes.

## Project Structure

```
CodeCoach-AI/
├── backend/
│   ├── app/
 │   │   ├── api/               # coach, run, submit, submissions, questions, skills, mistakes,
 │   │   │                      # reviews, memory, rescue, courses, progress, workspace, admin, auth, health, debug
 │   │   ├── adapters/          # code_wrappers, coaching_prompts, coaching_adapter, execution_adapter,
 │   │   │                      # submit_grading_service, response parser, formatter
 │   │   ├── use_cases/         # question validation (structure, test_cases, starter_code, solution, time, signature, output_format, animation gate)
 │   │   ├── services/          # groq, piston, skill_graph, sm2, memory_graph, error_graph,
 │   │   │                      # rescue, review, animations + scene_planner, usage, submissions, course (cached),
 │   │   │                      # question_bank, workspace, learner_context, adapter_state_recovery …
 │   │   ├── repositories/      # sql_* (Supabase/PostgreSQL only)
 │   │   ├── ports/             # Abstract interfaces (ABCs)
 │   │   ├── models/            # Pydantic schemas + domain enums (Question, ReviewCard, TopicMemory, RescueItem …)
 │   │   ├── core/              # database (async engine), config (get_settings), security (JWT/bcrypt)
 │   │   ├── middleware/        # rate_limit (in-process limiter), security_headers (CSP)
 │   │   └── dependencies/      # FastAPI Depends() wiring (app/api/dependencies.py)
 │   ├── alembic/               # migrations (initial, admin, usage, skill-graph, submissions,
 │   │                            # review_cards, rescue_queue, taxonomy prune, adapter-state — head b4c5d6e7f8a1)
 │   ├── scripts/               # sync_local_to_db, seed_admin, seed_skill_graph, backfill_skill_graph,
 │   │                            # seed_e2e, verify_course_exercises, animate_coverage
│   ├── tests/                 # unit, integration, contract, security, performance, simulation, migrations
│   └── docs/                  # CURRICULUM_DEPLOYMENT.md
├── frontend/
│   └── src/
│       ├── app/               # /, /problems, /problems/[id], /learn, /dashboard, /admin, /login, /privacy …
│       ├── features/          # auth, coaching, code-execution, question, curriculum, skill-graph,
│       │                      # rescue, review, memory, animation, usage → {hook, service, types, *.test.*}
│       ├── components/        # editor (Monaco), chat, sidebar, header, layout, rescue, visualization, admin, ui/*
│       ├── lib/               # http-client (FetchClient), fetch-client, shuffle, utils
│       ├── hooks/             # useLocalStorage, useDebounce, useWorkspaceMode …
│       ├── providers/         # Theme, Auth, Toast, Usage
│       └── e2e/               # Playwright specs (auth, settings, curriculum, code-execution, animate, viewer)
├── motion-canvas-lab/         # Motion Canvas project (viewer.html, scenes, viewer-player) — Vite on :9000 for E2E
├── graphify-out/              # Code knowledge graph artifacts (graph.json, GRAPH_REPORT.md, wiki/)
├── docker-compose.yml         # backend, frontend, redis, piston (Supabase external)
├── docker-compose.dev.yml     # dev override
└── Makefile                   # test, lint, graphify shortcuts
```

## Deployment

- **Docker Compose (production):** `docker compose up -d --build` builds `pip install` / `npm run build` into images. No volume mounts; `PistonService` + `Redis` + `Supabase` wired via env.
- **Cloudflare Workers (frontend):** OpenNext build — `NEXT_PUBLIC_*` must be set as build args, not runtime env.
- **Supabase migrations:** `alembic upgrade head` against the pooler (handles `pgbouncer=true` stripping, `%`-escaping, `asyncpg` statement-cache off). Verified Sep 04: `b4c5d6e7f8a1` on TEST.
- **Health:** `GET /health` checks `questions_db`, `piston`, `redis`; Docker `HEALTHCHECK` gates `backend`.

## Security

- Input validated at API boundaries (Pydantic); auth via JWT + bcrypt + Supabase OAuth; role-gated admin routes.
- Rate limiting via in-process limiter (`middleware/rate_limit.py`, coach/run/submit/rescue per-user) + `UsageService` token caps; 429 → `Retry-After` + `X-Usage-*`.
- Security headers: `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`, and CSP (`default-src 'self'` + `frame-src` viewer allowlist, `worker-src blob:` for Monaco).
- Secrets only from `.env` / env — never committed or logged; least privilege on all auth/authz paths.
- See `backend/tests/security/` for 5 committed security suites (auth, execution, input validation, etc.).

## Roadmap — audited Sep 04, 2026 (branch `docs/no-issue-docs-sync`)

```
Phase 1 ─── DSA Practice (current focus)
├── 107 live questions (107/107 skill-mapped, F3; 26 skills = 21 roadmap + 5 supporting)
├── Practice Next / skill-graph recommendations (shipped; silent refresh on learner-context invalidation; roadmap-only view)
├── Mistake-memory (submissions + error graph + SM-2 + Memory Graph /dashboard + Learning Analytics signals + adapter-state audit) (F6 + Idea #3 + #133 done)
├── Rescue contract — durable queue f2a3b4c5d6e7 + T1→T2→T3 escalation (Idea #4 done Aug 24, ProblemFlowMap static list; flow-map retired to animate)
├── Learner-aware coaching (shipped `f246c4a`): LearnerContextService + cache_keys + prompt injection + skill emission; coach surfaces (`questions`/`learn`) + warm prefetch landed Sep 04
├── Workspace persistence (shipped `#124`): Redis drafts + chat + last-visited (7d); adapter-state durability (shipped `#133`)
└── Next: attempt-journey replay (now unblocked) + reverse interview (#8, CoachingMode.SENIOR)

Phase 2 ─── Programming Language Curriculum
├── Python Fundamentals ─── 5 modules, 36 lessons (shipped)
├── C Programming ─── 5 modules, 35 lessons (F5, shipped)
├── Java Programming ─── 5 modules, 35 lessons (F5, shipped)
└── Context-aware AI coaching per lesson (now learner-aware `feat/125`)

Phase 3 ─── Future Modules
├── DBMS / SQL — no code
├── OOP & Design Patterns — no code (java course has OOP lessons but no dedicated track)
├── Web Development (React, Node) — no code
├── Theory / MCQ question type — Question has no MCQ fields
└── Classroom dashboard (Idea #2) — no class/roster model

Backlog — Ideas #6 (InterviewTheater), #7 (student-code POST /trace + TimelineScrubber), #9 honourable mentions (adversarial twin, takeover, …)
```

Detailed per-idea status (9 ideas + honourable mentions) lives in [Ideas.md](./Ideas.md) — audited Sep 04; #1/#3/#4 done + #5 unblocked + #8 next; flow-map retired.

## Known Gaps — code-audited Sep 04

- No full attempt-journey animated replay yet (`ProblemFlowMap` is static checkpoint list; `submissions` history now persisted and unblocks it, but timeline + highlights missing — Idea #5; former AI flow-map retired).
- No interview-theater session engine / interviewer UI (`CoachingMode` has 6 modes, no `SENIOR`; no `InterviewSessionService`, no `POST /interview` — Idea #6/`#8`; streaming + Monaco foundation only).
- No classroom/professor dashboard or roster model (`orm.py` has no `class`/`roster`/`assignment`; `data/courses` only `c/`+`java/` — Idea #2 segment moat).
- No generic time-travel debugging for student code (`trace_instrumenter.py`/`trace_parser.py` exist for canonical `animate` only; no `POST /trace`, no `TimelineScrubber` — Idea #7).
- `Ideas.md` backlog (adversarial twin, takeover, talk-it-out, voice mentor, …) not yet promoted — #8 is cheapest win to validate persona engine for #6.

## License

Proprietary — closed source. No public distribution, forking, or external contribution. Internal use only for the CodeCoach AI team and its university partners.

## Support

- **Docs:** [Progress.md](./Progress.md) (living status), [Ideas.md](./Ideas.md) (backlog), [backend/docs/CURRICULUM_DEPLOYMENT.md](./backend/docs/CURRICULUM_DEPLOYMENT.md), [Docs/TEST_ENVIRONMENT.md](./Docs/TEST_ENVIRONMENT.md).
- **Issues:** internal tracker only (no public GitHub Issues intake).
- **Contact:** See `.env.example` / `Docs/TEST_ENVIRONMENT.md` for TEST project refs; ask a maintainer for production credentials.
