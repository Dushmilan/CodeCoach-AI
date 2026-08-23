# CodeCoach-AI — Remaining Work Plan

> Generated from `Docs/AUDIT_REPORT.md` + `Docs/REMEDIATION_PLAN_2026-08-15.md`,
> verified against the codebase (Aug 15, 2026). Every code task follows TDD
> (red → green → refactor), caveman-review on the staged diff, and a Docker
> rebuild before commit (per `AGENTS.md`).

**Legend:** 🟢 no code / ops · 🔴 release-blocking · 🟠 high · 🟡 medium · 🔵 low

**Status:** ✅ Security phase (SEC-1..4) is complete. The plan below is the
remaining product, quality, testing, and ops backlog.

---

## Phase 0 — Ops (no code, do first)

### OPS-1 · Apply pending migrations to live Supabase — ✅ DONE (already at head e1f2a3b4c5d6, verified)
- **What:** `alembic upgrade head` (head = `e1f2a3b4c5d6`) via `DIRECT_URL` (session pooler).
- **Applies:** `c8d0e1f2a3b4` (repair `rate_limit_events` + `request_count`), `d9e1f2a3b4c5` (`submissions`), `e1f2a3b4c5d6` (public `request_count`).
- **Verify:** `alembic heads` = single head; `alembic current` = head; `/health/` → `questions_db == "ok"`.
- **Dep:** none. **Blocks:** any backend deploy.

### OPS-2 · Remove + rotate leaked creds (T0.2) — 🟡 PARTIAL (backend/.env cleaned; rotation deferred)
- **What:** delete `DATABASE_URL`/`DIRECT_URL` from `backend/.env`; export a local test URL only before `pytest` (per `backend/tests/README.md`).
- **Then:** rotate the Supabase DB password + any secret that appeared in plaintext on this machine.
- **Verify:** `grep -c DATABASE_URL backend/.env` → 0; tests still pass via exported local URL.
- **Blocks:** any production deployment (do before wiring the prod Supabase project).

### OPS-3 · Restart dev stack with real config (T0.1) — ✅ DONE (health ok, questions_db ok)
- **What:** `docker-compose up -d --build`; confirm "Database reachable; Alembic migration state present"; `curl :8000/health/` green.

---

## Phase 1 — Product features (by leverage) 🟠

> The features that finish the product moat: mistake-memory (F2), skill-aware
> practice (F3), and curriculum breadth (F5). Each lands as its own commit,
> TDD, with a Docker rebuild.

---

### F2 · Durable rescue re-surface queue 🟠  — ✅ DONE (Aug 23, branch `feat/rescue-resurface-queue`)
> **Implementation notes (deviations from the spec below):**
> - Stored statuses are only `abandoned | completed | dismissed`; **"due" is derived**
>   (`status='abandoned' AND due_at <= now()`) so no scheduled job is needed to flip states.
> - Dismissal permanence is enforced via a `latest()` repo lookup (a dismissed question
>   can never be re-opened by a later abandonment).
> - Repeat abandonment schedules `max(existing_due + 1 day, next 09:00)` — never in the past.
> - Client sends `tz_offset_minutes` east-positive (`-getTimezoneOffset()`); due date is
>   tomorrow 09:00 in the client's own morning.
> - ✅ Live DB updated (Aug 23): after the Supabase TEST project resume, `alembic upgrade head`
>   applied `f2a3b4c5d6e7`; verified table + partial unique index + both FKs on live, `alembic current` = head.

**Goal / user value**
The workspace already captures "abandoned problems" client-side
(`useRescueContract` → `rescue.storage.ts`, localStorage). Today they only
resurface as a static list on `/problems`. F2 makes that **durable and
time-based**: every abandoned problem becomes a "due today" item the next day
as a tiny, re-entry step — the "no-loss economy" of the mistake-memory moat.

**Current state (verified)**
- Frontend-only: `useRescueContract.hook.ts` writes `AbandonedProblem`
  (`questionId`, `title`, tier) into localStorage under `RESCUE_STORAGE_KEY`.
- No backend persistence, no due-date logic, no "resurfaces tomorrow" queue.
- `submissions` table (F1) is live — the mistake-memory data layer exists.

**Data model (new migration)**
- Reuse the `RescueIntervention` concept already referenced in `Progress.md`
  (checkpoints + flow maps exist). Add a durable record:
  - `rescue_queue` table: `id (uuid pk)`, `user_id (fk)`, `question_id (fk)`,
    `status` (`abandoned` | `due` | `completed` | `dismissed`),
    `first_abandoned_at`, `due_at` (next re-surface time),
    `resurface_count`, `last_intervention_at`, `created_at`, `updated_at`.
  - Index: `(user_id, status, due_at)` — the "what's due for me today" query.
- Idempotent upsert: one open row per (user, question).

