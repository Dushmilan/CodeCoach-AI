# Full-Product Audit — 3 Golden Journeys (Issue #294)

**Date:** 2026-09-23
**Auditor:** automated agent session (Playwright MCP + OTEL)
**Branch:** `test/294-full-product-audit`
**Sibling:** concurrency audit of classroom data — #295
**Verdict:** journeys functionally reachable; **3 defects** found (1 high, 2 medium) and **2 content/environment gaps**. No security/isolation leak found.

---

## 1. Environment

| Component | Value |
| --- | --- |
| Frontend | Next.js 14 dev, `http://localhost:3000`, `NEXT_PUBLIC_API_URL=""` (same-origin `/api` rewrite) |
| Backend | FastAPI + uvicorn, `http://localhost:8000`, `ENVIRONMENT=development` |
| Database | local PostgreSQL branch DB `codecoach_294_full_product_audit` (schema from ORM metadata + `alembic stamp head`) |
| Cache | Redis 7, `redis://localhost:6379/0`, `REDIS_ENABLED=true` |
| Code execution | Piston `http://localhost:2000/api/v2` (runtimes: python 3.10.0, javascript 18.15.0) |
| Animation viewer | motion-canvas-lab Vite dev, `http://localhost:9002` (`NEXT_PUBLIC_ANIMATION_VIEWER_URL`) |
| Tracing | OTEL enabled, `OTEL_ENABLED=true`, OTLP HTTP → local receiver on `:4318` → `/tmp/opencode/otel-spans.jsonl` |
| Browser | Playwright MCP (isolated profile), desktop 1280×800 |

**Seed data (prepopulated as required by the issue):**

| Seed | Result |
| --- | --- |
| `seed_e2e.py` | admin + superadmin + questions `two-sum`, `contains-duplicate` |
| `seed_classroom_demo.py` | professors ada/grace, 2 TAs, **15 students**, 2 classrooms, 19 enrollments, progress mirror |
| `seed_skill_graph.py` | 30 taxonomy rows (`skills`, `question_skills`) |

> Note: `seed_skill_graph.py` was **required** to exercise personalization. Before it ran, the taxonomy was empty and "Practice next" fell back to the static cold-start default — a seed gap, not an app behaviour.

---

## 2. Method

- Drive the real UI with Playwright MCP (screenshots at every step, console errors recorded per page).
- Capture backend spans via the app's opt-in OTLP export; correlate each journey step to a `trace_id`.
- Verify cache behaviour at the Redis key level and the DB-scan level (observed, not assumed).
- Snapshot seeded rows before/after and attribute every mutation.

**Evidence artifacts** (transient, not committed):
- Screenshots: `/home/dushmilan/Desktop/CodeCoach-AI/.playwright-mcp/audit/*.png`
- OTEL spans: `/tmp/opencode/otel-spans.jsonl` (**431 spans, 431 trace ids**)
- Backend log: `/tmp/opencode/backend.log`

Console-error note: `401 /api/usage` and `401 /api/auth/refresh` on anonymous pages are expected probes, plus `404 /favicon.ico`. Not defects.

---

## 3. Journey 1 — Student (new → returning) — PASS with defects

`register → dashboard → solve question (run + submit) → learn → animate`

| Step | Result | Evidence |
| --- | --- | --- |
| Register new user `audit_student_1` | PASS — HTTP 201 → `/` | `j1-01-register.png`, `j1-02-after-register.png`; trace `RxyQXyo8tqaLSQThFrOyIg==` |
| Problems + "Practice next" (new user) | PASS — panel renders | `j1-03-problems.png` |
| Open Two Sum | PASS — Monaco, Run/Submit/Animate, AI Coach panel | `j1-04-two-sum.png` |
| **Run** (live Piston) | PASS — "Test Results: 1/1 passed" | `j1-06-run-result.png`; trace `JBlVGzl9QKCesCv0cgdRoQ==` |
| **Submit** | PASS — "All tests passed!" toast + server submission row | `j1-07-submit.png`; trace `v0bEuNyEZ8Gi2JgsPPHIxA==` |
| **Animate** | PASS — dialog + viewer canvas, "2 / 5", narration "Compare [0]=2" | `j1-19-animate-9002.png`; trace `oNNf5YbMkDAkftMhEpKCPg==` |
| Dashboard skill graph | PASS — "26 skills • 26 prerequisite links"; Arrays → *learning* | `j1-12-dashboard.png` |
| Learn | Renders ("Python Fundamentals", "Data Structures") | `j1-13-learn.png` |
| Learn → course | **GAP** — progress `0/0`, no modules/lessons | `j1-14-course.png` |
| Returning: logout → login `audit_student_1` | PASS — HTTP 200, "Continue where you left off: Two Sum" | `j1-20..22-*.png` |
| Returning: solved status after fresh browser | **DEFECT F2** — table shows "Not started" for a solved question | `j1-22-returning-problems.png` |

