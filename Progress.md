# Progress

## Overview

**Status:** Pre-launch (development complete, not yet deployed)
**Commits:** ~65
**Questions:** 10 of 100 target (4 Easy, 6 Medium)
**Starter Code:** Python, JavaScript, Java

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

- 10 hand-authored questions with real-world themes
- Full CRUD via REST API
- Search by title/category/difficulty
- Filter by difficulty, category, company
- Pagination support
- 58KB JSON file-backed storage

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

## 8. Testing

### Backend (pytest)
- 12 test files covering all services, adapters, use cases, middleware
- 85% coverage threshold
- Mocked NVIDIA and Piston services
- Performance/load tests (concurrent requests, memory, locust)

### Frontend (Vitest)
- 20+ test files covering hooks, services, components
- FetchClient HTTP service tests
- Component tests for all UI components

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

## Gaps (Phase 1)

| Area | Missing | Plan |
|---|---|---|
| ~~**Questions**~~ | 90 of 100 ✅ | AI-assisted generation script (`backend/scripts/generate_questions.py`) |
| ~~**Auth**~~ | Google OAuth ✅ | Supabase-based Google OAuth + `/api/auth/supabase` endpoint + login/register pages + AuthProvider + auth-gated actions |
| ~~**Polish**~~ | Empty states, error handling, onboarding ✅ | EmptyState component, Toast system, OnboardingTour, login page with redirect hints, output panel placeholder |
| ~~**Educator materials**~~ | No professor-facing content ✅ | EDUCATORS.md + For Educators page (existing) |
| ~~**Privacy**~~ | No policy page ✅ | `/privacy` route with plain-language policy (existing) |
