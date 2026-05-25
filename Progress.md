# Progress

## Overview

**Status:** Pre-launch (development complete, not yet deployed)
**Commits:** 61+
**Questions:** 13 in question bank (10 hand-authored + 3 AI-verified) of 100 target; 87 AI-generated questions in review
**Starter Code:** Python, JavaScript, Java
**AI Quality Gate:** 4-round verification against 9 criteria (min avg > 90) before populating new questions

---

## 1. AI Coaching

- NVIDIA NIM (LLaMA 3.1 8B) integration via `integrate.api.nvidia.com/v1`
- Structured JSON responses: hints, reviews, explanations
- Server-Sent Events (SSE) streaming support
- 5 coaching modes: Hint, Review, Explain, Debug, Freeform
- BYO NVIDIA API key via settings modal
- Rate limited: 10 requests/min

## 2. Code Execution

- Piston API integration (self-hosted Docker container)
- Code wrapping for Python, JavaScript, Java — adds test harness around user functions
- Local JavaScript execution in browser (bypasses Piston)
- Multi-language support with runtime version detection
- Rate limited: 30 requests/min

## 3. Question Bank

- 13 questions in bank (10 hand-authored + 3 AI-generated that passed quality gate)
- AI-assisted generation script (`backend/scripts/generate_questions.py`) produces questions across 14 DSA topics via NVIDIA NIM
- **Dual Archetype System**: Two prompt archetypes — "Classic Grind" (traditional algorithm puzzles) and "Creative 2026" (real-world scenarios like LLM context windows, drone routing, GPU scheduling, smart grid DP, CRDT reconciliation)
- **14 2026 Scenario Seeds**: Each DSA topic has a hand-authored real-world framing (e.g., Sliding Window → LLM token budget optimization, Graphs → drone no-fly zone routing, Heap → GPU cluster job scheduling)
- **Auto-Retry on JSON Parse Failure**: Generator retries up to 3 times, feeding the JSON error back to the LLM so it self-corrects
- **Strict 20 Test Case Enforcement**: Generator prompt demands exactly 20 test cases (5 edge + 5 standard + 10 hidden); parser warns if fewer are produced
- **AI Quality Gate** (`backend/scripts/verify_and_populate.py`): 4 independent rounds of AI evaluation against **11 criteria** — topic relevance, difficulty match, correctness, clarity, starter code quality, test case quality, solution correctness, edge cases, test_case_coverage (≥20 test cases required), **thematic_coherence** (scenario logic/accuracy check), **boundary_edge_cases** (max-constraint stress testing)
- Questions populate bank only if average score > 90 across all 4 rounds; rejected questions saved to `rejected_questions.json` for review
- `--export-prompts` mode exports all questions as self-contained evaluation prompts for manual AI eval; `--import-scores` mode ingests scored results
- `--archetype` CLI flag supports `classic`, `creative_2026`, or `mixed` (default: mixed, 50/50 split per topic/difficulty)
- **Evaluation using NVIDIA API key** — pending: run `verify_and_populate.py` with NVIDIA NIM to auto-evaluate the 87 rejected questions and promote qualifying ones
- Full CRUD via REST API
- Search by title/category/difficulty
- Filter by difficulty, category, company
- Pagination support
- JSON file-backed storage

## 4. Submit & Grade

- Code submission against visible and hidden test cases
- Pass/fail reporting with detailed output
- Performance tracking per submission
- Integration with Piston code execution

## 5. Question Validation

- 7 validation use cases: structure, test cases, starter code, solution, time limits, function signature, output format
- Each use case is a single-responsibility class
- Orchestrated by `QuestionValidatorService`
- Batch and single validation endpoints

## 6. Authentication

- JWT-based registration and login (Access + Refresh tokens)
- **Google OAuth via Supabase** — `/api/auth/supabase` backend endpoint validates Supabase tokens and auto-creates local users on first login
- `UserInDB` extended with `oauth_provider`/`oauth_id` fields
- `UserRepository.get_by_oauth()` for OAuth-based lookups
- Frontend `AuthProvider` with React context, localStorage token persistence, `useAuth()` hook
- `FetchClient` auto-injects `Authorization: Bearer` from localStorage
- `AuthGuard` component + `useAuthGuard` hook gates Run/Submit/AI Coach actions behind login
- `/login` and `/register` pages with redirect-to-origin flow
- `/auth/callback` page for Supabase OAuth redirect handling
- Header is auth-aware: shows "Sign in" when logged out, username + "Logout" when logged in
- bcrypt password hashing
- File-based user storage
- `get_current_user` FastAPI dependency with HTTPBearer
- Rate limited: 20 requests/min