**API surface (new `app/api/rescue.py`, port + `sql_*` repo)**
- `GET /api/rescue/due` — due items for the current user (filter
  `status='due' AND due_at <= now`, ordered by `due_at`).
- `POST /api/rescue/{question_id}/abandon` — mark abandoned, set
  `due_at = tomorrow 09:00 local` (first time), or push one day out on repeat
  abandonment; idempotent.
- `POST /api/rescue/{question_id}/complete` — close the row
  (`status='completed'`).
- `POST /api/rescue/{question_id}/dismiss` — "leave me alone" for this
  question (`status='dismissed'`, never re-surfaces).
- Auth: `get_current_user` on all routes.

**Frontend**
- Replace localStorage in `useRescueContract`'s abandon path with the API
  (keep localStorage as an offline fallback only).
- `/problems` queue UI: render `GET /api/rescue/due` as a "Back tomorrow"
  section (reuse existing `AbandonedProblem` card styling).
- On solving a due question, call `complete` and remove from the queue.

**TDD red tests**
- Backend (integration, fresh client + mocked repo):
  - abandon → row created with `due_at` tomorrow; re-abandon same question
    is idempotent (no duplicate rows).
  - `due` returns only rows where `due_at <= now` and `status='due'`.
  - complete/dismiss transition the row; dismissed never re-surfaces.
- Frontend: hook calls the API on abandon; queue renders due items; solving
  removes the item.

**Files:** `backend/alembic/versions/<rev>_add_rescue_queue.py`, port +
`sql_rescue_repository.py`, `app/api/rescue.py`, `app/api/dependencies.py`,
`frontend/src/features/rescue/*`, `frontend/src/app/problems/page.tsx`.
**Effort:** Medium. **Dep:** OPS-1 (submissions live — done).

**Definition of done**
- Due queue survives page reloads and returns next day; no duplicates;
  dismiss is permanent; full gates green.

---

### F3 · Skill-graph mapping 21 → 109 🟠 — every question recommendable

**Goal / user value**
"Practice Next" only works for questions mapped to skills. Today 25 mapping
entries exist in the taxonomy (~21 match live questions), so most of the 109
seeded questions return no recommendations. F3 maps the remaining ~88 so every
question resolves a skill-based next-step.

**Current state (verified)**
- `backend/app/services/skill_taxonomy.py`: `SKILLS` taxonomy + `QUESTION_SKILLS`
  dict with 25 entries (`two-sum`, `contains-duplicate`, `group-anagrams`, …).
- `question_skills` table exists on live (verified earlier); seed script
  `backend/scripts/seed_skill_graph.py` is idempotent by natural key.
- `Progress.md`: 21 of 109 live questions mapped; 4 mapping IDs are test-only
  (not present in the DB) — those rows are currently dead.

**Work**
1. **Audit the taxonomy** against the live question inventory (109): list the
   unmapped question IDs + their `category`/`difficulty`, propose a skill per
   question (reuse the ~25 existing skills where they fit; add new skills only
   when a category genuinely lacks one — keep the taxonomy tight).
2. **Extend `skill_taxonomy.py`** `QUESTION_SKILLS` to cover all 109 (aim:
   every seeded question maps to ≥1 skill).
3. **Fix the 4 test-only mapping IDs** — re-point or drop them so every
   mapping row resolves to a real question.
4. **Backfill the live DB** — re-run `seed_skill_graph.py` (idempotent);
   verify `question_skills` row count ≥ 109.
5. **Regression guard** — a test asserting every seeded question resolves ≥1
   recommendation via `GET /api/skills/me/recommendations`.

**TDD red tests**
- Backend: new unit test over `skill_taxonomy.py` — every live question id
  (from a fixture of the 109) has ≥1 skill mapping; every mapping id exists in
  the live question set (no dead/test-only ids).
- Integration: for a sample of mapped questions, `/api/skills/me/recommendations`
  returns a non-empty list after seeding.

**Files:** `backend/app/services/skill_taxonomy.py`, `backend/scripts/seed_skill_graph.py`,
`backend/tests/unit/test_skill_taxonomy.py` (new), `backend/tests/integration/test_skill_graph_api.py`.
**Effort:** Medium (mostly taxonomy curation).

**Definition of done**
- 109/109 mapped in the taxonomy; `question_skills` ≥ 109 rows on live;
  every mapping resolves to a real question; recommendations non-empty for
  mapped questions.

---

### F5 · C / Java curricula 🟡 — curriculum breadth

**Goal / user value**
The curriculum is Python-only today. C and Java unlock the language-oriented
interview market (and the existing code-execution + validation stack already
supports both via Piston wrappers). Target: 15–20 C lessons + 15–20 Java
lessons, structured like Python Fundamentals (modules → lessons → exercises).