### "What's next" adaptation (explicit requirement)

Measured on a fresh user `audit_student_2` before vs after solving Two Sum:

| | Recommendation | Reason text |
| --- | --- | --- |
| Before solve | Two Sum (Arrays) | "Start learning Arrays." |
| After solve | Two Sum (Arrays) | "Master Arrays first; it unlocks other skills." |

The **reason updates** with progress (personalization works), but the **suggested question is unchanged and already solved** — see DEFECT F1.

---

## 4. Journey 2 — Professor — PASS with 1 defect

`login → create course → view class analytics`

| Step | Result | Evidence |
| --- | --- | --- |
| Login `professor.ada` | PASS — 200 → `/professor`; nav Overview/Courses/Curriculum/Classrooms/Analytics | `j2-01-professor.png`; trace `7o/a8RRBNQVzQRPKt5CKmQ==` |
| Courses list | PASS — 2 courses, `full_validate · animation passed` badges | `j2-05-courses.png` |
| **Create course** | **FAIL — HTTP 422 "Field required; Field required"** | `j2-07-course-created.png`; DEFECT F3 |
| Classrooms | PASS — `CS101 · Section A`, invite code, 8 students, 88.8%, 0 at risk | `j2-03-classrooms.png` |
| Class Analytics | PASS — Students 8, Avg completion 88.8%, Avg solved 0, signals empty state | `j2-04-analytics.png`; trace `HB2kuovUqE/seTbf3pfUVw==` (shared with TA) |

---

## 5. Journey 3 — Demonstrator (TA) — PASS

`login → view class analytics`

| Step | Result | Evidence |
| --- | --- | --- |
| Login `demonstrator.turing` (role `ta`) | PASS — 200 → `/demonstrator`; nav has **no** course-edit/roster-management | `j3-01-ta.png` |
| Class Analytics | PASS — both sections: CS101 (8 students, 88.8%), CS201 (7 students, 75.7%); "No at-risk students" | `j3-02-ta-analytics.png` |
| Scope: TA → `/professor` | PASS — "Access Denied — You need professor privileges" | `j3-03-ta-professor-blocked.png` |
| Anonymous → `/demonstrator/analytics` | PASS — redirected to `/login`; **no demo fixture leaked** | `j3-04-anon-no-leak.png` |
| Plain user → instructor API | PASS — `403 {"detail":"Insufficient permissions: instructor role required"}` | (curl evidence) |
| Plain user → professor API | PASS — `403 {"detail":"Insufficient permissions: professor role required"}` | (curl evidence) |

---

## 6. Cache verification (observed)

| Check | Method | Result |
| --- | --- | --- |
| Anonymous course-list key | Redis | `codecoach:courses:list:anonymous`, TTL 30 |
| Miss vs hit | 1st GET 13 ms; subsequent 6–8 ms | PASS — faster on hit |
| TTL expiry | wait 32 s | PASS — key gone (`ttl=-2`) |
| **Stampede lock** | cold key + **30 concurrent** GETs; DB scan delta | PASS — `courses` seq_scan **10 → 11** (**1** upstream build), lock key released |
| Invalidation on write | professor PUT `/api/professor/courses/python-fundamentals` → 200 | PASS — key deleted (`ttl=-2`) |

---

## 7. Seeded-data integrity (real users altering seeded data)

| Metric | Baseline | After full audit | Verdict |
| --- | --- | --- | --- |
| Users | 21 | 23 (+2 audit users) | expected |
| Classrooms | 2 | 2 | unchanged |
| Enrollments | 19 | 19 | unchanged |
| Audit users enrolled in seeded classrooms | — | **0** | no contamination |
| CS101 analytics | 8 students / 88.8% | 8 students / 88.8% | unchanged |

Real user activity (registering, solving, learning, animating) **did not alter** seeded classroom data. No isolation/security defect found.

---

## 8. Findings

### F1 — "Practice next" re-serves an already-solved question — **Medium** — #297

