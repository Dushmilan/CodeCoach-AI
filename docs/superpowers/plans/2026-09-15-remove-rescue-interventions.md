# Remove Rescue Stuck-Learner Interventions ("hard-block" popups) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete the entire Rescue system — the idle-triggered T1/T2/T3 popups that interrupt learners stuck on a question (T1 at 4 min idle, T2 +5 min, T3 +5 min) — from every layer of the application, with a verification subagent proving zero remnants.

**Architecture:** Pure deletion following existing seams: remove the frontend `features/rescue` module + `components/rescue` + call sites, delete the backend rescue router/service/repository/schemas/ORM, drop the `rescue_queue` table by migration (destructive — gated on explicit user confirmation), and finish with a subagent sweep (repo-wide grep + full gates) certifying removal.

**Tech Stack:** Next.js 14 + Vitest + Playwright; FastAPI + async SQLAlchemy + Alembic + pytest.

**Spec:** User request 2026-09-15 ("the feature that stops a question for ten minutes should be removed from the entire application"; clarified as the idle popups). Identified as the Rescue system via `frontend/src/features/rescue/rescue.config.ts` (`t1IdleMs: 4min`, `t2AfterT1Ms: 5min`, `t3AfterT2Ms: 5min`).

## Global Constraints

- Supabase PostgreSQL is the ONLY database; no new stores.
- TDD applies in reverse here: every deletion step starts by deleting/adjusting the corresponding tests, then source, then running the suite green. No orphaned test may reference removed symbols.
- Dropping the `rescue_queue` table destroys data — per production-first rules this needs explicit user confirmation at execution time; code removal lands first, the drop migration is a separate gated task.
- Preserve all other API contracts and behavior (skill graph, reviews queue, coaching, onboarding tour minus rescue copy).
- Backend gates: `ruff check .`, `ruff format . --check`, `python -m pytest tests/unit tests/integration tests/contract tests/migrations`.
- Frontend gates: `pnpm lint`, `pnpm typecheck`, `pnpm test:run`, `pnpm test:e2e` smoke (existing specs that touched rescue surfaces).
- `ANIMATION` validation gate and question pipeline are untouched.

---

## Step 0: Issue + isolated branch/worktree (blocking prerequisite)

Plan A lives on `feat/159-professor-dashboard`; this removal is unrelated, so one-issue-one-branch rules apply. Do NOT start Task 1 on the Plan A worktree.

- [ ] **Step 1: Create the issue** — `gh issue create --title "Remove rescue stuck-learner intervention system" --body "Removes T1/T2/T3 idle popups (frontend features/rescue, components/rescue, backend rescue router/service/repo/schemas, rescue_queue table). See docs/superpowers/plans/2026-09-15-remove-rescue-interventions.md."` Record the issue number `<N>`.
- [ ] **Step 2: Create worktree + branch** —
```bash
git fetch origin
git worktree add ../CodeCoach-AI-<N>-rescue -b fix/<N>-remove-rescue origin/main
cd ../CodeCoach-AI-<N>-rescue
```
- [ ] **Step 3: Verify clean** — `git worktree list && git branch --show-current && git status --porcelain` (expect the new branch, empty status).

## File map (exact deletion/stripping inventory, verified 2026-09-15)

**Delete — frontend (11 files):**
- `frontend/src/features/rescue/rescue.config.ts`
- `frontend/src/features/rescue/rescue.service.ts`
- `frontend/src/features/rescue/rescue.service.test.ts`
- `frontend/src/features/rescue/rescue.types.ts`
- `frontend/src/features/rescue/rescue.storage.ts`
- `frontend/src/features/rescue/rescue.checkpoints.ts`
- `frontend/src/features/rescue/use-rescue-contract.hook.ts`
- `frontend/src/features/rescue/use-rescue-contract.hook.test.ts`
- `frontend/src/features/rescue/RescueDueQueue.tsx`
- `frontend/src/features/rescue/RescueDueQueue.test.tsx`
- `frontend/src/components/rescue/ProblemFlowMap.tsx`
- `frontend/src/components/rescue/ProblemFlowMap.test.tsx`
- `frontend/src/components/rescue/RescueIntervention.tsx`

