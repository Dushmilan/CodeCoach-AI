# Professor/Lesson/Student DB Wiring + Hierarchy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the frontend-only instructor demo dataset with real Supabase-backed professor ownership, classrooms, enrollments, and temp student data, and expose the admin → professors → demonstrators → students hierarchy to admin/super_admin.

**Architecture:** New Alembic migration adds `courses.owner_id`, `classrooms`, and `classroom_enrollments` tables; new repository port + SQL implementation behind existing layered conventions; idempotent test-gated seed script assigns existing courses/lessons to professors and creates temp students; `GET /api/admin/hierarchy` serves the full tree; professor/demonstrator frontend reads live instructor endpoints.

**Tech Stack:** FastAPI + async SQLAlchemy (Supabase PostgreSQL only), Alembic, Pydantic v2, Next.js 14 + Vitest + Playwright.

**Spec:** User request 2026-09-15 (DB wiring + hierarchy) building on Issue #159 professor/demonstrator dashboards. "Oracle" was a mistype — no oracle entity exists or is planned.

## Global Constraints

- Supabase PostgreSQL is the ONLY database; no SQLite/MySQL/local Postgres, no runtime JSON stores.
- TDD red → green → refactor for every source change; bug fixes start with a reproducing test.
- `QuestionValidatorService.full_validate` including non-skippable `ANIMATION` (`animation.steps >= 3`) is untouched.
- Backend gates: `ruff check .`, `ruff format . --check`, `python -m pytest tests/unit tests/integration tests/contract`.
- Frontend gates: `pnpm lint`, `pnpm typecheck`, `pnpm test:run`, `pnpm test:e2e` (chromium at minimum).
- Seeds are idempotent upserts, refuse to run without `ALLOW_DEMO_SEED=1`, and only ever target the isolated test schema (`codecoach_test` via `DATABASE_URL` + `DATABASE_SEARCH_PATH`); never the production schema.
- No secrets in code/logs; JWT `role` remains the single source of truth for authorization.
- Preserve API contracts; hierarchy is additive (`GET /api/admin/hierarchy`), no breaking changes.

---

## File map

**Create:**
- `backend/alembic/versions/<rev>_professor_classrooms.py` — migration (owner_id, classrooms, enrollments).
- `backend/app/ports/classroom_repository.py` — `ClassroomRepository` protocol.
- `backend/app/repositories/sql_classroom_repository.py` — SQL implementation.
- `backend/app/services/hierarchy_service.py` — `HierarchyService.admin_tree()`.
- `backend/app/api/hierarchy.py` — `GET /api/admin/hierarchy` (or extend `admin.py`; prefer new router registered in `main.py`).
- `backend/scripts/seed_classroom_demo.py` — professors + assignment + temp students + enrollments + progress.
- `backend/tests/integration/test_classroom_repository.py`
- `backend/tests/integration/test_hierarchy_endpoint.py`
- `backend/tests/unit/test_seed_classroom_demo.py`
- `frontend/e2e/admin-hierarchy.spec.ts` — admin sees professor courses + classroom analytics.

**Modify:**
- `backend/app/models/orm.py` — `CourseORM.owner_id`, `ClassroomORM`, `ClassroomEnrollmentORM`.
- `backend/app/api/dependencies.py` — `get_classroom_repository()`, `get_hierarchy_service()`.
- `backend/app/api/instructor.py` — live classroom scoping (professor: owned; ta: assigned) backed by new repo.
- `backend/app/services/class_analytics_service.py` — accept real `classroom_id` (keep demo-shape output contract).
- `backend/scripts/seed_admin.py` — add `professor.grace` / `grace@university.edu` / `professor123`-style password to `INSTRUCTOR_SEED_USERS`.
- `frontend/src/features/instructor/demo.ts` — live fetch with typed fallback (tests via MSW).
- `frontend/src/app/admin/users/page.tsx` (or `dashboard`) — hierarchy section.
- `docs/INSTRUCTOR_DEMO.md` — live-mode wiring notes.

---

### Task 1: Migration — owner_id, classrooms, classroom_enrollments

**Files:**
- Create: `backend/alembic/versions/<rev>_professor_classrooms.py`
- Test: `backend/tests/migrations/test_alembic_migrations.py` (extend head list if it pins heads)

**Interfaces:**
- Consumes: existing `courses`, `users` tables.
- Produces: `courses.owner_id VARCHAR(36) NULL REFERENCES users(id) ON DELETE SET NULL`; `classrooms(id PK, course_id FK CASCADE, owner_id FK SET NULL, name, invite_code UNIQUE, term, schedule)`; `classroom_enrollments(id PK, classroom_id FK CASCADE, user_id FK CASCADE, role VARCHAR(10), UNIQUE(classroom_id, user_id))`.

