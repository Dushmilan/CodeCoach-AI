# Progress — CodeCoach AI

> Last updated: August 15, 2026 (branch `fix/production-runtime-config`)

This is the project's living status document. It is kept in sync with the code:
if a section lists a feature as **Built**, that capability exists in the current
codebase. Feature-by-feature status with checkboxes lives in [Ideas.md](./Ideas.md).

## Phase Status

| Phase                           | Status              | Notes                                                                                                                     |
| ------------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Phase 1 — DSA Practice          | **Mostly complete** | 109/100 questions in DB (33 Easy / 50 Medium / 26 Hard); skill-graph "Practice Next" shipped, DB tables pending migration |
| Phase 2 — Programming Languages | **Partial**         | Python Fundamentals shipped; C/Java curricula planned                                                                     |
| Phase 3 — Future Modules        | **Planned**         | DBMS, OOP, Web Dev, MCQ, Classroom                                                                                        |

## Feature Inventory

### Built

| Feature               | Status | Notes                                                                                                                                              |
| --------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| AI Coaching           | ✅     | 6 modes (hint, review, explain, debug, freeform, animate), SSE streaming, structured JSON                                                          |
| Code Execution        | ✅     | Piston; Python / JavaScript / Java wrappers; run + validate endpoints                                                                              |
| Submit & Grade        | ✅     | Visible + hidden test cases, pass/fail                                                                                                             |
| Question Bank         | ✅     | CRUD, search, filter; admin management                                                                                                             |
| Question Validation   | ✅     | 7 validation use cases (structure, tests, starter, solution, time, signature, output format)                                                       |
| Curriculum            | ✅     | Python Fundamentals — 5 modules, 36 lessons (21 theory + 15 exercises)                                                                             |
| Lesson-aware Coaching | ✅     | Lesson context injected into AI prompts                                                                                                            |
| Solution Animations   | ✅     | Generate → validate → compile → play; canonical-solution pipeline                                                                                  |
| Skill Graph           | ✅     | Learning events → mastery per skill; statuses new/learning/developing/strong/needs_review; decay + prerequisites. Tables applied to the live DB    |
| Practice Next         | ✅     | Recommended-questions API + UI queue on `/problems` (21 of 109 questions mapped)                                                                   |
| Rescue Contract       | ✅     | Checkpoints, RescueIntervention, ProblemFlowMap / SolutionFlowMap; durable re-surface queue live (Aug 23): `rescue_queue`, `/api/rescue/*`, "Back tomorrow" on `/problems` |
| Auth                  | ✅     | Email/password (JWT + bcrypt), refresh tokens, Supabase OAuth (Google) — "Continue with Google" button on `/login`                                 |
| Usage Metering        | ✅     | Daily input/output token caps, `X-Usage-*` headers, Redis-backed limits                                                                            |
| Plans & Gates         | ✅     | Per-user plan, **quota-gated** coaching (free 20 req/day, paid 500), usage bar, upgrade modal                                                      |
| Attempt History       | ✅     | `submissions` table persists every graded submit (attempt_index, error_signature) + `GET /api/submissions/me` — foundation for mistake-memory (#1) |
| Admin Panel           | ✅     | Dashboard, users, questions, curriculum, usage analytics, abuse reports                                                                            |
| Workspace UX          | ✅     | Monaco editor, themes, resizable panels, onboarding tour, toasts                                                                                   |
| Infrastructure        | ✅     | Docker Compose (backend, frontend, redis, piston), Alembic, Supabase single DB, OpenNext build                                                     |

### Partial / foundation

| Feature                | Status | What exists                                      | What's missing                                |
| ---------------------- | ------ | ------------------------------------------------ | --------------------------------------------- |
| Curriculum breadth     | ✅ C+Java live | **C Programming & Java Programming committed (F5)** | ML/PromptEng/R/JS courses exist in DB from earlier syncs; source JSON parked |
| Question bank volume   | 🟡     | 109 seeded in DB (33 Easy / 50 Medium / 26 Hard) | ~~Skill-graph covers 21~~ → **109/109 (F3)**  |
| ~~Rescue re-surface loop~~ | ✅ DONE (Aug 23) | Durable queue: `rescue_queue` + `/api/rescue/due` + "Back tomorrow" UI; dismissals permanent | Time-based stuck escalation (X min → scaffold) still open under Ideas #4 |
| Attempt-journey replay | 🟡     | Per-solve flow maps                              | Persistent attempt history + animated replay  |
| Interview theater      | 🟡     | SSE streaming + editor change events             | Session/event engine + interviewer UI         |

### Planned

| Item                       | Status | Notes                      |
| -------------------------- | ------ | -------------------------- |
| ~~C curriculum~~           | ✅ DONE (Aug 23) | 5 modules / 35 lessons     |
| ~~Java curriculum~~        | ✅ DONE (Aug 23) | 5 modules / 35 lessons     |
| DBMS / SQL module          | 🔴     | Phase 3                    |
| OOP & Design Patterns      | 🔴     | Phase 3                    |
| Web Dev (React, Node)      | 🔴     | Phase 3                    |
| Theory / MCQ question type | 🔴     | Phase 3                    |
| Classroom dashboard        | 🔴     | Phase 3                    |
| Product backlog (9 ideas)  | 🔴     | See [Ideas.md](./Ideas.md) |

## Infrastructure

- **Backend:** FastAPI + Pydantic v2, Clean Architecture (ports / adapters / services / sql repositories)
- **Frontend:** Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Monaco Editor
- **Database:** Supabase PostgreSQL (async SQLAlchemy) — the **only** database; Alembic migrations
- **Cache / Limits:** Redis for request/rate-limit usage tracking
- **Code Execution:** Piston (self-hosted Docker container)
- **AI:** Groq (llama-3.3-70b-versatile, llama-3.1-8b-instant; `animate` mode override) with per-user daily token metering
- **Auth:** Email/password (bcrypt + JWT) + Supabase OAuth (Google)
- **Rate Limiting:** slowapi per-minute per-user limit (default 60/min), per-mode coach/run/submit limits
- **Migrations:** `backend/alembic/versions/` — initial schema, admin tables, usage/request tracking, user plan column, skill-graph tables

> **IMP — Environment status:** The currently wired Supabase project
> (`qazpxjpcvsjbmgbzuxxp`) is the **TEST** database and the Google OAuth is
> **TEST OAuth**. A production database is NOT configured yet. See
> [Docs/TEST_ENVIRONMENT.md](./Docs/TEST_ENVIRONMENT.md) for the full test
> wiring (keys, OAuth URLs, verification commands).

## Test Counts (committed test files)

| Suite                            | Count    | Status     |
| -------------------------------- | -------- | ---------- |
| Backend unit tests               | 53 files | ✅ Passing |
| Backend integration tests        | 23 files | ✅ Passing |
| Backend security tests           | 7 files  | ✅ Passing |
| Backend performance tests        | 4 files  | ✅ Passing |
| Backend contract tests (OpenAPI) | 2 files  | ✅ Passing |
| Backend skill-graph simulation   | 8 files  | ✅ Passing |
| Backend migration tests          | 5 files  | ✅ Passing |
| Frontend unit/component tests    | 72 files | ✅ Passing |
| E2E (Playwright)                 | 15 specs | ✅ Passing |

See [backend/tests/README.md](./backend/tests/README.md) for how to run each tier.

- **F3 — Skill-graph full mapping (Aug 23, branch `feat/skill-graph-full-mapping`):**
  taxonomy grown 17→22 skills (+stacks-queues, heaps, backtracking, bit-manipulation,
  greedy); all 109 live questions mapped (was 21); 4 dead test-only mapping ids removed;
  6 pre-existing weight bugs fixed (summed to 0.9). Coverage locked by a live-inventory
  snapshot fixture + unit tests. Seed script now honors DATABASE_SEARCH_PATH; conftest
  question seeding made per-id idempotent (fixes latent order-dependent flake).
  Live reseeded: 212 rows, recommendations verified non-empty.

- **F5 — C & Java curricula shipped (Aug 23, branch `feat/f5-c-java-curricula`):**
  content recovered from the parked `feat/groq-usage-metering` branch and landed as
  committed source-of-truth JSON (`backend/data/courses/{c,java}/`): 2×5 modules,
  2×35 lessons (20 theory + 15 exercises each). Every exercise's reference solution
  authored and verified against local Piston — 30/30 test cases passing
  (`scripts/verify_course_exercises.py`, permanent regression tool). One authored
  starter bug found+fixed via that gate (calculator div-by-zero now prints `Error`
  with an INT_MIN sentinel contract). Synced to live: both courses serve 5 modules /
  35 lessons through `/api/courses`. Frontend language config already supported
  c/java. Content guard unit tests pin lesson counts, types, runnable exercises.

## Recent Changes

- **Live DB migration `f2a3b4c5d6e7` applied (Aug 23):** Supabase TEST project resumed;
  `alembic current` = `f2a3b4c5d6e7` (head), `rescue_queue` + indexes verified on live,
  `/health/` reports `questions_db: ok`.

- **F2 — Durable rescue re-surface queue (Aug 23, branch `feat/rescue-resurface-queue`):**
  new `rescue_queue` table (migration `f2a3b4c5d6e7`, partial unique index enforces one open
  row per user+question), `RescueRepository` port + SQL impl, `RescueService` rules engine
  (tomorrow-09:00 resurfacing in the client's timezone, repeat-abandon pushes a day out,
  dismissals permanent), `/api/rescue/{due,abandon,complete,dismiss}` endpoints, and the
  "Back tomorrow" due queue on `/problems`. 36 new backend tests + 16 new frontend tests.

## Recent Fixes

- Question loading bugs: removed `@lru_cache`, per-item error handling, relaxed Pydantic schemas
- Suite runner bugs: in-place functions, 5-param AI questions, signal 6 crashes, JS `fs` redeclaration
- Auth hardening: DI consistency, JWT/refresh handling, deactivated-user rejection
- `dependency_overrides`: replaced global `clear()` with targeted `pop()` across test suites
- Coach rate-limit config made lazy (resolved at request time, not import time)
- Redis failures degrade silently (socket-level errors caught, warning→debug logging)
- Admin panel: token-format mismatch, Next.js rewrite resolution in Docker, course-tree deserialization
- Code execution: `ExecutionResult` dataclass serialization fix, `run.py` variable-reference fix
- Curriculum: adjacent-lesson 404 handling, 14-course curriculum re-seeded into DB
- Alembic env.py fixed for Supabase pooler URLs (`%` escaping, asyncpg driver, `pgbouncer` param stripped, statement cache off); skill-graph tables applied to the live DB (`5bb567dd8649`)

## Known Issues

- ~~Skill taxonomy maps 21 of the 109 live questions~~ — **RESOLVED (Aug 23):**
  F3 mapped all 109 (212 `question_skills` rows live, 0 dead ids, 0 unmapped);
  coverage now guarded by `tests/unit/test_skill_taxonomy.py` + snapshot fixture.
- C/Java curricula planned but not yet committed
- ~~Live DB migration pending~~ — **DONE (Aug 15):** live Supabase is at head
  `e1f2a3b4c5d6`; verified `rate_limit_events`, `user_daily_usage.request_count`,
  `submissions`, and `question_skills` all exist on live; `alembic upgrade head`
  is a clean no-op.
- `backend/.env` contains credentials that appeared in plain text on this
  machine — **rotate before any real deployment**. Tests now refuse non-local
  database hosts (`tests/db_guard.py`).
- See [Ideas.md](./Ideas.md) for the product backlog and roadmap