**Current state (verified)**
- Schema supports arbitrary languages (`course_schemas.py`; curriculum lives in
  Supabase — seeded via `backend/scripts/sync_local_to_db.py` reading
  `data/courses/**`, which is not in git).
- Admin CRUD for curriculum exists (question/lesson forms, `MarkdownPreview`).
- Code execution supports `c`, `cpp`, `java` wrappers already.

**Work**
1. **Author C curriculum** (2 modules × ~8 lessons): syntax/fundamentals,
   pointers & memory, strings, structs, functions, debugging — each lesson
   theory + optional coding exercise (starter code + tests).
2. **Author Java curriculum** (2 modules × ~8 lessons): syntax/OOP, classes &
   objects, collections, exceptions, I/O, build/run basics.
3. **Land the content as JSON** under `backend/data/courses/c/` and
   `backend/data/courses/java/` (matching the Python structure the sync script
   expects), then `python scripts/sync_local_to_db.py` (idempotent upsert).
4. **Wire the learn UI** — the course list/module tree should render the new
   languages (verify `/learn`, `/learn/[courseId]`, lesson page for a C and a
   Java lesson; fix any hard-coded Python assumptions).

**TDD red tests**
- Backend: curriculum repo returns ≥15 C lessons and ≥15 Java lessons after
  seeding; lesson payloads pass the same schema validation as Python lessons.
- Frontend: lesson page renders a C and a Java lesson (exercise + editor
  language wiring) — extend existing `use-lesson.hook.test.ts` fixtures.

**Files:** `backend/data/courses/{c,java}/**` (content), `backend/scripts/sync_local_to_db.py`,
`backend/tests/integration/test_courses_endpoints.py`, frontend lesson fixtures.
**Effort:** High (content authoring).

**Definition of done**
- 15–20 lessons per language live in Supabase; a real C and Java lesson
  render + execute end-to-end; admin CRUD edits them.

---

## Phase 2 — Code quality / maintainability

| ID | Task | Red test | Effort |
|---|---|---|---|
| M-01 | Split `LessonPage.tsx` (381 lines) into `EditorPanel`/`ChatPanel`/`LessonSidebar`/`ProgressBar` | existing lesson page tests keep passing | High |
| M-02 | Split `schemas.py` (500 lines) into `coach/execution/question` modules | import parity test | Medium |
| M-03 | Add TanStack Query; replace manual `useEffect` fetch hooks | existing hook tests (15 files) stay green | Medium |
| M-04 | Fix N+1 filtered count — `total = len(summaries)` → SQL `COUNT(*)` in repo | assert repo issues a single `COUNT` query (query-count spy) | Low |
| M-07 | Keyset cursor pagination for `/api/questions` + admin list endpoints | contract test for `next_cursor` response shape | Medium |
| L-01 | Standardize on `lucide-react`; drop `@radix-ui/react-icons` | visual/typecheck | Low |
| L-02 | Move hardcoded Tailwind colors to CSS custom properties | snapshot | Low |
| L-03 | Add `@next/bundle-analyzer`; budget in CI | CI gate | Low |
| L-07 | `/api/v1/` version prefix + plan migration | contract tests updated | Medium |

---

## Phase 3 — Testing & observability gaps

| ID | Task | Effort |
|---|---|---|
| T-1 | k6 load tests for coach + submit endpoints (`tests/load/`) | Medium |
| T-2 | Mutation testing (`mutmut`) on core services | Medium |
| T-3 | axe-core a11y assertions in Playwright E2E | Medium |
| T-4 | testcontainers for Postgres + Redis integration | High |
| T-5 | Visual regression (Playwright + Percy/Chromatic) | High |
| OBS-1 | `/metrics` Prometheus endpoint + Redis hit-rate/cache metrics | Medium |
| OBS-2 | OpenTelemetry distributed tracing | High |
| CI-1 | Add Dependabot config (`.github/dependabot.yml`) + `pip-audit`/`pnpm audit` in CI | Low |

---

## Phase 4 — Long-term / product

- **Docs:** ADRs for key decisions; onboarding guide; env-var reference (CONTRIBUTING.md exists — extend).
- **Admin analytics dashboard** (use existing `/api/admin/stats`).
- **Audit-log retention & export** (re-add consumed tables — currently dropped).
- **Feature-flag system** (re-add the table only when a consumer exists).
- **Multi-provider AI fallback** (Gemini behind `CoachingProvider` port).
- **API versioning rollout** (L-07 above).

---

## Suggested execution order

1. **Phase 0** OPS-2 (rotation before prod wiring) — the only open ops item.
2. **Phase 1** F2 → F3 → F5 (product moat, by leverage).
3. **Phase 2** M-04 → M-01 → M-02 → M-03 → M-07 (quality), interleaving low items.
4. **Phase 3** T-1 → CI-1 → OBS-1 → rest.
5. **Phase 4** as capacity allows.
