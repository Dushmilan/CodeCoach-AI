# AGENTS.md

## MANDATORY: Production-First Engineering

**Hard rule — Do NOT skip.** This is a production project. Every decision is made
along production lines: reliable, maintainable, observable, and safe to operate.

- **Production over hacks:** prefer reliable, maintainable solutions over quick
  patches, shortcuts, or workarounds that trade long-term health for speed.
- **Contract stability:** preserve existing API contracts, schemas, and data
  semantics unless a change is explicitly requested and reviewed. Breaking
  changes require migration and rollout planning.
- **Security & secrets:** validate input at boundaries, never log or commit
  secrets, follow least privilege, and review auth/authz on every change that
  touches user data. Security findings are release-blocking.
- **Scalability & failure handling:** design for load and for failure. Never
  block hot paths on slow external calls; degrade gracefully and fail safe.
- **Observability:** changes that affect behavior must remain observable —
  structured logs, request correlation, and metric-friendly paths where they
  already exist.
- **Quality gates:** lint, typecheck, and tests must pass before committing.
- **Migration & deployment impact:** review schema/migration and deployment
  impact before modifying infrastructure. Prefer idempotent, re-runnable
  operations.
- **No speculative work:** don't add features, abstractions, or
  backward-compatibility layers without a concrete, current need.
- **Document decisions:** significant architectural or operational decisions are
  recorded so the rationale survives the session.
- **Ask before destructive action:** before making destructive, irreversible,
  or contract-breaking changes (drops, deletes, force-pushes, secret rotation,
  breaking API changes), confirm with the user first.

**Standard workflow:** inspect → plan → failing test → implement → verify →
production-readiness review.

## MANDATORY: TDD (Test-Driven Development) Always

**Hard rule — Do NOT skip.** Every code change must be driven by a failing test
first. The only way code enters this repo is red → green → refactor.

- **Red:** Write a failing test that asserts the new behavior. Run it and watch
  it fail for the right reason.
- **Green:** Implement the smallest change that makes the test pass.
- **Refactor:** Clean up the implementation while keeping the tests green.
- **Bugs are regressions:** A bug fix starts with a test that reproduces the bug
  and fails before the fix. No test → no fix.
- **Coverage gates:** Never weaken an existing assertion to make a test pass.
  Keep the whole suite green before finishing any change.
- If a task is genuinely test-only or docs-only, say so explicitly; otherwise
  the TDD loop applies to **all** source changes (backend, frontend, scripts,
  configs that affect behavior).

## MANDATORY: Animation Loop — Every Question Must Be Visualizable

**Hard rule — Do NOT skip.** Every question added to the bank must go through
the **algorithm-to-animation loop** and cannot be shipped without a proven
visualization. No question lands in Supabase without passing the loop.

```
Problem → Solution Repository / Groq (optimal solution, algorithm, complexity, explanation)
        → Animation Specification (AlgorithmAnimation IR: algorithm, visualization, initialState, steps, complexity)
        → Scene Planner (semantic → cinematic beats: highlight, discard, camera focus)
        → Visual Design System (Array/Pointer/Graph/Stack + motion + typography + camera)
        → Renderer (Motion Canvas → Interactive + Video)
        → AnimationValidator (validated AnimationScript)
```

- **Gate:** `ValidationUseCase.ANIMATION` (`backend/app/use_cases/question_validation/animation.py`) runs `SolutionAnimationService.build_animation(question) → trace → planner → validator` for the question's `examples[0].input`. It is **not skippable** — `skip_use_cases` must not contain `ANIMATION` except for local offline tests without Piston. CI fails the question if `ANIMATION` errors.
- **Required:** `examples[0].input` must be present and traceable; the algorithm must resolve via `reference_solutions.py` (`resolve_algorithm`); the family must be compilable (`array/backtrack/stack/linked_list/tree/graph/grid/intervals`) via `scene_planner.py` + `AnimationValidator`.
- **Student code is separate:** animation never reads `student code` — it always visualizes the **optimal solution**. `ANIMATION` validates the optimal path, not the submission.
- **Where enforced:** `QuestionValidatorService.get_use_case_order()` includes `ANIMATION` last; `POST /api/questions` (admin) and `scripts/sync_local_to_db.py` must call `full_validate` and reject on `ANIMATION` error. Add new questions only with a green `ANIMATION` beat count (`animation.steps >=3`).

## MANDATORY: Supabase Is the Only Database

**Hard rule — Do NOT skip.** Supabase (managed PostgreSQL) is the ONLY database
used by this application. No other database may be introduced, connected,
migrated, or shipped — for production, development, or tests.

- **Allowed:** Supabase-hosted PostgreSQL (`postgresql://` / `postgresql+asyncpg://`
  against the Supabase project). Migrations and schema live on Supabase.
