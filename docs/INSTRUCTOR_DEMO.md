# Instructor Demo — Professor + Demonstrator Dashboards (Issue #159, Phase 2)

Demo-mode dashboards for professors (class owners) and demonstrators (TAs, limited access).
This PR ships **phase 2** (dashboard aggregates) using a committed JSON dataset so reviewers
can click through everything **without touching the live database**. Supabase remains the
only runtime database; the JSON file is a transient demo/bootstrap source only.

## Demo dataset

- File: `frontend/src/data/instructor-demo.json` (also imported by `frontend/src/features/instructor/demo.ts`)
- Contents:
  - **Professors:** Prof. Ada Lovelace (`professor.ada`, `prof-ada-01`) — created
    `python-fundamentals` + `data-structures`; Prof. Grace Hopper (`professor.grace`,
    `prof-grace-02`) — created `data-structures`
  - **Demonstrator:** Alex Turing (`demonstrator.turing`, `ta-alex-01`, role `ta`) —
    assigned to `class-cs101-a` + `class-cs201-b`, read-only
  - **Classrooms:** `CS101 · Section A` (invite `CS101-A-2026`, 5 students) and
    `CS201 · Section B` (invite `CS201-B-2026`, 3 students)
  - **Cool features shown:** invite-code roster cards, per-student completion/solved/attempts,
    at-risk detection (completion < 35% or ≥10 unsolved attempts), skill-mastery bars
    (`arrays`, `strings`, `hash-maps`, `two-pointers`, `stacks-queues`, `recursion`,
    `trees`, `graphs`, `dp-1d` — all real skill slugs), plateau/activity signals,
    student detail with coaching entry points

## Verify roles with existing credentials

Seeded logins (see `backend/scripts/seed_admin.py` — run
`DATABASE_URL=... python backend/scripts/seed_admin.py` to create them;
usernames match `frontend/src/data/instructor-demo.json`):

| Login | Password | Role | Sees |
|---|---|---|---|
| `admin` | `admin123` | `admin` | Admin panel + professor + demonstrator areas |
| `superadmin` | `superadmin123` | `super_admin` | Everything, incl. user role assignment |
| `professor.ada` | `professor123` | `professor` | `/professor/*` full (login lands here), no admin panel, no demonstrator nav link |
| `demonstrator.turing` | `demonstrator123` | `ta` | `/demonstrator/*` read-only (login lands here), no roster management, no course editing |

Post-login routing (`frontend/src/app/login/page.tsx`): `professor` → `/professor`,
`ta` → `/demonstrator`, `admin`/`super_admin` → `/admin`, everyone else → `/`.
Header shows Professor xor Demonstrator link by primary role (admins see both).

To grant real professor/TA roles on a live instance: log in as `superadmin` →
Admin → Users → set role to `professor` or `ta` (allow-list extended in
`backend/app/api/admin.py`). JWT carries `role` exactly like `admin` today.

## Route inventory (every analytics view is a route)

| Route | Who | What |
|---|---|---|
| `/professor` | professor+ | Overview stats, classroom cards with invite codes |
| `/professor/courses` | professor+ | Created courses with `full_validate` + animation badges |
| `/professor/classrooms` | professor+ | Owned sections, invite codes, at-risk counts |
| `/professor/classrooms/[id]` | professor+ | Roster table (manage), per-student links |
| `/professor/analytics` | professor+ | Per-class completion, skill mastery, plateau signals |
| `/professor/students/[id]` | professor+ | Student progress + coaching entry |
| `/demonstrator` | instructor | Assigned sections overview (read-only) |
| `/demonstrator/classrooms` | instructor | Section list (read-only) |
| `/demonstrator/classrooms/[id]` | instructor | Roster read-only |
| `/demonstrator/analytics` | instructor | Same signals, coaching context |
| `/demonstrator/students/[id]` | instructor | Student progress read-only |
| `GET /api/instructor/class-analytics` | instructor (Bearer) | Backend read-only aggregate over existing `course_progress` + `submissions` |

TA permission matrix (enforced in `backend/app/api/auth_deps.py` + UI):
professor-only = roster management, course create/edit, deletes;
professor + TA = roster viewing, analytics, student coaching.

## Verification pipeline + skill graph wiring

- **Animation gate unchanged:** professor course creation links into the existing
  admin curriculum flow (`/admin/curriculum`); every new question still passes
  `QuestionValidatorService.full_validate` including the non-skippable
  `ANIMATION` use case (`animation.steps >= 3`). Demo courses carry
  `validation: { pipeline: full_validate, animationGate: passed }` badges.
- **Skill graph:** demo `skillMastery` references live taxonomy slugs from
  `app/services/skill_taxonomy.py` (`ROADMAP_ORDER`), so the demo renders the
  same skills the backend mastery engine produces. No new tracking tables for MVP.
- **Live boundary:** frontend pages read `demo.ts` (JSON) in this draft; the
  backend `GET /api/instructor/class-analytics` (guarded by `require_instructor`,
  degrades to empty on error) is the live contract phase-1 classroom tables will
  feed. MSW (`frontend/src/mocks/handlers.ts`) stubs `/api/instructor/*` in tests.

## Test & verify locally

```bash
# frontend (no DB needed)
cd frontend
pnpm install
pnpm vitest run src/app/professor src/app/demonstrator src/features/instructor src/components/header
pnpm typecheck
pnpm lint

# backend (ruff + standalone; full pytest needs Supabase isolated schema — CI runs it)
cd backend
ruff check app/api/auth_deps.py app/api/instructor.py app/api/dependencies.py app/main.py app/services/class_analytics_service.py
ruff format --check app/api/auth_deps.py app/api/instructor.py app/api/dependencies.py app/main.py app/services/class_analytics_service.py
```
