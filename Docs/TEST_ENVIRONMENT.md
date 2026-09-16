# Test & Branch Environment — Database

> Local-first PostgreSQL. Each git branch gets its own database
> (`codecoach_<slug>` via `backend/scripts/branch_db.py`); live is written
> only through the versioned promotion flow. The former hosted Supabase
> project (and Google OAuth via Supabase) is decommissioned — see #168.

This document is the source of truth for how environments are wired.

---

## 1. Environment matrix

| | Branch workspace (daily work) | Live |
| --- | --- | --- |
| Status | ✅ **Work here** | gated promotion only |
| Database | local PostgreSQL `codecoach_<slug>` | hosted PostgreSQL |
| `ENVIRONMENT` | `development` | `production` (fail-closed) |
| App runtime | localhost (Docker Compose or direct uvicorn) | hosted backend (future) |

Create the branch database (schema comes from the ORM — single source of truth):

```bash
cd backend
python scripts/branch_db.py init --url "postgresql://codecoach:codecoach@127.0.0.1:5432/codecoach_<slug>"
```

Point the app at it (`backend/.env` or root `.env`, both gitignored):

```
ENVIRONMENT=development
DATABASE_URL=postgresql://codecoach:codecoach@127.0.0.1:5432/codecoach_<slug>
JWT_SECRET_KEY=<random 64-hex>
GROQ_API_KEY=gsk_...                      # AI coaching (real key)
PISTON_API_URL=http://piston:2000/api/v2
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## 2. Data flow (`backend/scripts/branch_db.py`)

| Command | Direction | Gate |
| --- | --- | --- |
| `pull --from <LIVE> --to <LOCAL>` | live → local (read-only SELECTs) | refuses non-localhost destinations |
| `promote --from <LOCAL> --to <LIVE>` | local → live (upsert-only `merge()`) | refuses localhost targets AND requires `PROMOTE_TO_LIVE=YES-I-AM-SURE` |
| `status --url <URL>` | read-only row counts | — |

Copied tables, FK-safe order: `courses → questions → modules → lessons`.
Course `owner_id` is nullable, so no users travel with the curriculum; demo
users are created by the seed scripts, never copied.

---

## 3. Auth

Username/password only (bcrypt + HS256 JWT, `POST /api/auth/login|register|refresh`).
The former Google-OAuth path (`POST /api/auth/supabase`, `/auth/callback`,
`@supabase/ssr` + `@supabase/supabase-js`) was removed in #168 — no OAuth
configuration exists anymore.

---

## 4. Migrations

Live schema moves via Alembic only:

```bash
cd backend
export DATABASE_URL="<live session-pooler URL>"
.venv/bin/alembic upgrade head
```

Fresh branch databases do not need migrations — `branch_db.py init` builds the
schema from the ORM metadata.

**Never** run tests against live — the suite refuses non-local hosts
(`backend/tests/db_guard.py`, overridable only with `ALLOW_PRODUCTION_TEST_DB=1`).

Test isolation details (`backend/tests/conftest.py`):
- Each run needs a reachable local PostgreSQL (`DATABASE_URL`; defaults to
  `127.0.0.1:5432` when unset) and creates an isolated schema
  (`codecoach_test`, or `codecoach_test_gwN` per xdist worker) set via
  `DATABASE_SEARCH_PATH`, dropped afterwards.
- Shared auth builders: `backend/tests/fixtures/auth_helpers.py`
  (`register_headers`, `register_user_headers`, `admin_headers`, `aregister_headers`).
- Seed bank: 50 questions (5 hand-written + 45 generated) plus the 107 live ids
  (`backend/tests/fixtures/live_question_ids.json`).

---

## 5. Gotchas / notes

- Passwords and keys live in the environment or gitignored `.env` / `.env.seed`
  files (mode 0600) — never in desktop notes, chat logs, or committed files.
- When live is eventually reconfigured: create the hosted PostgreSQL project,
  rotate `JWT_SECRET_KEY` + `GROQ_API_KEY`, and update every variable in this
  doc for that target. Never copy branch credentials to live.