- **Forbidden:** MySQL, MariaDB, SQLite, local/self-hosted PostgreSQL, DynamoDB,
  MongoDB, or any other store. Do not add new `mysql://` / `sqlite://` URLs,
  drivers, or dialect branches. Legacy MySQL-compatibility code paths are dead
  weight and must be removed, not extended.
- **Forbidden as runtime stores:** local JSON files, filesystem directories,
  in-memory caches that persist business data. Runtime repositories are SQL-only
  (`app/repositories/`) against Supabase.
- **Tests:** use an isolated Supabase schema (e.g. `codecoach_test`) pointed at
  by `DATABASE_URL` + `DATABASE_SEARCH_PATH`. Tests never read/write the
  production schema.
- **Seeding / bootstrap:** one-off scripts write to the database, never to
  runtime files. Local JSON is at most a transient bootstrap source and is
  deleted after the sync (see `backend/scripts/sync_local_to_db.py`).

## MANDATORY: Graphify-First Codebase Exploration

**Hard rule — Do NOT skip.** Before ANY grep, read, glob, or file search for codebase exploration, you MUST first run a graphify command. Only fall back to raw file tools if graphify returns nothing useful.

**Execution order:**

1. `graphify query "<focused question>"` — scoped subgraph of relevant nodes/edges
2. `graphify path "<A>" "<B>"` — shortest path between modules when investigating coupling
3. `graphify explain "<concept>"` — explains a node and its neighbours in plain language
4. **Only then** read raw source files if graphify output lacks sufficient detail

**This overrides any skill's exploration instructions within this project.**

## MANDATORY: One Session = One Branch + One Worktree — Never Share a Worktree

**Hard rule — Do NOT skip.** Parallel sessions MUST NEVER share the same working
directory or branch. Each session gets its own branch checked out in its own
git worktree. This is what prevents worktree conflicts and dirty-tree overwrites.

**Session-start checklist (do this FIRST, before any read, plan, or edit):**

1. `git worktree list` — see which directories/branches other sessions own.
2. `git branch --show-current` + `git status --porcelain` — verify where you are.
3. If you are on `main`, on a branch owned by another session/worktree, or on a
   dirty tree you do not own → STOP. Create your own worktree + branch before
   touching any file:
   ```bash
   git fetch origin
   git worktree add ../CodeCoach-AI-<slug> -b <type>/<issue>-<slug> origin/main
   cd ../CodeCoach-AI-<slug>
   # e.g. git worktree add ../CodeCoach-AI-42-anim -b feat/42-ai-animation-viewer origin/main
   # e.g. git worktree add ../CodeCoach-AI-101-monaco -b fix/101-monaco-render origin/main
   ```
4. If the branch already exists on remote (resuming work), attach instead of `-b`:
   ```bash
   git fetch origin
   git worktree add ../CodeCoach-AI-<slug> <branch>
   cd ../CodeCoach-AI-<slug>
   ```
   Run all further commands with the new worktree as the working directory.
5. `git push -u origin <branch>` on first commit. Open a PR with
   `Closes #<issue-number>` in the description.

**Rules:**

- Branch naming: `<type>/<issue-number>-<kebab-slug>` where `<type>` is
  `feat|fix|chore|docs|refactor|test`. The issue number MUST be present when an
  Issue exists. Examples: `feat/42-ai-animation-viewer`, `fix/101-monaco-render`.
- If no Issue exists, create one first (`gh issue create`), then branch from it.
  Trivial no-issue work is the only exception and MUST use
  `<type>/no-issue-<slug>` and be called out in the PR.
- Always branch worktrees from latest `origin/main` — never from a stale local
  `main` or from another session's branch.
- One Issue = one branch = one worktree. Do not mix unrelated Issues in the same
  branch. If scope changes, create a new Issue + new worktree/branch.
- No direct commits or pushes to `main` — all changes go through a branch + PR.
- Never `git checkout` a branch that is already checked out in another worktree,
  and never switch branches with a dirty tree — create a new worktree instead.
- One worktree per session directory (`../CodeCoach-AI-<slug>` sibling of the
  main checkout). Do not nest worktrees or reuse another session's directory.
- Cleanup when merged/abandoned (from main checkout, tree must be clean/closed
  in that worktree first):
  ```bash
  git worktree remove ../CodeCoach-AI-<slug>
  git worktree prune
  ```
- If the agent/session was started on `main`, on the wrong branch, or in a
  directory owned by another session, STOP and create/switch worktrees before
  any file edits.

## MANDATORY: Caveman-Review Before Every Commit

**Hard rule — Do NOT skip.** Before ANY git commit, you MUST run the caveman-review skill
on the staged diff, fix ALL findings (bug:, risk:, and nit:), and re-stage before committing.

