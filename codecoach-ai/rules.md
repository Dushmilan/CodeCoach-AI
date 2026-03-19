# CodeCoach AI — Project Rules & Engineering Standards

> These rules apply to every file, commit, and decision in this project.
> Deviation requires explicit justification in a PR description.

---

## 1. Project Identity

- The project is called **CodeCoach AI**. Never abbreviate to "Coach", "CCAI", or any other alias in code, docs, or UI.
- The sole AI provider is **NVIDIA NIM**. Never introduce Groq, OpenAI, or Anthropic as a dependency — paid or free — without a team decision logged in the SDD.
- The project must remain **100% free to run** during Phases 1 and 2. Any change that introduces a paid dependency, even optionally, must update the cost table in the SDD first.

---

## 2. Repository Structure

```
codecoach-ai/
├── frontend/               # Next.js 14 App Router (Phase 2+)
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── (routes)/
│   ├── components/
│   │   ├── editor/         # CodeEditor, LanguageTabs, OutputBar
│   │   ├── sidebar/        # ProblemSidebar, QuestionCard
│   │   ├── chat/           # AIChatPanel, ChatMessage, TypingIndicator
│   │   └── ui/             # Shared primitives (Button, Badge, Modal)
│   ├── lib/
│   │   ├── nvidia.ts       # NVIDIA NIM client wrapper
│   │   ├── piston.ts       # Piston API client
│   │   └── supabase.ts     # Supabase client
│   └── public/
├── backend/                # FastAPI (Phase 2+)
│   ├── main.py
│   ├── routers/
│   │   ├── coach.py        # /api/coach
│   │   └── run.py          # /api/run
│   ├── questions/          # JSON question files
│   ├── prompts/            # System prompt templates
│   └── tests/
├── coding-coach.html       # Phase 1 single-file MVP
├── rules.md                # This file
├── .env.example
└── README.md
```

### Rules
- Never place business logic in `page.tsx` or route files. All logic lives in `lib/` or `routers/`.
- Component files must match their component name exactly: `AIChatPanel.tsx` not `chat-panel.tsx`.
- One component per file. No barrel exports that re-export more than 10 items.
- All question JSON files live in `backend/questions/`. Never hardcode questions in frontend code.

---

## 3. Naming Conventions

### General
- Use **camelCase** for variables and functions in JS/TS.
- Use **PascalCase** for React components, TypeScript types, and interfaces.
- Use **snake_case** for Python variables, functions, and filenames.
- Use **SCREAMING_SNAKE_CASE** for constants and environment variable names.
- Use **kebab-case** for file names in the frontend (except components).

### Specific
- AI coaching functions must be prefixed: `coach_` in Python, `coach` in TS (e.g., `coachReviewCode`, `coach_build_prompt`).
- API route handlers in FastAPI must end with `_handler` (e.g., `coach_handler`, `run_handler`).
- React components for the AI panel must be in `components/chat/`.
- All Piston-related utilities must live in `lib/piston.ts` — never inline Piston calls in components.

---

## 4. AI Integration Rules (NVIDIA NIM)

These are the most critical rules in this document.

### 4.1 Model Selection
Always use the correct model for the task:

| Task | Model | Max Tokens |
|---|---|---|
| Hints, quick Q&A, explain concept | `meta/llama-3.1-8b-instruct` | 512 |
| Code review, complexity analysis, evaluation | `mistralai/mixtral-8x7b-instruct-v0.1` | 1024 |
| Post-interview full evaluation (Phase 3) | `mistralai/mixtral-8x7b-instruct-v0.1` | 2048 |

**Never** use the heavy model for quick hints — latency matters.

### 4.2 API Usage
- **Always call NVIDIA NIM from the backend** (Phase 2+). Never expose `NVIDIA_API_KEY` to the browser.
- The only allowed direct browser → NVIDIA NIM call is in **Phase 1 (single HTML file)**, where the user supplies their own key.
- Always set `stream: true` for coaching responses. Blocking responses are not acceptable for UX.
- Always set an explicit `max_tokens` limit. Never leave it unset.
- Always include a `temperature` value. Default: `0.7` for coaching, `0.3` for code review.

### 4.3 Prompt Rules
- All system prompts must live in `backend/prompts/` as `.txt` files — never hardcoded inline in route handlers.
- Every prompt must include: (1) role definition, (2) problem context, (3) user's current code, (4) task instruction.
- Prompts must explicitly instruct the model to **not give away the full solution** unless the user has attempted the problem and explicitly asks.
- Responses must be kept concise: instruct the model to respond in under 150 words for hints, under 250 words for reviews.
- Always sanitise user code before injecting it into a prompt — strip null bytes and limit to 5000 characters.