**Strip — frontend (call sites + copy):**
- `frontend/src/app/problems/[id]/page.tsx` + `page.test.tsx` — remove rescue hook usage/rendering
- `frontend/src/app/problems/page.tsx` + `page.test.tsx` — remove rescue queue usage
- `frontend/src/app/dashboard/page.tsx` + `page.test.tsx` — remove rescue usage
- `frontend/src/components/onboarding/OnboardingTour.tsx` + `OnboardingTour.test.tsx` — remove the "Stuck for 4 minutes? AI nudges you…" copy (keep the rest of the tour)

**Delete — backend (9 files):**
- `backend/app/api/rescue.py`
- `backend/app/services/rescue_service.py`
- `backend/app/ports/rescue_repository.py`
- `backend/app/repositories/sql_rescue_repository.py`
- `backend/app/models/rescue_schemas.py`
- `backend/alembic/versions/f2a3b4c5d6e7_add_rescue_queue.py` (superseded by the drop migration; keep history linear — do NOT delete, see Task 3)
- `backend/tests/unit/test_rescue_service.py`
- `backend/tests/unit/test_sql_rescue_repository.py`
- `backend/tests/integration/test_rescue_endpoints.py`

**Strip — backend:**
- `backend/app/main.py` — unregister rescue router
- `backend/app/api/dependencies.py` — remove `get_rescue_*` providers
- `backend/app/models/orm.py` — remove `RescueQueueORM` (`rescue_queue`, ~lines 369-408)
- `backend/tests/conftest.py` — remove rescue fixtures/seeds
- `backend/tests/migrations/test_alembic_migrations.py` — update head/pin expectations

**Create — backend:**
- `backend/alembic/versions/<rev>_drop_rescue_queue.py` — gated drop (Task 3)

---

### Task 1: Frontend removal

**Files:** all frontend delete/strip entries above.

- [ ] **Step 1: Delete rescue tests first** — `git rm` the 3 frontend rescue test files (`rescue.service.test.ts`, `use-rescue-contract.hook.test.ts`, `RescueDueQueue.test.tsx`, `ProblemFlowMap.test.tsx`). Run `pnpm vitest run src/features/rescue src/components/rescue` — Expected: no test files found (proves nothing else depends on the test modules).
- [ ] **Step 2: Delete rescue source** — `git rm` the 9 remaining rescue source files. Run `pnpm typecheck` — Expected: FAIL with "Cannot find module …/rescue/…" at exactly the 4 call-site files (`problems/[id]/page.tsx`, `problems/page.tsx`, `dashboard/page.tsx`, plus any test imports). This failure list IS the stripping checklist; if another file appears, stop and triage before continuing.
- [ ] **Step 3: Strip call sites** — remove hook calls, rendered `<RescueIntervention/>`/`<ProblemFlowMap/>`/queue components, and rescue imports from the files in the Step 2 failure list; update their tests to drop rescue cases (no weakened non-rescue assertions). Remove the stuck-4-minutes copy line from `OnboardingTour.tsx` and its test expectation.
- [ ] **Step 4: Verify** — `pnpm typecheck && pnpm lint && pnpm test:run`. Expected: PASS, zero `rescue`/`Rescue`/`useRescue`/`tierThresholds`/`RESCUE_` matches in `frontend/src`:
```bash
grep -rni "rescue\|tierThresholds\|RESCUE_" frontend/src frontend/e2e || echo CLEAN
```
Expected output: `CLEAN`.
- [ ] **Step 5: Commit** — `git add -A && git commit -m "fix(<N>): remove rescue stuck-learner interventions from frontend"`.

### Task 2: Backend removal (code only, table stays until Task 3)

**Files:** all backend delete/strip entries above except the Alembic create-version.

