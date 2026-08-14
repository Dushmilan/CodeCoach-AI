# CodeCoach AI

**A private, AI-powered coding practice platform for university students.**

Practice DSA problems and learn programming languages with structured lessons
and real-time AI coaching. This is a closed, proprietary project — the source
is private and not distributed, and there is no public contribution workflow.

---

## Table of Contents

- [What is CodeCoach AI?](#what-is-codecoach-ai)
- [Who is it for?](#who-is-it-for)
- [Features](#features)
- [Roadmap](#roadmap)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Data Model](#data-model)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Development](#development)
- [Known Gaps](#known-gaps)

---

## What is CodeCoach AI?

CodeCoach AI is an AI-assisted coding practice platform for university students.
It combines:

- **DSA practice** — a question bank of 109 problems (33 Easy / 50 Medium /
  26 Hard) seeded in Supabase across ~19 categories (Arrays & Hashing, Two
  Pointers, Sliding Window, Trees & Recursion, Dynamic Programming, Graphs,
  Linked Lists, Binary Search, and more) with Python, JavaScript, and Java
  starter code.
- **Language curriculum** — a Python Fundamentals course (5 modules, 36 lessons)
  mixing theory with interleaved coding exercises in `/learn`. The data model
  supports arbitrary languages (C, Java, and more are planned).
- **AI coaching** — hints, code reviews, explanations, debugging help, and
  code animations powered by Groq (six modes: hint, review, explain, debug,
  freeform, animate).
- **Submit & grade** — code runs against visible and hidden test cases in an
  isolated Piston container with pass/fail results.
- **Skill graph** — learning events are turned into per-skill mastery estimates
  and a "Practice Next" recommendation queue, so the platform learns which
  skills each student needs to work on.

AI coaching runs on the platform's own Groq key with per-user daily token
limits, so students never supply their own API keys or subscriptions.

## Who is it for?

| Audience                       | Need                                                          |
| ------------------------------ | ------------------------------------------------------------- |
| **Struggling CS students**     | Hand-holding through basics, structured learning              |
| **Interview grinders**         | Coached practice across 100+ target problems                  |
| **Non-CS majors**              | Learn programming from scratch                                |
| **Professors**                 | A curriculum-aligned tool they can recommend to their classes |

## Features

Documented features are marked with their actual state so the docs never drift
ahead of the code.

### Built

| Feature                     | Description                                                                                                                          |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **AI Coaching**             | 6 modes (hint, review, explain, debug, freeform, animate) via Groq — structured JSON responses + SSE streaming (`POST /coach`, `POST /coach/stream`) |
| **Code Execution**          | Piston container — Python, JavaScript, Java with smart code wrapping for test-harness generation (`GET/POST /run`, `/run/validate`, `/run/languages`) |
| **Submit & Grade**          | Run code against visible + hidden test cases, pass/fail reporting (`POST /submit`)                                                  |
| **Question Bank**           | DSA questions with CRUD, search, and filtering by difficulty/category (admin + public `/questions`)                                  |
| **Question Validation**     | Validation use cases — structure, test cases, starter code, solution, time limits, function signature, output format (`/question-validation`) |
| **Curriculum**              | Python Fundamentals — 5 modules, 36 lessons (21 theory + 15 exercises); `/learn` dashboard, module tree, lesson viewer, adjacent-lesson navigation |
| **Lesson-aware Coaching**   | AI coaching that injects lesson context into each prompt; theory and exercise lesson layouts                                    |
| **Solution Animations**     | Generate, validate, compile, and play structured step-by-step code animations (animate coaching mode, canonical-solution pipeline, `AnimationPlayer`) |
| **Skill Graph**             | Learning events (runs, submissions, hints, reveals, diagnosis, review) → per-skill mastery + status (new/learning/developing/strong/needs_review), trends, decay, and graphs |
| **Practice Next**           | Deterministic "recommended questions" API respecting skill prerequisites; surfaced as a "Practice Next" queue on the problems page   |
| **Rescue Contract**         | Stuck-student intervention: checkpoints, `RescueIntervention`, problem/solution flow maps, diagnosis with deterministic fallback      |
| **Auth**                    | JWT email/password registration + login (bcrypt, refresh tokens) + Supabase OAuth (Google)                                          |
| **Usage Metering**          | Per-user daily input/output token caps on coach endpoints surfaced via `X-Usage-*` headers; Redis-backed request/rate-limit tracking |
| **Plans & Gates**           | Per-user plan field and premium gating (`PremiumGate`, `UpgradeModal`, usage bar)                                                     |
| **Admin Panel**             | Dashboard, users, questions, curriculum CRUD, question validation, usage analytics, rate-limit analytics, abuse reports               |
| **Workspace UX**            | Monaco editor, dark/light theme, resizable panels, sidebar navigation, onboarding tour, toasts, hydration guard                        |
| **Infrastructure**          | Docker Compose (backend, frontend, redis, piston), Alembic migrations, Supabase as the single database, Cloudflare Workers (OpenNext) build |

### Partial / foundation

| Feature                      | What exists                                                                    | What's missing                                    |
| ---------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------- |
| **Curriculum breadth**       | Python Fundamentals shipped; schema supports C/Java/ML/Prompt-Engineering      | C and Java content not yet committed              |
| **Question bank volume**     | 109 questions seeded (33 Easy / 50 Medium / 26 Hard)                          | Skill-graph mapping covers 21 of 109 questions    |
| **Rescue re-surface loop**   | Intervention + flow maps built                                                | "abandoned problem resurfaces tomorrow" queue     |
| **Attempt-history replay**   | Per-solve flow maps                                                             | Persistent full attempt journeys + animated replay|
| **Interview theater**        | SSE streaming foundation + editor change events                                | Session/event engine + interviewer UI             |

### Planned

| Phase               | Scope                                                                                       |
| ------------------- | ------------------------------------------------------------------------------------------- |
| **Phase 1 — DSA**   | Question target met (109 in DB: 33 Easy / 50 Medium / 26 Hard); expand skill-graph coverage across all questions, onboarding polish, empty states |
| **Phase 2 — Curriculum** | C and Java curricula (15–20 lessons each), context-aware coaching per lesson           |
| **Phase 3 — Expand**| DBMS/SQL module, OOP/Design Patterns, Web Dev, theory/MCQ question type, classroom dashboard|
| **Backlog**         | See [Ideas.md](./Ideas.md) for the product backlog and roadmap                                |

## Roadmap

```
Phase 1 ─── DSA Practice (current focus)
├── 109 / 100 coding questions ─── 33 Easy / 50 Medium / 26 Hard
├── Practice Next / skill-graph recommendations (shipped)
└── Polish (onboarding, empty states, error handling)

Phase 2 ─── Programming Language Curriculum
├── Python Fundamentals ─── 5 modules, 36 lessons (shipped)
├── C curriculum ─── 15-20 lessons (planned)
├── Java curriculum ─── 15-20 lessons (planned)
└── Context-aware AI coaching per lesson

Phase 3 ─── Future Modules
├── DBMS / SQL
├── OOP & Design Patterns
├── Web Development (React, Node)
├── Theory / MCQ question type
└── Classroom dashboard
```

## Tech Stack

| Layer              | Technology                                                                 |
| ------------------ | -------------------------------------------------------------------------- |
| **Backend**        | Python 3.11+, FastAPI, Pydantic v2, Uvicorn                                |
| **Frontend**       | Next.js 14 (App Router), React 18, TypeScript                              |
| **Editor**         | Monaco Editor (`@monaco-editor/react`)                                     |
| **Styling**        | Tailwind CSS 3, `tailwind-merge`, `clsx`                                   |
| **Code Execution** | Piston (self-hosted Docker container)                                      |
| **AI Coach**       | Groq (LLaMA 3.3 70B versatile / LLaMA 3.1 8B instant) via `api.groq.com/openai/v1`, with animation-specific model override |
| **Database**       | Supabase PostgreSQL (async SQLAlchemy) — the **only** database             |
| **Cache / Limits** | Redis (7-alpine) for request/rate-limit usage tracking                     |
| **Auth**           | JWT (python-jose), bcrypt, Supabase OAuth (Google)                         |
| **Migrations**     | Alembic (`backend/alembic/`)                                               |
| **Testing**        | pytest (backend), Vitest + Testing Library + MSW (frontend), Playwright (E2E) |
| **Deploy**         | Docker Compose + Cloudflare Workers (OpenNext) build                       |

## Architecture

**Backend — Clean Architecture / Hexagonal (Ports/Adapters).**

```
backend/app/
  ports/            Abstract interfaces (ABCs) — repositories, code executor, coaching provider
  adapters/         Concrete implementations (code_wrappers, coaching_prompts, response parser, formatter)
  use_cases/        Single-responsibility validation logic (question validation)
  services/         Business logic wrapping ports (Groq, Piston, skill graph, animations, usage)
  repositories/     SQLAlchemy repositories (sql_*) — Supabase/PostgreSQL only
  api/              Thin FastAPI route handlers
  models/           Pydantic schemas (request/response + domain enums)
  core/             Database engine/session, settings, security
  middleware/       Rate limiting
  dependencies/     FastAPI Depends() injection wiring (app/api/dependencies.py)
```

**Frontend — feature-based.**

```
frontend/src/
  features/     {auth, coaching, code-execution, curriculum, question, skill-graph,
                 rescue, animation, usage}/  {hook, service, types, context}
  components/   Reusable UI (editor, chat, sidebar, header, layout, rescue, visualization, admin…)
  lib/          HTTP client port/adapter (FetchClient)
  hooks/        Shared hooks (useLocalStorage, useDebounce, …)
  providers/    Theme, Auth, Toast, Usage providers
```

**Key architectural decisions**

- **Supabase/PostgreSQL is the single source of truth** — questions, courses,
  modules, lessons, users, progress, usage, and skill-graph state all live in
  PostgreSQL; the application never reads content from the filesystem at
  runtime. See [backend/docs/CURRICULUM_DEPLOYMENT.md](./backend/docs/CURRICULUM_DEPLOYMENT.md).
- **Platform-owned Groq key** — AI coaching runs on a server-side key; clients
  never supply their own. Per-user input/output tokens are metered with daily
  caps enforced on the coach endpoints.
- **Deterministic skill graph** — skill mastery is derived from explicit
  learning events via pure, unit-tested rules (`skill_graph_rules.py`), and
  recommendations respect the skill taxonomy's prerequisites.
- **Code wrapping** — every Piston-supported language has a `_wrap_<language>_code`
  adapter that converts bare function definitions into a stdin → call → stdout
  test harness. Without it, bare definitions produce no output.
- **Dependency injection** — FastAPI `Depends()` for services, constructor
  injection for use cases, making the backend fully testable with mocks.

## Data Model

| Table               | Purpose                                                          |
| ------------------- | ---------------------------------------------------------------- |
| `users`             | Accounts (auth, roles, plans, refresh tokens)                    |
| `questions`         | Question bank (difficulty, category, starter code, test cases…)  |
| `courses`           | Course metadata (id, title, language, order)                     |
| `modules`           | Module metadata (course_id, title, order)                        |
| `lessons`           | Lesson content (theory/exercise, order, linked question)         |
| `course_progress`   | Per-user lesson/progress tracking                                |
| `usage_*`           | AI usage events, daily counters, rate-limit/request tracking     |
| `admin_*`, `audit_logs` | Admin auth/session data and audit trail                     |
| `skills`, `question_skills`, `learning_events`, `user_skill_states` | Skill graph: definitions, questions↔skills mapping, per-user skill state and learning events |

> **Live DB note (checked Aug 14, 2026):** the `public` schema holds `users`,
> `questions`, `courses`, `modules`, `lessons`, `course_progress`, `usage_*`,
> admin/audit tables, and the skill-graph tables (`skills`, `question_skills`,
> `learning_events`, `user_skill_states`) after applying
> `5bb567dd8649_add_skill_graph_tables`. Questions, courses, modules, and
> lessons are fully seeded (109 / 14 / 70 / 491 rows). `alembic upgrade head`
> was run against the live DB on Aug 14, 2026.

Migrations live in `backend/alembic/versions/` (initial schema, admin tables,
usage tracking, request tracking, user plan column, skill-graph tables).
Tests use an isolated `codecoach_test` schema.

## Getting Started

### Quick start with Docker

```bash
docker compose up --build
```

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

The stack provisions backend, frontend, Redis, and Piston; PostgreSQL is
external (Supabase project or a local Postgres for development).

### Manual backend setup

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Groq API key and Supabase DATABASE_URL
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Manual frontend setup

```bash
cd frontend
pnpm install
cp .env.example .env.local
pnpm dev
```

### Piston (code execution)

```bash
docker run -d -p 2000:2000 --name piston ghcr.io/engineer-man/piston
```

### Seeding data

Content lives in the database. Initial data can be bootstrapped idempotently
from a local JSON export:

```bash
cd backend
python scripts/sync_local_to_db.py            # uses DATABASE_URL from .env
```

See [backend/docs/CURRICULUM_DEPLOYMENT.md](./backend/docs/CURRICULUM_DEPLOYMENT.md)
for the data model, seed scripts, and test-schema behavior.

## Environment Variables

### Backend (`.env`)

```
GROQ_API_KEY=your_groq_api_key_here
JWT_SECRET_KEY=your_jwt_secret_key
DATABASE_URL=postgresql://postgres.<ref>.<region>.pooler.supabase.com:6543/postgres?pgbouncer=true
# Session-mode pooler (migrations / tooling):
# DIRECT_URL=postgresql://postgres.<ref>.<region>.pooler.supabase.com:5432/postgres
# Optional Groq model overrides (defaults shown)
# GROQ_MODEL_EASY=llama-3.1-8b-instant
# GROQ_MODEL_STREAM=llama-3.1-8b-instant
# GROQ_MODEL_ANIMATE=llama-3.3-70b-versatile
DAILY_TOKEN_INPUT_CAP=250000
DAILY_TOKEN_OUTPUT_CAP=125000
USER_RATE_LIMIT_PER_MINUTE=60
SUPABASE_URL=https://your-project-id.supabase.co      # optional — OAuth (Google)
SUPABASE_ANON_KEY=your_supabase_anon_key_here           # optional — OAuth (Google)
PISTON_API_URL=http://localhost:2000/api/v2/piston      # optional — local Piston
```

### Frontend (`.env.local`)

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co      # optional — OAuth
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here
```

## Project Structure

```
CodeCoach-AI/
├── backend/
│   ├── app/
│   │   ├── api/               # auth, coach, run, submit, questions, question_validation,
│   │   │                      #   courses, progress, skills, daily_limits, admin, health, debug
│   │   ├── adapters/          # code_wrappers/, coaching_prompts/, response parser, formatter
│   │   ├── use_cases/         # Question validation use cases
│   │   ├── services/          # Groq, Piston, skill graph, animations, usage, course, question…
│   │   ├── repositories/      # sql_* repositories (Supabase/PostgreSQL only)
│   │   ├── ports/             # Abstract interfaces (ABCs)
│   │   ├── models/            # Pydantic schemas + domain enums
│   │   ├── core/              # Database engine/session, settings, security
│   │   ├── middleware/        # Rate limiting
│   │   └── dependencies/      # FastAPI Depends() injection (app/api/dependencies.py)
│   ├── alembic/               # Database migrations (Supabase/PostgreSQL)
│   ├── scripts/               # seed_admin, seed_skill_graph, verify_skill_graph,
│   │                          #   sync_database, sync_local_to_db, animate_coverage
│   ├── tests/                 # unit, integration, contract, security, performance,
│   │                          #   simulation, migrations
│   └── docs/                  # CURRICULUM_DEPLOYMENT.md
├── frontend/
│   └── src/
│       ├── app/               # pages (home, problems, learn, privacy, login/register, admin…)
│       ├── components/        # editor, chat, sidebar, header, layout, rescue, visualization, admin, ui
│       ├── features/          # {auth, coaching, code-execution, curriculum, question,
│       │                      #   skill-graph, rescue, animation, usage} → {hook, service, types}
│       ├── lib/               # HTTP client port/adapter
│       ├── hooks/             # Shared hooks
│       └── providers/         # Theme, Auth, Toast, Usage providers
│   └── e2e/                   # Playwright specs
├── graphify-out/              # Code knowledge graph artifacts
├── docker-compose.yml         # backend, frontend, redis, piston
└── Makefile
```

## Testing

### Backend (pytest)

```bash
cd backend
python -m pytest tests/unit/           # 53 unit test files
python -m pytest tests/integration/    # 23 integration test files
python -m pytest tests/security/       # 7 security test files
python -m pytest tests/performance/    # 4 performance test files
python -m pytest tests/contract/       # 2 OpenAPI contract test files
python -m pytest tests/simulation/     # 8 skill-graph simulation test files
python -m pytest tests/migrations/     # 5 migration test files
python -m pytest                        # All tiers
```

Integration, contract, and migration tests require `DATABASE_URL` pointed at
an isolated Postgres schema (see [backend/tests/README.md](./backend/tests/README.md)).

### Frontend (Vitest)

```bash
cd frontend
pnpm test:run                   # Single run (72 unit/component test files)
pnpm lint                       # ESLint
pnpm typecheck                  # TypeScript check (tsc --noEmit)
```

### E2E (Playwright)

```bash
cd frontend
npx playwright test             # 15 specs; requires a running dev + backend stack
```

## Development

This is a private, closed project. There is no public contribution workflow:
no fork/PR intake, no external maintainers, and no MIT-style licensing.

Internal development process (see [AGENTS.md](./AGENTS.md) for the full rules):

1. Work on a feature branch off `main`.
2. Follow TDD — write a failing test first, then implement, then refactor.
3. Run lint + typecheck + the full test tiers before merging.
4. Rebuild the affected Docker image (`docker compose up -d --build <service>`)
   after any backend/frontend source change.
5. Keep the code knowledge graph current (`graphify update .`) and reference it
   with `graphify query` during exploration.
6. Preserve the API contracts and error semantics; breaking changes need
   migration and rollout planning.

## Known Gaps

- Skill-graph mapping covers 21 of the 109 live questions; the rest have no
  taxonomy mapping for recommendations.
- C and Java curricula are supported by the schema but not yet committed.
- No persistent attempt-history/replay or abandoned-problem re-surface queue yet
  (see [Ideas.md](./Ideas.md)).
- Students have no `/dashboard` memory-first route yet.