# Phase 1 — DSA Practice (Complete)

## Overview

Phase 1 delivers a free, open-source LeetCode alternative with built-in AI coaching. Users practice DSA coding questions with instant hints, reviews, and debugging — no LeetCode Premium or Hackerrank license required.

**Status:** Feature-complete. 13/100 target questions in bank; 87 AI-generated questions pending population via quality gate.

---

## Core Systems Built

### 1. AI Coaching
- NVIDIA NIM (LLaMA 3.1 8B) integration via `integrate.api.nvidia.com/v1`
- Structured JSON responses: hints, reviews, explanations
- Server-Sent Events (SSE) streaming support
- 5 coaching modes: Hint, Review, Explain, Debug, Freeform
- BYO NVIDIA API key via settings modal
- Rate limited: 10 requests/min

### 2. Code Execution
- Piston API integration (self-hosted Docker container)
- Code wrapping for Python, JavaScript, Java — test harness around user functions
- Local JavaScript execution in browser (bypasses Piston)
- Multi-language support with runtime version detection
- Rate limited: 30 requests/min

### 3. Question Bank
- 13 questions in bank (10 hand-authored + 3 AI-generated that passed quality gate)
- AI-assisted generation script (`backend/scripts/generate_questions.py`) across 14 DSA topics via NVIDIA NIM
- **Dual Archetype System**: "Classic Grind" (traditional algorithm puzzles) and "Creative 2026" (real-world scenarios like LLM context windows, drone routing, GPU scheduling)
- **14 2026 Scenario Seeds**: Each DSA topic has a hand-authored real-world framing
- **Auto-Retry on JSON Parse Failure**: Generator retries up to 3 times
- **Strict 20 Test Case Enforcement**: 5 edge + 5 standard + 10 hidden
- **AI Quality Gate** (`backend/scripts/verify_and_populate.py`): 4 independent rounds of AI evaluation against 11 criteria (avg > 90 to populate)
- Full CRUD via REST API, search/filter/pagination, JSON file-backed storage

### 4. Submit & Grade
- Code submission against visible and hidden test cases
- Pass/fail reporting with detailed output
- Performance tracking per submission
- Integration with Piston code execution

### 5. Question Validation
- 7 validation use cases (structure, test cases, starter code, solution, time limits, function signature, output format)
- Single-responsibility classes orchestrated by `QuestionValidatorService`
- Batch and single validation endpoints

### 6. Authentication
- JWT-based registration and login (Access + Refresh tokens)
- Google OAuth via Supabase token validation
- Email/password (bcrypt hashed) + OAuth flows
- File-based user storage
- Frontend `AuthProvider`, `FetchClient`, `AuthGuard`, `useAuthGuard` hook
- `/login`, `/register`, `/auth/callback` pages with redirect-to-origin flow

### 7. Frontend Workspace
- Monaco Editor with Python/JS/Java language selector
- Sidebar with collapsible question list, difficulty filters, random picker
- Question description panel with hints toggle
- AI chat panel with typing indicator, quick action buttons
- Structured response renderer (hints, reviews, explanations)
- Dark/Light theme toggle with persistent storage
- Settings modal for NVIDIA API key
- Resizable editor + output panel
- Navigation controls (prev/next question)
- **OnboardingTour** — 4-step first-visit overlay
- **Toast notification system** with frosted glass design
- **EmptyState component** for empty panels

### 8. Testing
- Backend: 28 pytest test files covering all services, adapters, use cases, middleware
- Frontend: 13 toast notification unit tests
- AI quality gate with 4-round evaluation

---

## Question Pipeline Status

| Step | Count |
|---|---|
| Target question count | 100 |
| Hand-authored in bank | 10 |
| AI-generated passing quality gate | 3 |
| AI-generated pending evaluation | 87 |

**Next action:** Run `verify_and_populate.py` with NVIDIA NIM to auto-evaluate the 87 pending questions and promote qualifying ones. (Deferred to after Phase 2 ships.)

## Phase 2 Migration Note

Phase 2 (programming language curricula) is now live with its own quality-gate pipeline. The `verify_and_populate.py` script for Phase 1 remains unrun — the 87 DSA questions still need evaluation.