- [ ] **Step 1: Delete rescue tests first** — `git rm backend/tests/unit/test_rescue_service.py backend/tests/unit/test_sql_rescue_repository.py backend/tests/integration/test_rescue_endpoints.py`. Run `python -m pytest backend/tests/unit backend/tests/integration -q` — Expected: PASS (nothing else imports them; if collection errors appear, triage before continuing).
- [ ] **Step 2: Delete rescue source** — `git rm backend/app/api/rescue.py backend/app/services/rescue_service.py backend/app/ports/rescue_repository.py backend/app/repositories/sql_rescue_repository.py backend/app/models/rescue_schemas.py`. Strip `main.py` router registration, `dependencies.py` providers, `RescueQueueORM` from `orm.py`, rescue fixtures from `conftest.py`, and update `test_alembic_migrations.py` expectations.
- [ ] **Step 3: Verify** — `ruff check backend && ruff format backend --check && python -m pytest backend/tests/unit backend/tests/integration backend/tests/contract backend/tests/migrations -q`. Expected: PASS. Then:
```bash
grep -rni "rescue" backend/app backend/tests backend/scripts || echo CLEAN
```
Expected output: `CLEAN` (the old `f2a3b4c5d6e7_add_rescue_queue.py` migration will still match — that is expected and allowed; everything else must be gone).
- [ ] **Step 4: Commit** — `git add -A && git commit -m "fix(<N>): remove rescue backend (router, service, repo, schemas, ORM)"`.

### Task 3: Drop `rescue_queue` table (GATED — destructive)

> Do NOT execute without explicit user confirmation in the execution session. Dropping destroys queued rescue rows. Default recommendation: run this task only after Tasks 1–2 are merged and the user confirms no rescue data needs preservation (it is regenerable idle-state, normally safe, but the call is the user's).

- [ ] **Step 1: Confirm** — ask the user: "Drop table `rescue_queue` (all queued rows deleted)?" Proceed only on explicit yes.
- [ ] **Step 2: Write migration** — new revision from current head:
```python
def upgrade() -> None:
    op.drop_table("rescue_queue")
def downgrade() -> None:
    op.create_table("rescue_queue", sa.Column("id", sa.String(36), primary_key=True), ...)
```
(downgrade recreates the minimal shape from `f2a3b4c5d6e7_add_rescue_queue.py` — read that file for exact columns).
- [ ] **Step 3: Verify** — `python -m pytest backend/tests/migrations -q` plus upgrade/downgrade round-trip on the test schema. Expected: PASS, single head.
- [ ] **Step 4: Commit** — `git add backend/alembic backend/tests/migrations && git commit -m "fix(<N>): drop rescue_queue table"`.

### Task 4: Verification subagent sweep (the "spin up an agent" requirement)

**Files:** none (read-only) — output is a verification report posted back to the session.

- [ ] **Step 1: Dispatch a fresh subagent** (`task` tool, `subagent_type: "general"`) with this exact brief:
> "Verify complete removal of the Rescue stuck-learner system in worktree ../CodeCoach-AI-<N>-rescue. (1) Repo-wide grep for `rescue|Rescue|RESCUE|tierThresholds|t1IdleMs|stuckCheckpoint|rescue_abandoned_problems` excluding git history and the superseded migration `f2a3b4c5d6e7_add_rescue_queue.py` — report every hit or ZERO HITS. (2) Run backend gates (`ruff check .`, `ruff format . --check`, `python -m pytest tests/unit tests/integration tests/contract tests/migrations`) and frontend gates (`pnpm lint`, `pnpm typecheck`, `pnpm test:run`) from a clean state; report pass/fail with failing test names. (3) Boot the app (backend :8000, frontend :3000 same-origin) and confirm: solving flow on a problem page with 5+ minutes idle shows NO popup; no `/api/rescue*` route in OpenAPI (`/openapi.json`). Return ONLY: hit list, gate results, idle-probe result, OpenAPI rescue-route check."
- [ ] **Step 2: Review the report** — every gate must pass and hits must be zero (modulo the allowed migration file). Any hit → new fix task; any red gate → systematic-debugging loop.
- [ ] **Step 3: Caveman-review + PR** — run the caveman-review skill on the staged diff per repo rules, then open the PR with `Closes #<N>`.

## Self-review

- Spec coverage: remove idle popups everywhere ✓ (Tasks 1–2 delete/strip every inventoried file; inventory verified by grep 2026-09-15); "ten minutes" perception ✓ (T1 4min + T2 5min chain gone); verification agent ✓ (Task 4 with exact brief); no over-deletion ✓ (reviews queue, skill graph, coaching, simulation learner profiles untouched — none reference rescue symbols; subagent confirms).
- Placeholders: none — every step names files, commands, expected outputs.
- Type consistency: no new types introduced; contract is deletion-only. Migration chain stays linear (old rescue migration retained, drop appended).