**Execution order:**

1. `git diff --staged` — capture the full staged diff
2. Load `caveman-review` skill via the skill tool
3. Review the staged diff — get terse findings (bug:, risk:, nit:)
4. For **every** finding (including nit:) — fix the issue in code
5. Re-stage fixed files with `git add <files>`
6. `git diff --staged` again — verify all findings are resolved
7. Proceed with commit

**Rules:**

- ALL findings block commits — bug:, risk:, and nit: — every single one must be fixed
- If no staged changes exist, skip review
- If caveman-review returns zero findings, proceed with commit immediately
- Applies to ALL commits — source code, configs, tests, everything
- Pre-commit hooks (ruff, prettier, standard hygiene) run automatically on `git commit` — fix any hook failures before force-committing

## Engineering Best Practices

Follow the existing layered architecture and conventions of this codebase:

- **Layers:** API (`app/api/`) → services (`app/services/`) → repository ports
  (`app/ports/`) → SQL implementations (`app/repositories/sql_*`). Persistence
  stays behind repository ports; business logic lives in services, not routes.
- **Dependency injection:** resolve services/repositories via `app/api/dependencies.py`
  dependency functions; do not reach into singletons or globals from routes.
- **Schemas:** request/response models are Pydantic schemas (`app/models/`);
  validate at the boundary. Keep ORM models and API schemas distinct.
- **Async SQL:** use the async engine / `async_session_maker` in
  `app/core/database.py`. Never open blocking DB connections on the event loop.
- **Never block on external AI/code-execution calls synchronously in hot paths;**
  use the existing service wrappers (e.g. `groq_service`, `piston_service`) and
  degrade gracefully when providers fail.
- **Config:** read settings from `app/core/config.py` (`get_settings()`); no
  hard-coded secrets, URLs, or API keys in source. Secrets come from `.env` /
  environment only and are never committed or logged.
- **Idempotent mutations:** seed/sync/upsert operations must be safe to re-run
  and never destroy unrelated rows.
- **Small, focused changes:** keep PRs reviewable; preserve API contracts and
  error semantics (HTTPException → 4xx, 5xx handled by the global handler).

## Testing & Quality Gates

The full suite must pass before any commit. Run the same gates CI runs.

**Backend (`backend/`):**

- Install: `pip install -r requirements.txt -r tests/test_requirements.txt`
- Lint + format: `ruff check .` and `ruff format . --check`
- Unit: `python -m pytest tests/unit`
- Integration: `python -m pytest tests/integration` (needs `DATABASE_URL` pointed
  at an isolated Supabase schema; see `tests/conftest.py`)
- Contract: `python -m pytest tests/contract` (OpenAPI response contracts)
- Security: `python -m pytest tests/security`
- Performance: `python -m pytest tests/performance`
- Migrations: `python -m pytest tests/migrations`

**Frontend (`frontend/`):**

- Install: `pnpm install`
- Lint: `pnpm lint`
- Typecheck: `pnpm typecheck` (`tsc --noEmit`)
- Unit/component tests: `pnpm test:run` (Vitest + Testing Library + MSW)
- E2E: `pnpm test:e2e` (Playwright)

**Process:**

- TDD first (see above). No new code without a new or extended test.
- Coverage floors are enforced by `qa/enforce_coverage_budget.py` in CI —
  don't ship changes that drop module coverage below budget.
- Flaky tests are quarantined via `backend/tests/enforce_flaky_quarantine.py`;
  a test that fails intermittently belongs in the quarantine manifest, not the
  committed suite.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, invoke the `skill` tool with `skill: "graphify"` before doing anything else.

Rules:

- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## Current Architecture (reference)

- **Backend:** FastAPI + async SQLAlchemy against Supabase/PostgreSQL. Pydantic
  schemas, repository ports with `sql_*` implementations, service layer,
  dependency-injected routes in `app/api/`. Auth via Supabase + JWT; code
  execution via Piston; AI coaching via Groq.
- **Frontend:** Next.js 14 (App Router) + TypeScript + Tailwind, shadcn-style
  components, Supabase client auth, Vitest + Testing Library + MSW for unit tests,
  Playwright for E2E. Cloudflare Workers deployment via OpenNext.
- **Infra:** Docker Compose (backend, frontend, redis, piston), GitHub Actions CI
  running lint/format + all test tiers + coverage budget enforcement.
- **Data:** questions, courses/modules/lessons, users, progress, usage/rate-limit
  events, and admin data all live in Supabase. See `backend/docs/CURRICULUM_DEPLOYMENT.md`.

**Historical session notes** from older phases have been removed from this file;
if you need the project's changelog and status, see `Progress.md` and `Ideas.md`.