## 7. Frontend Workspace

- Monaco Editor (`@monaco-editor/react`) with Python/JS/Java language selector
- Sidebar with collapsible question list, difficulty filters, random picker
- Question description panel with hints toggle
- Code editor with Run / Submit / Reset controls
- AI chat panel with typing indicator, quick action buttons
- Structured response renderer (hints, reviews, explanations)
- Dark/Light theme toggle with persistent storage
- Settings modal for NVIDIA API key
- Resizable editor + output panel
- Navigation controls (prev/next question)
- **OnboardingTour** — 4-step first-visit overlay (Welcome, Question Browser, AI Coach, API Key)
- **Toast notification system** — `ToastProvider` + `showToast()` imperative API for success/error/info messages
- **EmptyState component** — used in MessageList and CodeEditorContainer output panel
- **AuthGuard** — public workspace is browsable; Run/Submit/AI Coach redirect to `/login` if unauthenticated

## 8. Testing

### Backend (pytest)
- 28 test files covering all services, adapters, use cases, middleware
- 85% coverage threshold
- Mocked NVIDIA and Piston services
- Performance/load tests (concurrent requests, memory, locust)
- 288 tests passing (274 unit + 14 script tests)
- Auth: 4 supabase login tests (creates new user, returns existing, invalid token, no config)
- Question generation: 10 tests (slugify, prompt building, JSON parsing, topic extraction)
- AI Verification Script: 48 tests (prompt building, response parsing, scoring, filtering, merging, export, import, archetype detection, thematic coherence, boundary edge cases, auto-retry logic)

### Frontend (Vitest)
- 29 test files covering hooks, services, components
- 284 tests passing (29 test suites)
- Auth service: 6 tests (login, register, loginWithSupabase, getMe)
- AuthProvider: 6 tests (initial state, login, register, logout, loginWithSupabase, token persistence)
- Other: FetchClient HTTP service tests, component tests for all UI components
- TypeScript: `tsc --noEmit` passes clean

### E2E (Playwright)
- Homepage smoke test
- User flow test (question selection → code execution → AI coaching)

## 9. Infrastructure

- Docker Compose with 3 services: backend (FastAPI, port 8000), frontend (Next.js, port 3000), piston (port 2000)
- Backend Dockerfile (Python 3.11-alpine)
- Health check and detailed diagnostics endpoints
- Debug endpoints for environment and API key status
- Pre-commit hooks configured
- Issue templates (bug report, feature request)

---

## Phase 1 Status

**All Phase 1 gaps are addressed.** Every item is backed by implementation, tests, or existing content.

| Area | Status | Details |
|---|---|---|
| Questions | ✅ Ready | 13 in bank (10 hand-authored + 3 AI-verified). 87 more AI-generated awaiting evaluation via NVIDIA API key |
| Auth | ✅ Complete | JWT email/password + Google OAuth via Supabase with full frontend integration |
| UX Polish | ✅ Complete | EmptyState, Toast, OnboardingTour, auth-aware header, output panel placeholder |
| Educator materials | ✅ Existing | EDUCATORS.md + For Educators page |
| Privacy | ✅ Existing | `/privacy` route with plain-language policy |

---

## Immediate Next Step — AI Evaluation of Pending Questions

- Run `verify_and_populate.py` with NVIDIA API key to auto-evaluate 87 rejected questions across 4 rounds
- Promote any that pass > 90 threshold to the question bank
- Target: close to 100 questions before starting Phase 2

## What's Next (Phase 2 — Programming Language Curricula)

- C, Python, Java — each with ~15-20 interleaved theory + coding exercise lessons
- Context-aware AI coaching per lesson
- `/learn` navigation
- Future: DBMS/SQL, OOP & Design Patterns, Web Dev, Theory/MCQ question type, classroom dashboard
