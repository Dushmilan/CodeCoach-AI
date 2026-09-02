# Progress — CodeCoach AI

> Last updated: September 02, 2026 (branch `feat/125-coach-skill-context-cache`) — audited against code.

This is the project's living status document. It is kept in sync with the code:
if a section lists a feature as **Built**, that capability exists in the current
codebase. Feature-by-feature status with checkboxes lives in [Ideas.md](./Ideas.md).

## Phase Status

| Phase                           | Status              | Notes                                                                                                                     |
| ------------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Phase 1 — DSA Practice          | **Mostly complete** | 109/100 questions in DB (33 Easy / 50 Medium / 26 Hard); skill-graph "Practice Next" shipped (109/109 mapped, F3); `submissions`/`review_cards`/`rescue_queue` at head; learner-context cache landed |
| Phase 2 — Programming Languages | **Partial**         | Python Fundamentals + C Programming + Java Programming shipped (5 modules each); DBMS/OOP/WebDev/MCQ still Phase 3        |
| Phase 3 — Future Modules        | **Planned**         | DBMS, OOP, Web Dev, MCQ, Classroom                                                                                        |

## Feature Inventory

### Built

| Feature               | Status | Notes                                                                                                                                              |
| --------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| AI Coaching           | ✅     | 6 modes (hint, review, explain, debug, freeform, animate), SSE streaming, structured JSON; lesson-aware + learner-aware (skill + recent-attempt blocks) |
| Code Execution        | ✅     | Piston; Python / JavaScript / Java wrappers; run + validate endpoints                                                                              |
| Submit & Grade        | ✅     | Visible + hidden test cases, pass/fail; `submit` emits idempotent `LearningEvent sub:{id}` to skill graph, `run` captures `question_id` crashes |
| Question Bank         | ✅     | CRUD, search, filter, `/stats` aggregates; admin management (`/api/questions`, `/api/admin/questions`)                                            |
| Question Validation   | ✅     | 7 validation use cases (structure, tests, starter, solution, time, signature, output format)                                                       |
| Curriculum            | ✅     | Python Fundamentals — 5 modules, 36 lessons (21 theory + 15 exercises); C + Java — 5 modules, 35 lessons each (20 theory + 15 exercises)         |
| Lesson-aware Coaching | ✅     | Lesson context injected into AI prompts (`PromptBuilder._lesson_context_block`)                                                                    |
| Learner-aware Coaching | ✅     | `LearnerContextService` composes cached skill graph (weakest 3) + recent attempts (last 3) into system prompt; `GroqService` v7 hash skips cache when personalized; invalidated on `submit`/`skills` writes (`feat/125`) |
| Solution Animations   | ✅     | Generate → validate → compile → play; canonical-solution `__trace` pipeline (`trace_instrumenter` + `trace_parser` + `SolutionAnimationService`); flow-map retired |
| Skill Graph           | ✅     | Learning events → mastery per skill; statuses new/learning/developing/strong/needs_review; decay + prerequisites; 22 skills, 212 rows (109/109 mapped, F3) |
| Practice Next         | ✅     | Recommended-questions API (`GET /api/skills/me/recommended-questions`) + UI queue on `/problems` via `useRecommendedQuestions` (109/109 mapped, silent refresh on `learner-context-invalidated`)    |
| Rescue Contract       | ✅     | `RescueIntervention` + `ProblemFlowMap` (static checkpoint list via `rescue.checkpoints.ts`, flow-map retired); durable `rescue_queue` (`f2a3b4c5d6e7`) + `/api/rescue/*` ("Back tomorrow"); T1(4m)→T2(+5m AI hint)→T3(+5m re-plan) via `useRescueContract` |
| Auth                  | ✅     | Email/password (JWT + bcrypt), refresh tokens, Supabase OAuth (Google) — "Continue with Google" button on `/login`                                 |
| Usage Metering        | ✅     | Daily input/output token caps, `X-Usage-*` headers, Redis-backed limits                                                                            |
| Plans & Gates         | ✅     | Per-user plan, **quota-gated** coaching (free 20 req/day, paid 500), usage bar, upgrade modal                                                      |
| Attempt History       | ✅     | `submissions` table persists every graded submit + crashed `run?question_id` (attempt_index, error_signature) + `GET /api/submissions/me`          |
| Error Graph           | ✅     | `GET /api/mistakes/graph` — per-user error graph derived from attempt history: signatures grouped with occurrences, affected questions, first/last seen, resolution state; ranked most-recurring first |
| Spaced Repetition     | ✅     | SM-2 review rotation over own past bugs: `review_cards` (`a3b4c5d6e7f8`, unique per user+question+signature), failures open/refresh, passes promote; `/api/reviews/due` + `POST /api/reviews/{id}/grade`; observe hook in `submit`+`run` |
| Memory Graph          | ✅     | Forgetting-curve dashboard (Idea #3): `GET /api/memory/graph` aggregates review cards + submissions by `category` into per-topic energy-cost view (`daysSinceLastTouch`, `dueCount`, `lapses`); `MemoryGraph.tsx` sorted by `energyCostMinutes`; student `/dashboard` route with MemoryGraph + RescueDueQueue + ReviewsDueQueue; Header adds Dashboard link |
| Learning Analytics    | ✅     | Plateau detection `GET /api/analytics/signals` (recursion plateau etc.), 7d window, bounded 1000; banner on `/dashboard`                            |
| Admin Panel           | ✅     | Dashboard, users, questions, curriculum, usage analytics, abuse reports; Header shows **Admin Dashboard** link when `user.role ∈ {admin, super_admin}` (desktop + mobile, gated on `isHydrated`) |
| Workspace UX          | ✅     | Monaco editor (CSP `worker-src blob:` fix `e51ddf4`), themes, resizable panels, onboarding tour, toasts                                               |
| Infrastructure        | ✅     | Docker Compose (backend, frontend, redis, piston), Alembic, Supabase single DB, OpenNext build                                                     |

### Partial / foundation

| Feature                | Status | What exists                                      | What's missing                                |
| ---------------------- | ------ | ------------------------------------------------ | --------------------------------------------- |
| Curriculum breadth     | ✅ C+Java live | **C Programming & Java Programming committed (F5)** | ML/PromptEng/R/JS source JSON parked; DBMS/OOP/WebDev/MCQ not started |
| Question bank volume   | ✅ 109/109 | 109 seeded in DB (33 Easy / 50 Medium / 26 Hard), 109/109 skill-mapped (F3, 212 rows) | — |
| ~~Rescue re-surface loop~~ | ✅ DONE (Aug 24) | Durable queue: `rescue_queue` + `/api/rescue/due` + "Back tomorrow" UI; dismissals permanent; T1→T2→T3 escalation now wired to AI coach | Time-based escalation ✅ DONE |
| Attempt-journey replay | 🟡     | `ProblemFlowMap` checkpoint list (static) + `submissions` history now persisted; animation infra (`trace_parser`) for canonical solutions only | Animated replay timeline over own journey + "where you errored" highlights |
| Interview theater      | 🟡     | SSE streaming (`POST /coach/stream`) + Monaco `onCodeChange` + `CoachingService` | Session/event engine + `InterviewSessionService` + `InterviewTheater` UI (Idea #6) |
| Time-travel debugging  | 🟡     | `trace_instrumenter`/`trace_parser` for canonical-solution animation traces only | Generic AST tracing for user code + `POST /trace` + `TimelineScrubber` (Idea #7) |

### Planned

| Item                       | Status | Notes                      |
| -------------------------- | ------ | -------------------------- |
| ~~C curriculum~~           | ✅ DONE (Aug 23) | 5 modules / 35 lessons     |
| ~~Java curriculum~~        | ✅ DONE (Aug 23) | 5 modules / 35 lessons     |
| DBMS / SQL module          | 🔴     | Phase 3 — no code          |
| OOP & Design Patterns      | 🔴     | Phase 3 — no code (java course covers OOP lessons but not dedicated track) |
| Web Dev (React, Node)      | 🔴     | Phase 3 — no code          |
| Theory / MCQ question type | 🔴     | Phase 3 — `Question` has no MCQ fields, no `POST /trace` |
| Classroom dashboard        | 🔴     | Phase 3 — no `class`/`roster` model, no professor view (Idea #2) |
| Reverse interview (`senior` mode) | 🔴 Next up | `CoachingMode` has 6 modes, no `SENIOR` (Idea #8) |
| Interview theater           | 🔴     | Needs session/event engine (Idea #6) |
| Time-travel debugging       | 🔴     | Needs generic tracing executor (Idea #7) |
| Product backlog (9 ideas)  | 🔴     | See [Ideas.md](./Ideas.md) honourable mentions |

## Infrastructure

- **Backend:** FastAPI + Pydantic v2, Clean Architecture (ports / adapters / services / sql repositories)
- **Frontend:** Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Monaco Editor
- **Database:** Supabase PostgreSQL (async SQLAlchemy) — the **only** database; Alembic migrations
 - **Cache / Limits:** Redis for request/rate-limit + learner-context (`coach:ctx` 60s, `skills:graph` 60s, `submissions:recent` 30s, `skills:recs` 60s)
 - **Code Execution:** Piston (self-hosted Docker container)
- **AI:** Groq (openai/gpt-oss-120b, openai/gpt-oss-20b; `animate` mode override) with per-user daily token metering; `cache_keys.py` centralized TTLs
- **Auth:** Email/password (bcrypt + JWT) + Supabase OAuth (Google)
- **Rate Limiting:** slowapi per-minute per-user limit (default 60/min), per-mode coach/run/submit limits
- **Migrations:** `backend/alembic/versions/` — initial (`ca0a9c3babd2`), admin (`4476164f80b7`), usage (`7fc9e8c06939`, `a1b2c3d4e5f6`, `c8d0e1f2a3b4`), plan (`a5369fbca804`), skill-graph (`5bb567dd8649`), submissions (`d9e1f2a3b4c5`), review_cards (`a3b4c5d6e7f8`), rescue_queue (`f2a3b4c5d6e7`); head = `e1f2a3b4c5d6` on TEST

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
| Frontend unit/component tests    | 76 files | ✅ Passing |
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

- **Learner-context personalization (Sep 02, branch `feat/125-coach-skill-context-cache`, `f246c4a`):** `LearnerContextService` composes weakest-3 skill blocks + last-3 submission blocks (truncated 500-char code, 120-char sig) cached via `backend/app/core/cache_keys.py` (`coach:ctx` 60s, `skills:graph` 60s, `submissions:recent` 30s); `PromptBuilder.build()` appends `learner_context`/`submission_context`; `GroqService` v7 hash skips cache when personalized; `POST /api/coach/` always-on for authed (degrade open), `POST /api/submit/` emits idempotent `LearningEvent sub:{id}` and invalidates `coach:ctx`/`skills:graph`/`submissions:recent`/`skills:recs:*`; `skills.py` ingests also invalidate; `MainWorkspace.tsx:82` + `useRecommendedQuestions` dispatch/listen `learner-context-invalidated`; `Problem` now full description (title+category+difficulty+desc+examples+constraints) not just title.
- **Monaco CSP fix (Sep 02, `e51ddf4`):** restores editor rendering blocked by CSP `worker-src`/`script-src` + dynamic import; `worker-src blob:` verified, `AnimateLauncher` iframe `frame-src` still allowed.
- **Admin Header link (Aug 24):** `Header.tsx` now shows an **Admin Dashboard** link (`/admin`, `data-testid="header-admin-link"` + mobile `header-admin-link-mobile`) when `useAuth().user.role` is `admin` or `super_admin` (gated on `isHydrated && isAuthenticated`). Desktop island nav (hidden on mobile, icon `LayoutDashboard`) + mobile overlay menu. TDD: 5 new tests in `Header.test.tsx` (admin, super_admin visible; user/unauth/unhydrated hidden) — 11/11 green, full suite 643/643.
- **Run capture + CSP/API-base fix (Aug 24):**
  `POST /api/run/` accepts optional `question_id`; a crashed run inside a
  question workspace now records an attempt (passed=false, first-stderr-line
  signature) and opens/refreshes a mistake-memory card - best-effort, no
  question context means no capture (scratch runs stay out of the graph).
  Frontend wires question context through the interactive-run branch only
  (one click = one execution; multi-tc validate loops rely on graded submit).
  Also fixed a latent stdin/version arg-swap in `useCodeExecution.runCode`
  and the real bug behind locally-red E2E auth specs: next.config's
  `|| 'http://localhost:8000'` resurrected a cross-origin API base that CSP
  `connect-src 'self'` blocks. API base is now empty-by-default (same-origin
  via the /api rewrite), with env override preserved (`??`). Admin/superadmin
  seeded into TEST DB via scripts/seed_admin.py - admin-flow E2E is 5/5 green.
- **Live DB migration `a3b4c5d6e7f8` applied (Aug 24):** Supabase TEST project;
  `alembic current` = head, `review_cards` + its 4 indexes verified on live
  (natural-key unique + `(user_id, state, due_at)` queue index), 0 rows.

- **F6 — Mistake-memory phase 2 (Aug 24):** error-graph derivation
  (`error_graph_rules.py` + `ErrorGraphService`, `GET /api/mistakes/graph`) and an
  SM-2 spaced-repetition scheduler over the user's own past bugs
  (`sm2_rules.py`, `ReviewService`, `review_cards` migration `a3b4c5d6e7f8`,
  `/api/reviews/due|grade`). Observe hook added to `submit.py` (best-effort,
  same contract as submission persistence). Also hardened the coverage-budget
  gate: the Piston-failure `except` branches in starter/testcase validators had
  zero dedicated tests and were only covered when the real Piston endpoint was
  unreachable — now pinned by `TestExecutorFailureHandling` so the gate no
  longer depends on infrastructure state.

- **Live DB migration `f2a3b4c5d6e7` applied (Aug 23):** Supabase TEST project resumed;
  `alembic current` = `f2a3b4c5d6e7` (head), `rescue_queue` + indexes verified on live,
  `/health/` reports `questions_db: ok`.

- **F2 — Durable rescue re-surface queue (Aug 23, branch `feat/rescue-resurface-queue`):**
  new `rescue_queue` table (migration `f2a3b4c5d6e7`, partial unique index enforces one open
  row per user+question), `RescueRepository` port + SQL impl, `RescueService` rules engine
  (tomorrow-09:00 resurfacing in the client's timezone, repeat-abandon pushes a day out,
  dismissals permanent), `/api/rescue/{due,abandon,complete,dismiss}` endpoints, and the
  "Back tomorrow" due queue on `/problems`. 36 new backend tests + 16 new frontend tests.
- **Flow-map retirement:** AI `SolutionFlowMap`/`flow_map_*` (`GET /questions/{id}/flow-map`) removed and replaced by canonical **Animate** pipeline (`SolutionAnimationService` + `trace_instrumenter`/`trace_parser`, `POST /api/coach/animate`). Rescue `ProblemFlowMap` retained as static checkpoint list via `rescue.checkpoints.ts`.

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

- E2E suite (Playwright): fixed Aug 24 — `homepage.spec.ts` retargeted from the
  old workspace layout to the landing page, `Sign in` selectors scoped to
  `getByRole('main')`, `networkidle` waits replaced with explicit
  `expect(...).toBeVisible`, `playwright.config.ts` warmup raised to 180s
  with `expect.timeout: 10000`, `backend/app/api/questions.py` trailing-slash
  307 fixed (`@router.get("")`), and `next.config.js` CSP `frame-src` added for
  the Motion Canvas viewer (`AnimateLauncher` iframe to `:9000`; unblocked both
  `animate-flow` stub and `viewer-render` real-render specs — now 51/51 chromium).
- ~~Skill taxonomy maps 21 of the 109 live questions~~ — **RESOLVED (Aug 23):**
  F3 mapped all 109 (212 `question_skills` rows live, 0 dead ids, 0 unmapped);
  coverage now guarded by `tests/unit/test_skill_taxonomy.py` + snapshot fixture.
- ~~C/Java curricula planned but not yet committed~~ — **RESOLVED (Aug 23, F5):** both committed (`backend/data/courses/{c,java}/` 5/35 each, 30/30 Piston verified).
- ~~Live DB migration pending~~ — **DONE (Aug 15):** live Supabase is at head
  `e1f2a3b4c5d6`; verified `rate_limit_events`, `user_daily_usage.request_count`,
  `submissions`, and `question_skills` all exist on live; `alembic upgrade head`
  is a clean no-op.
- Docs were stale (Aug 14/24) — audited Sep 02 against code (branch `feat/125-coach-skill-context-cache`); flow-map retired to animate, `CoachingMode` 6 modes, `data/courses` only `c`/`java`.
- See [Ideas.md](./Ideas.md) for the product backlog and roadmap
