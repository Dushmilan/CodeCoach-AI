# E2E Tests (Playwright)

## Prerequisites

| Service | URL | How |
|---|---|---|
| Backend | `http://localhost:8000` | `python -m uvicorn app.main:app --port 8000` (from `backend/`) |
| Frontend | `http://localhost:3000` | `pnpm dev` (from `frontend/`, `NEXT_PUBLIC_API_URL=""` so `/api` proxies to the backend) |
| Animation viewer | `http://localhost:9000/viewer.html` | `pnpm dev --port 9000` (from `motion-canvas-lab/`) |
| Postgres / Redis / Piston | compose defaults | `docker compose up -d postgres redis piston` |

Notes:

- Use the hostname `localhost` (not `127.0.0.1`) for the viewer: its Vite dev
  server binds `localhost`, which may resolve to IPv6 `::1`.
- The Playwright config boots the frontend and viewer automatically via
  `webServer` (`reuseExistingServer: true`); start the backend yourself.

## Seeding

Specs assume seed data — an admin login plus sample questions:

```bash
cd backend
DATABASE_URL=postgresql://codecoach:codecoach@127.0.0.1:5432/codecoach_test \
DATABASE_SEARCH_PATH=public \
python scripts/seed_e2e.py   # idempotent, safe to re-run
```

This creates `admin/admin123` (+ `superadmin`) and the `two-sum` /
`contains-duplicate` questions that the problems-table and code-execution
specs navigate to. Without the seed, those specs fail on an empty table —
that is a seed gap, not an app bug.

## Running

```bash
cd frontend
pnpm playwright test --project=chromium e2e/homepage.spec.ts
```

`viewer-render.spec.ts` and `animate-flow.spec.ts` additionally need the
viewer service above. Live Piston is required for code-execution specs;
live Groq is never required (AI specs use MSW mocks).
