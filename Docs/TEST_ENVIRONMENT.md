# Test Environment — Database & OAuth

> ⚠️ **IMP — the current Supabase project is the TEST database, and the Google
> OAuth integration is TEST OAuth. A production database is NOT configured yet.**
> Last verified: 2026-08-15 (migration head re-verified Sep 04, 2026: `b4c5d6e7f8a1`).

This document is the source of truth for how the **test** environment is wired.
Nothing here is production.

---

## 1. Environment matrix

| | Test (current) | Production |
| --- | --- | --- |
| Status | ✅ **Live now** | ❌ Not configured yet |
| Supabase project ref | `qazpxjpcvsjbmgbzuxxp` | — |
| Supabase URL | `https://qazpxjpcvsjbmgbzuxxp.supabase.co` | — |
| DB role | `postgres` on that project | — |
| `ENVIRONMENT` | `development` | `production` (fail-closed) |
| App runtime | localhost (Docker Compose) | Cloudflare Workers + hosted backend (future) |

The app's `DATABASE_URL` / `DIRECT_URL` in `.env` **point at the test project**.
Migrations are applied there (`alembic upgrade head`), and the dev stack reads
and writes this test DB only.

---

## 2. Where the credentials live

Both files are **gitignored** — never commit them.

| File | Used by |
| --- | --- |
| `.env` (repo root) | `docker-compose` (the running stack) |
| `backend/.env` | `make dev-backend` (direct uvicorn runs) |

Key variables:

```
ENVIRONMENT=development
DATABASE_URL=postgresql://postgres.<ref>.<region>.pooler.supabase.com:6543/postgres?pgbouncer=true
DIRECT_URL=postgresql://postgres.<ref>.<region>.pooler.supabase.com:5432/postgres   # migrations
JWT_SECRET_KEY=<random 64-hex>
GROQ_API_KEY=gsk_...                      # AI coaching (real key)
SUPABASE_URL=https://qazpxjpcvsjbmgbzuxxp.supabase.co
NEXT_PUBLIC_SUPABASE_URL=https://qazpxjpcvsjbmgbzuxxp.supabase.co
SUPABASE_ANON_KEY=sb_publishable_...      # same value in both *_ANON_KEY lines
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_...
PISTON_API_URL=http://piston:2000/api/v2
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### 2a. API key model (new Supabase key system)

Supabase replaced the old `anon` / `service_role` JWT keys with:

- **`sb_publishable_...`** — public, for browsers/clients. ✅ **Use this.**
- **`sb_secret_...`** — privileged, server-only. ❌ Never in `.env`/frontend.

The old `eyJ...` `anon` key may still exist under **Settings → API Keys →
Legacy API Keys**; the publishable key is its drop-in replacement.

Where to find them: **Supabase Dashboard → project → ⚙️ Settings (bottom-left) →
API Keys** (direct link: `https://supabase.com/dashboard/project/<ref>/settings/api-keys`).

---

## 3. Google OAuth — TEST OAuth

### 3a. Flow

```
Login page (Continue with Google)
  -> supabase.auth.signInWithOAuth({ provider: 'google', redirectTo: origin + '/auth/callback' })
  -> GET {SUPABASE_URL}/auth/v1/authorize?provider=google&redirect_to=...&redirect_uri=...
  -> 302 to Google consent screen (accounts.google.com)
  -> Google -> {SUPABASE_URL}/auth/v1/callback
  -> Supabase 303 -> {origin}/auth/callback?code=...
  -> callback page exchanges code (SDK, PKCE) -> loginWithSupabase(access_token)
  -> POST /api/auth/supabase  (backend verifies via {SUPABASE_URL}/auth/v1/user)
  -> user session created (auto-creates account on first Google sign-in)
```

### 3b. Registered URLs (verified)