- [ ] **Step 1: Write the failing test** — add a migration test asserting upgrade head applies cleanly and the three structures exist:
```python
def test_professor_classrooms_tables_exist(alembic_runner):
    alembic_runner.upgrade("head")
    assert _table_exists("classrooms")
    assert _table_exists("classroom_enrollments")
    assert _column_exists("courses", "owner_id")
```
Run: `DATABASE_URL=<test> python -m pytest backend/tests/migrations -x -q`
Expected: FAIL (tables missing).

- [ ] **Step 2: Write the migration** — single revision from current head with `upgrade()` creating the column + two tables + indexes (`ix_classrooms_owner`, `ix_enrollments_classroom`, `ix_enrollments_user`), and `downgrade()` dropping in reverse order.
- [ ] **Step 3: Run migration test** — same command. Expected: PASS.
- [ ] **Step 4: Run full migration suite** — `python -m pytest backend/tests/migrations -q`. Expected: PASS, single head.
- [ ] **Step 5: Commit** — `git add backend/alembic backend/tests/migrations && git commit -m "feat(159): migrate professor ownership, classrooms, enrollments"`.

### Task 2: ORM models

**Files:**
- Modify: `backend/app/models/orm.py:75-130`
- Test: `backend/tests/integration/test_classroom_repository.py::test_models_persist` (written in Task 3; models land first so the suite imports them)

**Interfaces:**
- Consumes: `UserORM`, `CourseORM`, `ModuleORM`, `LessonORM`.
- Produces: `CourseORM.owner_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)`; `class ClassroomORM(Base)` with `__tablename__ = "classrooms"` and columns above + relationships to `CourseORM`/`UserORM`; `class ClassroomEnrollmentORM(Base)` with `__tablename__ = "classroom_enrollments"`, `role` default `"student"`.

- [ ] **Step 1: Write the failing test** (in the Task 3 file, first test only):
```python
async def test_models_persist(db_session):
    prof = UserORM(id="u-prof", username="p", email="p@e.edu", hashed_password="x", role="professor")
    db_session.add(prof)
    course = CourseORM(id="c-1", title="T", description="D", language="python", order=1, owner_id="u-prof")
    db_session.add(course)
    room = ClassroomORM(id="r-1", course_id="c-1", owner_id="u-prof", name="CS101", invite_code="INV-1", term="Fall 2026", schedule="Mon")
    db_session.add(room)
    await db_session.commit()
    assert (await db_session.get(ClassroomORM, "r-1")).invite_code == "INV-1"
```
Run: `python -m pytest backend/tests/integration/test_classroom_repository.py::test_models_persist -q`
Expected: FAIL (`ClassroomORM` undefined).

- [ ] **Step 2: Implement models** in `orm.py` exactly per Interfaces.
- [ ] **Step 3: Re-run** — Expected: PASS.
- [ ] **Step 4: Commit** — `git add backend/app/models/orm.py backend/tests/integration/test_classroom_repository.py && git commit -m "feat(159): ORM for course ownership, classrooms, enrollments"`.

### Task 3: ClassroomRepository port + SQL implementation

**Files:**
- Create: `backend/app/ports/classroom_repository.py`, `backend/app/repositories/sql_classroom_repository.py`
- Modify: `backend/app/api/dependencies.py` (add `get_classroom_repository`)
- Test: `backend/tests/integration/test_classroom_repository.py` (extend)

**Interfaces:**
- Consumes: `AsyncSession`, ORM models.
- Produces: `class ClassroomRepository(Protocol)` with `async def create_classroom(*, course_id, owner_id, name, invite_code, term, schedule) -> ClassroomORM`; `async def list_owned_by_professor(owner_id) -> list[ClassroomORM]`; `async def list_for_ta(user_id) -> list[ClassroomORM]` (join enrollments where role=`ta`); `async def enroll(classroom_id, user_id, role) -> ClassroomEnrollmentORM` (upsert on `(classroom_id, user_id)`); `async def set_course_owner(course_id, owner_id) -> None`. `class SqlClassroomRepository(ClassroomRepository)` implements all five.

