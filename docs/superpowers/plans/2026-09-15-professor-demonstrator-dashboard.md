# Professor + Demonstrator Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship phase-2 professor + demonstrator (TA) dashboards as role-gated routes backed by a committed demo JSON dataset, with backend professor/ta guards and read-only class analytics over existing data.

**Architecture:** Backend extends roles + auth guards and adds a read-only `ClassAnalyticsService` aggregating existing submissions/progress/skill data (no new tables, no new tracking). Frontend adds `/professor/*` + `/demonstrator/*` App Router routes with shared instructor components served by `frontend/src/data/instructor-demo.json` + MSW demo handlers. Docs carry credentials + verification-pipeline wiring.

**Tech Stack:** FastAPI + Pydantic v2, async SQLAlchemy (Supabase-only runtime), Next.js 14 App Router + TypeScript + Tailwind, Vitest + Testing Library + MSW, pytest + ruff.

**Spec:** Issue #159 (Institutional project: professor + TA access, classrooms, class analytics). Phasing: this PR covers phase 2 (professor dashboard aggregates) in demo-JSON mode; phase 1 tables (classrooms/classroom_members/invite codes) and phase 4 TA limits land as follow-ups.

## Global Constraints

- Supabase PostgreSQL is the ONLY runtime database; no `mysql://`/`sqlite://`, no filesystem business-data stores in backend runtime.
- Demo JSON is a transient frontend demo/bootstrap source only (`frontend/src/data/instructor-demo.json` + `docs/INSTRUCTOR_DEMO.md`); backend runtime repositories stay SQL-only.
- Every new question passes the non-skippable ANIMATION validation gate (`animation.steps >= 3`); professor course creation reuses the existing admin curriculum pipeline + `full_validate`.
- TDD red-green-refactor for every source change; full gates green before commit (ruff, pytest unit, vitest, tsc, lint).
- Least-privilege TA matrix enforced in backend guards and frontend nav (professor-only: roster management, course create/edit, deletes).
- No breaking API contracts; new routes only (`/api/instructor/*`, `/professor/*`, `/demonstrator/*`).

---

### Task 1: Backend role guards + TA permission matrix

**Files:**
- Test: `backend/tests/unit/test_instructor_roles.py`
- Modify: `backend/app/api/auth_deps.py`
- Modify: `backend/app/api/admin.py` (role allow-list)

**Interfaces:**
- Consumes: `UserResponse(role: str)` from `app.models.auth_schemas`.
- Produces: `require_professor() -> UserResponse`, `require_instructor() -> UserResponse`, `instructor_can_manage_roster(role: str) -> bool`, `instructor_can_edit_courses(role: str) -> bool`, `INSTRUCTOR_ROLES = ("professor","ta","admin","super_admin")`.

- [ ] **Step 1: Write the failing test**

```python
import pytest
from fastapi import HTTPException
from datetime import datetime, timezone
from app.models.auth_schemas import UserResponse

def _user(role: str) -> UserResponse:
    return UserResponse(id="u1", username="u", email="u@x.ai",
                        created_at=datetime.now(timezone.utc), role=role)

@pytest.mark.asyncio
async def test_require_professor_allows_professor():
    from app.api.auth_deps import require_professor
    assert (await require_professor(_user("professor"))).role == "professor"

@pytest.mark.asyncio
async def test_require_professor_denies_ta_and_student():
    from app.api.auth_deps import require_professor
    for role in ("ta", "user"):
        with pytest.raises(HTTPException) as exc:
            await require_professor(_user(role))
        assert exc.value.status_code == 403

@pytest.mark.asyncio
async def test_require_instructor_allows_professor_and_ta():
    from app.api.auth_deps import require_instructor
    for role in ("professor", "ta"):
        assert (await require_instructor(_user(role))).role == role

def test_ta_permission_matrix():
    from app.api.auth_deps import instructor_can_manage_roster, instructor_can_edit_courses
    assert instructor_can_manage_roster("professor") is True
    assert instructor_can_manage_roster("ta") is False
    assert instructor_can_edit_courses("professor") is True
    assert instructor_can_edit_courses("ta") is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_instructor_roles.py -v`
Expected: FAIL with "No module / cannot import require_professor".

