# Progress

## Overview

**Status:** Pre-launch (development complete, not yet deployed)
**Commits:** 63+
**Questions:** 36 authored questions in question bank across 14/14 DSA topics
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
- **FIXED (May 29, 2026):** Code wrapping now detects the user's function name dynamically (instead of hardcoding `solve()`) and correctly parses JSON input into native list/int types, preventing string-parsing bugs.
- Local JavaScript execution in browser (bypasses Piston)
- Multi-language support with runtime version detection
- Rate limited: 30 requests/min

## 3. Question Bank

- 36 questions in bank across 14/14 DSA topics
- Automated question generation pipeline scrapped in favor of author-provided questions
- **FIXED (May 28, 2026):** Removed `@lru_cache` causing stale questions, added try/except per question in `FileQuestionRepository._load()`.

## 4. Submit & Grade

- Code submission against visible and hidden test cases
- Pass/fail reporting with detailed output
- **FIXED (May 29, 2026):** Consolidated into single batch `evaluate_suite` call. Fixed syntax errors (`TypeError` on `json.dumps` over generators).

## 5. Question Validation

- 7 validation use cases: structure, test cases, starter code, solution, time limits, function signature, output format
- Orchestrated by `QuestionValidatorService`

## 6. Authentication

- JWT-based registration and login
- Google OAuth via Supabase
- bcrypt password hashing
- File-based user storage

## 7. Frontend Workspace

- Monaco Editor, collapsible sidebar, dark/light theme, resizable panels, AI chat
- **FIXED (May 29, 2026):** Switched build pipeline to `npm` for better dependency reliability. Fixed pre-rendering errors on `/login` using `Suspense` for `useSearchParams`.

## 8. Testing

- **462 backend tests** (356 unit + 106 integration), 50 script, 297 frontend, 19 E2E
- TypeScript clean
- **May 29, 2026:** Fixed 6 suite-runner bugs (in-place functions, multi-param, Signal 6, JS fs, Java json.dumps, stdout=None). Added 62 new tests across 5 files — total coverage: **849 tests**.

## 9. Infrastructure

- Docker Compose with 3 services
- **FIXED (May 29, 2026):** Updated `Dockerfile` to use `node:20-alpine` and `npm` to resolve dependency build issues (`styled-jsx/package.json` missing). Added `.dockerignore` for `node_modules`.

---

## Phase 2 Status

- **Phase 2 Step 10 Complete:** E2E testing passed, TypeScript clean.
- **Next:** Programming language curriculum (C, Python, Java).