### 4.4 Error Handling
- If NVIDIA NIM returns a 429 (rate limit), surface a user-friendly message: *"The AI coach is busy — try again in a few seconds."* Never show raw API errors to the user.
- If NVIDIA NIM returns a 5xx, retry once after 3 seconds, then surface the error.
- All AI calls must have a **15-second timeout**. Never let the UI hang indefinitely.

---

## 5. Code Execution Rules (Piston API)

- **Never** use `eval()` for Python or Java execution in production. `eval()` is only acceptable in Phase 1 for JavaScript in-browser demo purposes.
- Always validate the `language` field against an allowlist before forwarding to Piston:
  ```python
  ALLOWED_LANGUAGES = {"python", "javascript", "java"}
  ```
- Always enforce a **10-second execution timeout** on the Piston request.
- Never return raw Piston error payloads to the frontend. Normalise all responses to `{ stdout, stderr, exit_code }`.
- Limit code input to **10,000 characters** maximum. Reject and return a 400 error if exceeded.
- Log every code execution request with: `language`, `question_id`, `exit_code`, `duration_ms`. Never log the code itself (privacy).

---

## 6. Frontend Rules

### 6.1 React & TypeScript
- **No `any` types.** Use `unknown` and narrow, or define a proper interface.
- All components must be typed with explicit prop interfaces. No inline type definitions for props.
- Use `const` by default. Only use `let` when reassignment is truly necessary.
- No class components. All components must be functional.
- Never use `useEffect` to fetch data. Use React Query or SWR.
- All async operations in components must handle loading and error states explicitly.

### 6.2 Editor (Monaco)
- The Monaco Editor instance must never be accessed directly from outside `components/editor/CodeEditor.tsx`.
- Language switching must preserve the user's code per language per question in local state.
- The editor must be read-only during code execution (while awaiting Piston response).

### 6.3 Chat Panel
- AI responses must be streamed token-by-token. Never buffer the full response and show it all at once.
- The typing indicator must appear within **200ms** of sending a request.
- Chat history must be capped at **50 messages** in state. Older messages are trimmed from the top.
- Never allow sending an empty message. Disable the send button and ignore Enter keypress when input is blank.

### 6.4 Styling
- Use CSS variables for all colours. No hardcoded hex values outside of `:root` declarations.
- Dark theme is the default and required. Light theme is optional (Phase 2).
- No inline `style` props except for dynamic values that cannot be expressed with class names.
- All interactive elements must have `:focus-visible` styles for keyboard accessibility.
- Minimum tap target size: 44×44px on all clickable elements.

---

## 7. Backend Rules (FastAPI)

### 7.1 Structure
- All route logic must live in `routers/`. `main.py` only registers routers and middleware.
- Use Pydantic models for all request bodies and responses. Never use raw `dict` for API I/O.
- All database queries must go through a service layer. Routers must not query Supabase directly.

### 7.2 Security
- Rate limit `/api/coach` to **10 requests per minute per IP** using `slowapi`.
- Rate limit `/api/run` to **20 requests per minute per IP**.
- Validate and sanitise all inputs server-side, even if the frontend already validates.
- Never log request bodies in production. Log only: route, status code, duration, IP hash.
- All environment variables must be loaded via `pydantic-settings`. Never use `os.environ.get()` directly.

### 7.3 Responses
- All API responses must follow a consistent envelope:
  ```json
  { "success": true, "data": { ... } }
  { "success": false, "error": "Human-readable message" }
  ```
- HTTP status codes must be semantically correct: 200 for success, 400 for bad input, 429 for rate limit, 500 for server error.
- Never return a 200 with an error message in the body.

---

## 8. Question Bank Rules

- Every question must have all required fields. No field may be null or empty:
  - `id`, `title`, `difficulty`, `category`, `description`
  - `starter.python`, `starter.javascript`, `starter.java`
  - `hints` (minimum 2 hints per question)
  - `time_complexity`, `space_complexity`
  - `test_cases` (minimum 3 test cases per question)

- `difficulty` must be exactly one of: `"easy"`, `"medium"`, `"hard"`. No other values.
- `id` must be kebab-case and globally unique (e.g., `"two-sum"`, `"longest-substring"`).
- Starter code must be syntactically valid for all three languages. Validate before committing.
- Test cases must include at least one edge case (empty input, single element, negative numbers, etc.).
- Never include the solution in the starter code. The starter must only contain the function signature and a `pass` / placeholder body.

---

## 9. Environment Variables

All required environment variables must be documented in `.env.example` with placeholder values and a comment explaining each one. A missing or empty required variable must cause the app to **fail fast at startup** — never silently default.

```bash
# NVIDIA NIM — get free key at build.nvidia.com
NVIDIA_API_KEY=nvapi-xxxxxxxxxxxxxxxxxxxx

# Supabase — free at supabase.com
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...   # backend only, never expose to browser

# App config
ALLOWED_ORIGIN=https://your-app.vercel.app
ENVIRONMENT=development                 # development | production
```