- [ ] **Step 3: Write minimal implementation**

```python
INSTRUCTOR_ROLES = ("professor", "ta", "admin", "super_admin")
async def require_professor(current_user: UserResponse = Depends(get_current_user)):
    if current_user.role not in ("professor", "admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Insufficient permissions: professor role required")
    return current_user
async def require_instructor(current_user: UserResponse = Depends(get_current_user)):
    if current_user.role not in INSTRUCTOR_ROLES:
        raise HTTPException(status_code=403, detail="Insufficient permissions: instructor role required")
    return current_user
def instructor_can_manage_roster(role: str) -> bool:
    return role in ("professor", "admin", "super_admin")
def instructor_can_edit_courses(role: str) -> bool:
    return role in ("professor", "admin", "super_admin")
```

Extend `admin.py` role allow-list in `update_user` to `["user","professor","ta","admin","super_admin"]`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_instructor_roles.py tests/unit/test_auth_dependency.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/unit/test_instructor_roles.py backend/app/api/auth_deps.py backend/app/api/admin.py
git commit -m "feat: add professor/ta instructor guards and permission matrix"
```

### Task 2: Backend read-only class analytics service + `/api/instructor/*` contracts

**Files:**
- Test: `backend/tests/unit/test_class_analytics_service.py`
- Create: `backend/app/services/class_analytics_service.py`
- Modify: `backend/app/models/analytics_schemas.py`
- Create: `backend/app/api/instructor.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/api/dependencies.py`

**Interfaces:**
- Consumes: roster `list[str]` user_ids + `SubmissionRepository.list_by_user`, progress repo, skill-state repo (injected fakes in tests).
- Produces: `ClassAnalyticsService.class_overview(user_ids) -> ClassAnalyticsResponse`, `GET /api/instructor/roster`, `GET /api/instructor/class-analytics`.

- [ ] **Step 1: Write the failing test**

```python
def test_class_overview_aggregates_per_student():
    import asyncio
    from app.services.class_analytics_service import ClassAnalyticsService
    svc = ClassAnalyticsService(submissions=FakeSubs(), progress=FakeProgress())
    resp = asyncio.run(svc.class_overview(["s1","s2"]))
    assert resp.total_students == 2
    assert resp.avg_completion >= 0
    assert len(resp.students) == 2
```

(Fakes return 1 solved / 1 attempted submissions + 50% progress rows.)

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_class_analytics_service.py -v`
Expected: FAIL ("No module named class_analytics_service").

- [ ] **Step 3: Write minimal implementation**

Pydantic `ClassStudentSummary(user_id, username, completed_lessons, total_lessons, completion_pct, solved, attempted, plateau_signals)` + `ClassAnalyticsResponse(total_students, avg_completion, avg_solved, students)`. Service loops roster, calls existing repos read-only, never writes. Router guards with `require_instructor`, returns service output, degrades to empty on exception with log.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_class_analytics_service.py tests/contract -v`
Expected: PASS, no OpenAPI break (new prefix only).

- [ ] **Step 5: Commit**

```bash
git add backend/tests/unit/test_class_analytics_service.py backend/app/services/class_analytics_service.py backend/app/models/analytics_schemas.py backend/app/api/instructor.py backend/app/main.py backend/app/api/dependencies.py
git commit -m "feat: add read-only class analytics service and instructor API"
```

### Task 3: Frontend demo dataset + aggregators (TDD)

**Files:**
- Create: `frontend/src/data/instructor-demo.json`
- Create: `frontend/src/features/instructor/demo.ts`
- Test: `frontend/src/features/instructor/demo.test.ts`
- Modify: `frontend/src/mocks/handlers.ts`

**Interfaces:**
- Consumes: demo JSON (`professors`, `demonstrators`, `courses`, `classrooms`, `enrollments`, `progress`, `skillMastery` using slugs `arrays|strings|hash-maps|two-pointers|stacks-queues|trees|graphs|dp-1d`).
- Produces: `getClassroom(id)`, `getClassroomStudents(id)`, `getClassAnalytics(id)`, `canManageRoster(role)`, `canEditCourses(role)`.

- [ ] **Step 1: Write the failing test**

```ts
import { describe, it, expect } from "vitest";
import { getClassAnalytics, canManageRoster } from "./demo";
describe("instructor demo", () => {
  it("aggregates class analytics", () => {
    const a = getClassAnalytics("class-cs101-a");
    expect(a.totalStudents).toBeGreaterThan(0);
    expect(a.avgCompletion).toBeGreaterThanOrEqual(0);
  });
  it("enforces TA matrix", () => {
    expect(canManageRoster("professor")).toBe(true);
    expect(canManageRoster("ta")).toBe(false);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm vitest run src/features/instructor/demo.test.ts`
Expected: FAIL (module missing).

- [ ] **Step 3: Write minimal implementation**

Demo JSON with 2 professors, 1 demonstrator, 2 courses, 2 classrooms, 8 enrolled students with progress/submissions/skill mastery. Pure TS aggregators + MSW `GET /api/instructor/*` demo handlers.

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm vitest run src/features/instructor/demo.test.ts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/data/instructor-demo.json frontend/src/features/instructor/demo.ts frontend/src/features/instructor/demo.test.ts frontend/src/mocks/handlers.ts
git commit -m "feat: add instructor demo dataset and aggregators"
```

### Task 4: Frontend professor + demonstrator routes + layouts (TDD)

**Files:**
- Create: `frontend/src/app/professor/layout.tsx`, `page.tsx`, `courses/page.tsx`, `classrooms/page.tsx`, `classrooms/[id]/page.tsx`, `analytics/page.tsx`, `students/[id]/page.tsx`
- Create: `frontend/src/app/demonstrator/layout.tsx`, `page.tsx`, `classrooms/page.tsx`, `classrooms/[id]/page.tsx`, `analytics/page.tsx`
- Create: `frontend/src/components/instructor/InstructorSidebar.tsx`, `StatCard.tsx`, `AnalyticsCharts.tsx`, `RosterTable.tsx`
- Test: `frontend/src/app/professor/page.test.tsx`, `frontend/src/app/demonstrator/page.test.tsx`

**Interfaces:**
- Consumes: `useAuth()` role (`professor|ta|admin|super_admin`), demo aggregators, existing `Card`, `Header`, `SkillGraph` patterns.
- Produces: role-gated routes rendering overview stats, course cards, roster tables, analytics (completion distribution, skill mastery bars, plateau signals list).

- [ ] **Step 1: Write failing page tests** (render with mocked `useAuth` professor/ta; assert headings + `data-testid` blocks; assert Access Denied for `user` role).
- [ ] **Step 2: Run to verify fail** (`pnpm vitest run src/app/professor/page.test.tsx` → FAIL missing module).
- [ ] **Step 3: Implement layouts + pages + components** (server-safe `"use client"`, `dynamic="force-dynamic"`, existing Tailwind/card styling, lucide icons, Link routes for every analytics view).
- [ ] **Step 4: Verify pass** (`pnpm vitest run src/app/professor src/app/demonstrator src/features/instructor`).
- [ ] **Step 5: Commit** (`git commit -m "feat: add professor and demonstrator dashboards"`).

### Task 5: Docs + Header nav + verification wiring

**Files:**
- Create: `docs/INSTRUCTOR_DEMO.md`
- Modify: `frontend/src/components/header/Header.tsx` (role-gated Professor/Demonstrator links)
- Modify: `frontend/src/mocks/handlers.ts` (auth `/me` role passthrough for demo)

**Interfaces:**
- Consumes: existing credentials (`admin/admin123`, `superadmin/superadmin123`) + demo JSON logins (`professor.ada / demonstrator.turing` demo-mode only).
- Produces: docs table (roles × routes × capabilities), JSON location, ANIMATION-gate note, skill-graph slug note.

- [ ] **Step 1: Write docs** with credentials table, route inventory, demo-vs-live boundary, validation pipeline section.
- [ ] **Step 2: Header nav test** (`Header.test.tsx` asserts Professor link visible for professor role, hidden for student).
- [ ] **Step 3: Implement nav + docs.**
- [ ] **Step 4: Run `pnpm test:run`, `pnpm typecheck`, `pnpm lint`.**
- [ ] **Step 5: Commit** (`git commit -m "docs: add instructor demo guide and role nav"`).
