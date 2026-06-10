# Issues — CodeCoach AI

> Last updated: June 7, 2026

## Open Issues

| ID  | Severity | Status | Description                                                                       | File(s)                                                       |
| --- | -------- | ------ | --------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| I6  | High     | Open   | Rate limiting not wired to any endpoint — decorator never applied                 | `backend/app/middleware/rate_limit.py`, `backend/app/main.py` |
| I7  | High     | Open   | RateLimitMiddleware creates new instance per request — no state persistence       | `backend/app/middleware/rate_limit.py:120`                    |
| I8  | High     | Open   | Supabase OAuth callback crashes — env vars undefined, `!` assertions throw        | `frontend/src/app/auth/callback/page.tsx`                     |
| I9  | Medium   | Open   | Leaked NVIDIA API key in `.env.example` (version controlled)                      | `backend/.env.example` (now fixed)                            |
| I10 | Medium   | Open   | FileUserRepository.\_load() has no try/except — one bad entry crashes all lookups | `backend/app/repositories/file_user_repository.py`            |
| I11 | Medium   | Open   | Dev docker-compose missing JWT_SECRET_KEY — insecure fallback always active       | `docker-compose.dev.yml`                                      |
| I12 | Low      | Open   | Health endpoint reports rate_limiting: enabled when it's not                      | `backend/app/api/health.py`                                   |
| I13 | Low      | Open   | CORS origins hardcoded instead of env-driven                                      | `backend/app/main.py`                                         |
| I14 | Low      | Open   | Hardcoded JWT fallback secret when JWT_SECRET_KEY unset                           | `backend/app/services/auth_service.py`                        |

## Resolved Issues

| ID  | Severity | Description                                                                               | Fix                                                                          |
| --- | -------- | ----------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| I1  | High     | `@lru_cache()` on questions API cached stale data — never re-read from disk               | Removed `@lru_cache()` from `get_questions_service()`                        |
| I2  | High     | No try/except in `FileQuestionRepository._load()` — one malformed question crashed all 18 | Added per-item try/except, skip malformed, log errors                        |
| I3  | Medium   | Pydantic schemas too strict for NIM generator output (dict values where strings expected) | Made schemas accept `Union[str, Dict, List, int, None]` with auto-conversion |
| I4  | Medium   | HTTPException swallowed by generic error handler — 400 returned as 500                    | Fixed error handler ordering                                                 |
| I5  | Low      | Test asserting non-existent company names                                                 | Fixed test assertion                                                         |
| I15 | High     | Suite runner: in-place functions (rotate-image, next-permutation) return None             | Runner serializes input_value when function returns None                     |
| I16 | High     | Suite runner: 5-param AI question — JSON dict fed but function expects 5 positional args  | Convert inputs to `\n`-separated format, spread args                         |
| I17 | High     | Suite runner: `_parse_suite_output` ignored `exec_result.signal` — SIGABRT silenced       | Added signal_info to error paths                                             |
| I18 | High     | JS `fs` redeclaration — both runner template and wrapper add `const fs = require('fs')`   | Removed from runner template, added process.stdout.write bypass              |
| I19 | Medium   | Java `json.dumps` bare generator — not serializable                                       | Changed to list comprehension                                                |
| I20 | Medium   | `stdout=None` guard missing in piston service                                             | Added guard for None stdout                                                  |