- [ ] **Step 1: Write failing tests** — one per method above (owned list excludes others' rooms; ta list only assigned rooms; enroll upsert changes role without duplicating; set_course_owner persists).
Run: `python -m pytest backend/tests/integration/test_classroom_repository.py -q`
Expected: FAIL (port/repo missing).
- [ ] **Step 2: Implement port + SQL repo + dependency wiring** (follow `sql_course_repository.py` patterns; no blocking calls on the event loop).
- [ ] **Step 3: Re-run** — Expected: PASS.
- [ ] **Step 4: Ruff** — `ruff check backend/app/ports/classroom_repository.py backend/app/repositories/sql_classroom_repository.py && ruff format --check ...`. Expected: clean.
- [ ] **Step 5: Commit** — `git add <files> && git commit -m "feat(159): classroom repository with professor/ta scoping"`.

### Task 4: Seed — professor.grace, course assignment, temp students

**Files:**
- Modify: `backend/scripts/seed_admin.py` (`INSTRUCTOR_SEED_USERS` += professor.grace)
- Create: `backend/scripts/seed_classroom_demo.py`
- Test: `backend/tests/unit/test_seed_classroom_demo.py`

**Interfaces:**
- Consumes: `ClassroomRepository`, `UserORM`, `CourseORM`, `CourseProgressORM`.
- Produces: `async def seed_demo(session, *, allow: bool) -> dict` returning `{"professors": 2, "courses_assigned": N, "students": 8, "enrollments": 10, "progress": 8}`. Rules (approved defaults): course title/slug containing `data-structures` → `professor.grace`, everything else → `professor.ada`; temp students = the 8 demo roster identities (`mia, leo, ava, noah, zoe, eli, ivy, max`) with `@university.example` emails and username prefix unchanged (usernames match `instructor-demo.json`); enroll 5 into `CS101-A-2026` classroom + 3 into `CS201-B-2026`; TA `demonstrator.turing` enrolled as `ta` in both; `course_progress.completed_lessons` mirrors demo counts. Script exits non-zero unless `ALLOW_DEMO_SEED=1` AND `DATABASE_SEARCH_PATH=codecoach_test`.

- [ ] **Step 1: Write failing unit test** — mock session asserting: refuses without `ALLOW_DEMO_SEED=1` (`SystemExit`); with flag, calls upserts and returns the exact report-dict keys.
Run: `python -m pytest backend/tests/unit/test_seed_classroom_demo.py -q`
Expected: FAIL (module missing).
- [ ] **Step 2: Implement script + grace seed entry** (bcrypt like `seed_admin.py`; every write is select-then-insert/update).
- [ ] **Step 3: Re-run unit test** — Expected: PASS.
- [ ] **Step 4: Dry-run against test schema** — `ALLOW_DEMO_SEED=1 DATABASE_URL=<test> DATABASE_SEARCH_PATH=codecoach_test python backend/scripts/seed_classroom_demo.py`, run twice; second run must change nothing (idempotency proof from report diff).
- [ ] **Step 5: Commit** — `git add backend/scripts backend/tests/unit/test_seed_classroom_demo.py && git commit -m "feat(159): seed professors, course assignment, temp classroom data"`.

### Task 5: Live instructor endpoints

**Files:**
- Modify: `backend/app/api/instructor.py`, `backend/app/services/class_analytics_service.py`
- Test: `backend/tests/integration/test_hierarchy_endpoint.py` (classroom scope tests) + `backend/tests/contract/*` (response-shape; add file `test_instructor_contract.py` if absent)

**Interfaces:**
- Consumes: `ClassroomRepository`, `ClassAnalyticsService.class_overview`.
- Produces: `GET /api/instructor/classrooms` → owned rooms for `professor`, assigned rooms for `ta` (403 otherwise via `require_instructor`); `GET /api/instructor/classrooms/{id}` → room + `class_overview` aggregates, 404 unknown, 403 not-owner-or-assigned. `class_overview(classroom_id)` resolves enrollments from `classroom_enrollments` instead of demo constants; output shape unchanged (`ClassAnalyticsResponse`).

- [ ] **Step 1: Write failing integration tests** — professor sees only owned rooms; ta sees only assigned; cross-professor id → 403; unknown id → 404; analytics totals equal seeded progress.
Run: `python -m pytest backend/tests/integration/test_hierarchy_endpoint.py -q`
Expected: FAIL (routes missing).
- [ ] **Step 2: Implement routes + service change** (dependency-inject repo via `dependencies.py`; keep `ClassAnalyticsResponse` contract byte-identical).
- [ ] **Step 3: Re-run + contract suite** — `python -m pytest backend/tests/integration/test_hierarchy_endpoint.py backend/tests/contract -q`. Expected: PASS.
- [ ] **Step 4: Commit** — `git add backend/app/api/instructor.py backend/app/services/class_analytics_service.py backend/tests && git commit -m "feat(159): live instructor classroom endpoints with role scoping"`.

### Task 6: Admin hierarchy (admin → professors → demonstrators → students)

**Files:**
- Create: `backend/app/services/hierarchy_service.py`, `backend/app/api/hierarchy.py`, `backend/tests/integration/test_hierarchy_endpoint.py` (hierarchy cases)
- Modify: `backend/app/main.py` (register router), `frontend/src/app/admin/users/page.tsx` or `dashboard` (hierarchy section), `frontend/e2e/admin-hierarchy.spec.ts` (new)
- Test: integration + component test for the admin section + e2e spec

**Interfaces:**
- Consumes: `ClassroomRepository`, `ClassAnalyticsService`, `require_admin`.
- Produces: `GET /api/admin/hierarchy` (admin/super_admin only) →
```json
{"professors": [{"id": "...", "username": "professor.ada", "courses": [{"id": "...", "title": "...", "lessons": 36}], "classrooms": [{"id": "...", "name": "...", "invite_code": "...", "tas": ["demonstrator.turing"], "students": 5, "avg_completion": 61}]}]}
```
`class HierarchyService`: `async def admin_tree(self) -> dict` assembling exactly that shape. Admin UI section lists each professor → courses (lesson counts) → classrooms (TA names, student counts, avg completion linking to existing analytics).

- [ ] **Step 1: Write failing integration test** — seed via Task 4 helpers, assert tree shape/values for ada (1 course*, 1 classroom, 5 students) and 403 for professor token. (*Course count follows real DB content; assert `>=1` plus exact classroom assertions.)
Run: `python -m pytest backend/tests/integration/test_hierarchy_endpoint.py -q`
Expected: FAIL.
- [ ] **Step 2: Implement service + route + registration.**
- [ ] **Step 3: Admin UI section + component test + e2e spec** (login as `admin`, assert professor rows + classroom analytics visible).
- [ ] **Step 4: Run** — backend integration + `pnpm test:run <admin tests>` + `npx playwright test e2e/admin-hierarchy.spec.ts --project=chromium`. Expected: PASS.
- [ ] **Step 5: Commit** — `git add <files> && git commit -m "feat(159): admin hierarchy over professors, courses, classrooms"`.

### Task 7: Frontend live wiring (professor/demonstrator read live API)

**Files:**
- Modify: `frontend/src/features/instructor/demo.ts` (+ `demo.test.ts`), professor + demonstrator pages if shapes change
- Test: `demo.test.ts` (MSW live-shape tests), existing page tests stay green

**Interfaces:**
- Consumes: `GET /api/instructor/classrooms`, `GET /api/instructor/classrooms/{id}`.
- Produces: `demo.ts` exports keep their signatures; internals fetch live endpoints with the demo JSON as offline fallback only (never a runtime store).

- [ ] **Step 1: Write failing tests** — MSW returns live payloads; assert `getClassrooms()`/`getClassAnalytics()` return them; MSW network error → demo fallback.
Run: `pnpm vitest run src/features/instructor/demo.test.ts`
Expected: FAIL (no fetch path).
- [ ] **Step 2: Implement live fetch + fallback.**
- [ ] **Step 3: Run** — `pnpm vitest run src/features/instructor && pnpm typecheck && pnpm lint`. Expected: PASS/clean.
- [ ] **Step 4: Commit** — `git add frontend/src/features/instructor && git commit -m "feat(159): instructor dashboards read live classroom API"`.

### Task 8: Full verification + docs

**Files:**
- Modify: `docs/INSTRUCTOR_DEMO.md` (live-mode section: migration, seeds, hierarchy endpoint)

- [ ] **Step 1: Backend all tiers** — `ruff check . && ruff format . --check && python -m pytest tests/unit tests/integration tests/contract -q`. Expected: PASS.
- [ ] **Step 2: Frontend all gates** — `pnpm lint && pnpm typecheck && pnpm test:run`. Expected: PASS (87+ files).
- [ ] **Step 3: E2E** — instructor-flow + admin-hierarchy specs on chromium. Expected: PASS.
- [ ] **Step 4: Coverage budget** — run `qa/enforce_coverage_budget.py` per CI; top up tests if the new modules fall short.
- [ ] **Step 5: Docs + graphify** — update `docs/INSTRUCTOR_DEMO.md`, run `graphify update .`.
- [ ] **Step 6: Commit** — `git add docs/INSTRUCTOR_DEMO.md && git commit -m "docs(159): live classroom wiring and hierarchy"`.

## Self-review

- Spec coverage: professor IDs ✓ (Task 4 + seed_admin), lesson import/assignment ✓ (Task 4 rules), temp students ✓ (Task 4), connect components ✓ (Tasks 5, 7), failing-test iteration ✓ (every task red→green), admin access to demonstrator/professor/student data + assigned lessons + classroom analytics ✓ (Task 6), hierarchy admin → professors → demonstrators → students ✓ (Task 6 tree; TA layer represented per-classroom via `tas`). Oracle: N/A (mistype, confirmed).
- Placeholders: none — every step names files, symbols, commands, expected outcomes.
- Type consistency: `ClassAnalyticsResponse` shape frozen (Task 5); hierarchy shape defined once in Task 6 and reused by UI/e2e.