| Item | Value |
| --- | --- |
| Supabase project URL | `https://qazpxjpcvsjbmgbzuxxp.supabase.co` |
| Authorization endpoint | `.../auth/v1/authorize` (legacy/SDK) and `.../auth/v1/oauth/authorize` (new OIDC) |
| Token endpoint | `.../auth/v1/oauth/token` |
| OIDC discovery | `.../auth/v1/.well-known/openid-configuration` |
| JWKS | `.../auth/v1/.well-known/jwks.json` |
| **Google redirect URI** (in Google Cloud Console) | `https://qazpxjpcvsjbmgbzuxxp.supabase.co/auth/v1/callback` |
| App callback (dev) | `http://localhost:3000/auth/callback` (allowed in Supabase URL config) |

The new OIDC endpoints require an OAuth `client_id` + `redirect_uri` (a
separate, dashboard-registered OAuth application); the **SDK flow uses the
legacy `/auth/v1/authorize` endpoint** with the publishable key, which is what
the app's "Continue with Google" button uses.

### 3c. Dashboard configuration (already done)

- ✅ **Authentication → Providers → Google** → enabled (`google: True`)
- ✅ Google OAuth Client ID/Secret registered (redirect URI above)
- ✅ App redirect URLs allow `http://localhost:3000/auth/callback`
- ✅ Email/password auth enabled (`email: True`)

### 3d. Verification commands

```bash
# Provider status
curl -H "apikey: $SUPABASE_ANON_KEY" https://qazpxjpcvsjbmgbzuxxp.supabase.co/auth/v1/settings
# expect: "google": true

# Authorize step redirects to Google (proves the chain is configured)
curl -sI -H "apikey: $SUPABASE_ANON_KEY" \
  "https://qazpxjpcvsjbmgbzuxxp.supabase.co/auth/v1/authorize?provider=google&redirect_to=http%3A%2F%2Flocalhost%3A3000%2Fauth%2Fcallback"
# expect: HTTP 302 -> accounts.google.com

# Backend accepts the key (bogus token => "Invalid Supabase token", not "not set")
curl -X POST http://localhost:8000/api/auth/supabase -H "Content-Type: application/json" \
  -d '{"access_token":"bogus"}'
```

---

## 4. Test database migrations

The test DB is migrated to Alembic head:

```
alembic_version = b4c5d6e7f8a1
```

Apply/re-run (against the test project, session pooler):

```bash
cd backend
export DATABASE_URL="$(grep '^DIRECT_URL=' .env | cut -d= -f2- | tr -d '\"')"
.venv/bin/alembic upgrade head
```

**Never** run tests against the test project DB — the test suite uses a local
Postgres (`postgres:16` on `127.0.0.1:5433` in the example below; `conftest.py`
defaults to `127.0.0.1:5432` when `DATABASE_URL` is unset) and refuses non-local hosts
(`backend/tests/db_guard.py`, overridable only with `ALLOW_PRODUCTION_TEST_DB=1`).

Test isolation details (`backend/tests/conftest.py`):
- Each run creates an isolated schema (`codecoach_test`, or `codecoach_test_gwN`
  per xdist worker) set via `DATABASE_SEARCH_PATH`, and drops it afterwards.
- Shared auth builders: `backend/tests/fixtures/auth_helpers.py`
  (`register_headers`, `register_user_headers`, `admin_headers`, `aregister_headers`).
- Seed bank: 50 questions (5 hand-written + 45 generated) plus the 107 live ids
  (`backend/tests/fixtures/live_question_ids.json`).

---

## 5. Gotchas / notes

- **Free tier:** API keys and OAuth are available on the free plan — the
  "API" section is now called **"API Keys"** in the dashboard.
- Google OAuth app in **Testing mode** → your Google account must be listed as a
  *test user* (Google Cloud Console → OAuth consent screen → Test users).
- The publishable key is public by design — it is NOT a secret.
- When production is eventually configured: create a *separate* Supabase
  project, rotate `JWT_SECRET_KEY` + `GROQ_API_KEY`, and update every variable
  in this doc for that project. Never copy test credentials to prod.