- **Where:** `backend/app/services/skill_graph_rules.py::recommend` (suggested question = `question_by_skill[slug][0]`), `backend/app/services/skill_graph_service.py::get_recommended_questions` (cold-start `_resolve_ids`), `frontend/src/features/skill-graph/RecommendedQuestions.tsx`.
- **Behaviour:** after solving Two Sum, the panel's *reason* updates (`NEW_SKILL` → `MISSING_PREREQUISITE`) but the suggested question stays `two-sum`. The cold-start default (`DEFAULT_COLD_START_QUESTION_IDS`) is also static and includes solved questions.
- **Impact:** the concrete "what's next" action does not reflect solved history, which is the explicit product requirement.
- **Caveat:** the 2-question branch bank limits alternatives for `arrays`; severity may be higher with the full bank. Question-level solved-exclusion appears absent regardless.
- **Repro:** fresh user → `/problems` (note Two Sum) → solve Two Sum → `/problems` (Two Sum still suggested).
- **Evidence:** `j1-09-next-before-solve.png`, `j1-11-next-after-solve.png`; trace `e2oMmh6Mp8ZlCIn7ehlNDQ==`.

### F2 — Problem-list solved status is client-local only — **Medium** — #298

- **Where:** `frontend/src/app/problems/page.tsx:49` (`useLocalStorage<...>('user_progress', {})`), `frontend/src/features/question/use-code-runner.hook.ts:61`.
- **Behaviour:** the STATUS column is derived solely from `localStorage.user_progress`; nothing rehydrates it from the server on load. A returning user on a fresh browser (or after storage clear) sees **"Not started"** for questions the server knows are solved — even though "Continue where you left off" (server-driven) shows the same question.
- **Impact:** returning-user progress appears lost cross-device; contradicts the "solved/attempted history" requirement.
- **Repro:** user solves Two Sum → DB `submissions` has the row (verified: 1 row for `audit_student_1`) → clear localStorage → log in → problems table shows "Not started".
- **Evidence:** `j1-22-returning-problems.png`; DB query `select count(*) from submissions` → 1.

### F3 — Professor "Create course" always fails 422 — **High** — #296

- **Where:** professor curriculum form (only a title input) vs `backend/app/api/professor.py::create_owned_course` + `backend/app/models/admin_models.py::CourseCreate` (requires `id`, `title`, `description`, `language`, `order`).
- **Behaviour:** the form POSTs `{"title":"Audit Course 294","description":"","language":"python"}` to `/api/professor/courses`; the API rejects with 422 ("Field required; Field required") because `id` and `order` are missing. Course creation is unreachable from the professor UI.
- **Impact:** a core professor workflow (create course) cannot complete; also blocks the intended cache-invalidation-on-create check from that path.
- **Repro:** `professor.ada` → `/professor/curriculum` → enter title → **Create course** → 422.
- **Evidence:** `j2-07-course-created.png`; captured request body `{"title":"Audit Course 294","description":"","language":"python"}`; trace `Pq/S1qCgdK/KSOE+mBwKAg==`.

### G1 — Learn content empty (seed gap, not a bug) — Info

- `modules=0`, `lessons=0` in the branch DB, so a course page shows `0/0`. The Learning Paths list and the empty course state render correctly. Needs a curriculum content seed for full coverage; the UI is not defective.

### G2 — Animation viewer is an external dependency — Info

- The launcher defaults to `http://localhost:9000` (`AnimateLauncher.tsx`). A pre-existing viewer instance on `:9000` rendered no canvas in this environment; with a correctly built viewer on `:9002` the animation rendered (canvas, 5 steps). Not an app defect — an operational dependency worth documenting.

---

## 9. Acceptance criteria status

| Criterion | Status |
| --- | --- |
| 3 journeys executed end-to-end with screenshot evidence | ✅ |
| OTEL traces captured; screenshot steps correlated to trace ids | ✅ (431 spans / 431 traces) |
| New-user vs returning-user behaviour documented | ✅ (incl. F2) |
| "What's next" verified against solved/attempted history | ✅ → F1 |
| Cache verified (hit / miss / invalidation / TTL / stampede) with evidence | ✅ |
| Seeded-data baseline diff clean, or defects raised | ✅ clean |
| Full checklist audited | ✅ (Auth, Problems, Learn, Animate, Coach, Professor, TA, Admin-adjacent, Cache, Errors) |
| Each defect raised as its own child issue | ✅ #296 (F3, high), #297 (F1), #298 (F2) |

## 10. Limitations & deferred

- **Viewport:** this pass ran at desktop **1280×800**. The mobile **390×844** sweep from the
  issue's evidence requirements was **not** executed; it remains to be done before the
  journey is considered fully closed.
- **Concurrency:** classroom data under parallel users (lost updates, double-counts,
  stampede under parallel writers, isolation across real users) is tracked separately in
  #295 and not covered by this single-user pass.
