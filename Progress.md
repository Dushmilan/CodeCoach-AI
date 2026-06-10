# Progress — CodeCoach AI

> Last updated: June 7, 2026

## Phase Status

| Phase                           | Status          | Notes                              |
| ------------------------------- | --------------- | ---------------------------------- |
| Phase 1 — DSA Practice          | **In Progress** | 36/100 questions (36%)             |
| Phase 2 — Programming Languages | **Complete**    | 3 courses, 9 modules, 27 lessons   |
| Phase 3 — Future Modules        | **Planned**     | DBMS, OOP, Web Dev, MCQ, Classroom |

## Question Bank

- **Total:** 36 questions across 14 DSA topics
- **Difficulty:** 6 easy, 7 medium, 5 hard (+ 18 initial batch)
- **Generation:** Google Gemini with model fallback (gemini-2.5-flash-lite → gemini-3.1-flash-lite → gemini-3.5-flash)
- **Threshold:** 90 questions (for quality gate)
- **Target:** 100 questions (30 Easy / 50 Medium / 20 Hard)

## Curriculum (Phase 2)

| Course              | Modules | Lessons                          |
| ------------------- | ------- | -------------------------------- |
| Python Fundamentals | 3       | 9                                |
| C Programming       | 3       | 9                                |
| Java Fundamentals   | 3       | 9                                |
| **Total**           | **9**   | **27** (18 theory + 9 exercises) |

- AI coaching: lesson context injected into NIM system prompts
- Content pipeline: `generate_curriculum.py` (NIM) + `verify_curriculum.py` (3-round quality gate)

## Test Counts

| Suite                     | Count                    | Status          |
| ------------------------- | ------------------------ | --------------- |
| Backend unit tests        | 26 test files            | ✅ Passing      |
| Backend integration tests | 10 test files            | ✅ Passing      |
| Backend security tests    | 5 test files             | ✅ Passing      |
| Backend performance tests | 2 test files             | ✅ Passing      |
| Frontend unit tests       | 48 test files            | ✅ Passing      |
| E2E (Playwright)          | 43 tests across 10 specs | Needs fresh run |
| Script tests              | 50 tests                 | ✅ Passing      |

## Infrastructure

- **Backend:** FastAPI + Pydantic v2, Clean Architecture (Ports/Adapters)
- **Frontend:** Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Monaco Editor
- **Database:** Supabase PostgreSQL (via SQLAlchemy async) + file-based fallback
- **Code Execution:** Piston (self-hosted Docker)
- **AI:** NVIDIA NIM (llama-3.1-8b-instruct, mixtral-8x7b) + Google Gemini fallback
- **Auth:** Email/password (bcrypt + JWT) + Supabase OAuth (Google)
- **Rate Limiting:** slowapi (10/min coach, 30/min run/submit)
- **Graphify:** 4162 nodes, 6746 edges, 460 communities

## Recent Fixes (May–June 2026)

- Question loading bugs: removed @lru_cache, added per-item error handling, relaxed Pydantic schemas
- Suite runner bugs: in-place functions, 5-param AI questions, signal 6 crashes, JS fs redeclaration
- Auth: DI consistency, security hardening, SQL infrastructure
- ORM: column sizes, Supabase migration fixes, progress validation

## Known Issues

- 54+ questions still needed to reach 100 target
- E2E tests need fresh run with live stack
- See `Issues.md` for full bug tracker