**Rules:**
- `SUPABASE_SERVICE_ROLE_KEY` must **never** appear in frontend code or be committed to git.
- `NVIDIA_API_KEY` must **never** appear in frontend code (Phase 2+).
- Never commit a `.env` file. Only `.env.example` is committed.
- Rotate `NVIDIA_API_KEY` immediately if accidentally exposed.

---

## 10. Git & Version Control

### Branching
- `main` — production-ready code only. Protected. Requires PR + review.
- `dev` — integration branch. All feature branches merge here first.
- `feature/<short-description>` — feature work (e.g., `feature/mock-interview-timer`)
- `fix/<short-description>` — bug fixes (e.g., `fix/chat-scroll-bug`)
- `chore/<short-description>` — non-functional changes (e.g., `chore/update-deps`)

### Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/):
```
feat: add NVIDIA NIM streaming to chat panel
fix: handle Piston timeout gracefully in output bar
chore: update question bank with 10 new medium problems
docs: update SDD phase 2 checklist
refactor: extract prompt builder into separate module
test: add unit tests for coach router
```

- Subject line: max 72 characters, imperative mood, no period at end.
- Never commit directly to `main` or `dev`.
- Never commit commented-out code. Delete it.
- Never commit `console.log` or `print()` debug statements in production code.

### Pull Requests
- Every PR must reference an issue or task.
- Every PR must include a brief description of what changed and why.
- PRs touching `/api/coach` or NVIDIA NIM integration require extra scrutiny — note this in the PR description.
- PRs must not mix feature work and refactoring. Keep them separate.

---

## 11. Testing Standards

### Frontend
- Every utility function in `lib/` must have unit tests.
- Critical UI flows (sending a message, running code, switching questions) must have integration tests.
- Use Vitest for unit tests, Playwright for end-to-end.
- Minimum coverage target: **70%** for `lib/` files.

### Backend
- Every FastAPI route must have at least: one happy-path test, one invalid input test, one rate limit test.
- Mock NVIDIA NIM and Piston in all tests — never call real external APIs in tests.
- Use `pytest` with `httpx.AsyncClient` for route testing.
- Minimum coverage target: **80%** for `routers/` files.

### Question Bank
- A validation script (`scripts/validate_questions.py`) must be run in CI on every PR that touches `backend/questions/`.
- The script must check: required fields, valid difficulty values, unique IDs, valid starter code syntax.

---

## 12. Performance Standards

- **AI first token latency:** Must appear within **3 seconds** of sending a message (NVIDIA NIM streaming).
- **Code execution round-trip:** Must complete within **12 seconds** (10s Piston timeout + 2s overhead).
- **Page load (Vercel):** Lighthouse performance score must stay above **85**.
- **Bundle size:** Frontend JS bundle must stay under **500KB** gzipped. Monitor with `next build` output.
- **Monaco Editor:** Must load lazily — never block initial page render.

---

## 13. Accessibility Standards

- All interactive elements must be keyboard-navigable.
- All images and icons must have descriptive `alt` text or `aria-label`.
- Colour contrast ratio must meet WCAG AA: minimum 4.5:1 for normal text, 3:1 for large text.
- The code editor must announce execution results to screen readers via `aria-live`.
- Do not rely on colour alone to convey information (e.g., difficulty badges must have text labels, not just colour).

---

## 14. Documentation Rules

- Every new component must have a JSDoc comment describing its purpose and key props.
- Every new FastAPI route must have a docstring and a Pydantic model with field descriptions.
- The SDD in Notion must be updated whenever: a new technology is added, a phase checklist item is completed, or the architecture changes.
- `README.md` must always reflect the current Phase and have up-to-date setup instructions.
- This `rules.md` must be reviewed and updated at the start of every new Phase.

---

## 15. What Never to Do

| ❌ Never | ✅ Instead |
|---|---|
| Hardcode API keys in source code | Use environment variables |
| Call NVIDIA NIM from the browser (Phase 2+) | Proxy through FastAPI backend |
| Show raw API errors to users | Show friendly, actionable error messages |
| Use `any` type in TypeScript | Use proper types or `unknown` |
| Commit `.env` files | Only commit `.env.example` |
| Inline questions in frontend code | Load from `/api/questions` |
| Block on AI response (no streaming) | Always stream NVIDIA NIM responses |
| Run user code without a timeout | Always enforce 10s Piston timeout |
| Use `eval()` for non-JS languages | Use Piston API |
| Push directly to `main` | Always use a PR |
| Log user code server-side | Only log metadata (language, duration) |
| Leave unused `console.log` in code | Delete before committing |

---

*Last updated: March 2026 — Version 1.0.0*
*Owner: Dushmilan | Aligned with SDD v1.2.0*
