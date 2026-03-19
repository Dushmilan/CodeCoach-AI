# 📐 Software Design Document — CodeCoach AI

# Software Design Document

## CodeCoach AI — Interview Practice Platform

> **Version:** 1.2.0 | **Date:** March 2026 | **Status:** 🟢 Active | **Updated:** NVIDIA NIM as sole AI provider
> 

---

# 1. Overview

## 1.1 Purpose

This document describes the software architecture, component design, data flow, and technology decisions for **CodeCoach AI** — an AI-powered coding interview practice platform. It is intended for developers building, extending, or maintaining the project.

## 1.2 Project Summary

CodeCoach AI lets users practice coding interview problems with real-time AI coaching. Users write code in a browser-based editor, run it, and interact with an LLM-powered coach that provides hints, complexity analysis, code review, and explanations — all in a conversational interface.

## 1.3 Goals

- Provide a distraction-free, IDE-like coding environment in the browser
- Deliver real-time AI coaching via the **NVIDIA NIM free API** (zero cost)
- Support multiple programming languages (Python, JavaScript, Java)
- Keep infrastructure costs at **$0/month** using free tiers only
- Be deployable as a single HTML file or a full-stack web app

---

# 2. Tech Stack

## 2.1 Frontend

| Layer | Technology | Tier |
| --- | --- | --- |
| UI Framework | Vanilla HTML/CSS/JS (Phase 1), Next.js/React (Phase 2) | Free |
| Code Editor | Monaco Editor (browser) or CodeMirror | Free |
| Fonts | Google Fonts (JetBrains Mono, Syne) | Free |
| Hosting | Vercel | Free tier |
| Styling | Custom CSS / Tailwind CSS | Free |

## 2.2 Backend

| Layer | Technology | Tier |
| --- | --- | --- |
| API Server | FastAPI (Python) | Free (self-hosted) |
| Code Execution | Piston API ([emkc.org](http://emkc.org), public instance) | Free |
| Auth | Supabase Auth | Free tier (50k MAU) |
| Database | Supabase PostgreSQL | Free tier (500MB) |
| Backend Hosting | Render | Free tier (750 hrs/mo) |

## 2.3 AI Layer

| Provider | Model | Role | Cost |
| --- | --- | --- | --- |
| **NVIDIA NIM** | `meta/llama-3.1-8b-instruct` | Primary AI coach | **$0 (Free)** |
| **NVIDIA NIM** | `mistralai/mixtral-8x7b-instruct-v0.1` | Complex reasoning tasks | **$0 (Free)** |

> ✅ **NVIDIA NIM is the sole AI provider.** All AI coaching is powered exclusively by NVIDIA's free hosted NIM API, running on DGX Cloud. Free NVIDIA Developer Program members get unlimited prototyping access — no credit card required.
> 

> 🔑 **How to get your free NVIDIA API key:** Sign up at [build.nvidia.com](http://build.nvidia.com) → pick any model → click **"Get API Key"** → join the free NVIDIA Developer Program.
> 

---

# 3. System Architecture

## 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                      Browser                        │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Problem  │  │ Code Editor  │  │  AI Chat     │  │
│  │ Sidebar  │  │ (Monaco)     │  │  Panel       │  │
│  └──────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────┬───────────────────────────────┘
                      │ HTTPS
         ┌────────────┴────────────┐
         │                         │
  ┌──────▼──────┐        ┌─────────▼──────────────────┐
  │  FastAPI    │        │      NVIDIA NIM  (FREE)     │
  │  Backend    │───────▶│  meta/llama-3.1-8b-instruct │
  │  (Render)   │        │  mistralai/mixtral-8x7b     │
  └──────┬──────┘        └────────────────────────────┘
         │
  ┌──────▼──────┐
  │ Piston API  │
  │ (Code Exec) │
  └─────────────┘
         │
  ┌──────▼──────┐
  │  Supabase   │
  │  (DB+Auth)  │
  └─────────────┘
```

### AI Request Flow (NVIDIA NIM)

```
User sends message or clicks "AI Review"
  → Frontend calls FastAPI POST /api/coach
  → FastAPI builds prompt:
      system: "You are an expert coding interview coach..."
      context: problem title + language + user's current code
      user: message
  → POST https://integrate.api.nvidia.com/v1/chat/completions
      model: "meta/llama-3.1-8b-instruct"
      max_tokens: 512
      stream: true
  → NVIDIA NIM returns GPU-accelerated streamed tokens (~200ms avg)
  → FastAPI pipes SSE stream back to browser
  → Chat panel renders tokens in real time
  → If 429 rate limit hit → switch to mixtral-8x7b for that request
```

## 3.2 Phase 1 — Single File (Current)

In Phase 1, the entire app runs as a single `coding-coach.html` file. The browser calls the NVIDIA NIM API directly using the user's personal API key stored in JS memory (never persisted).

**Pros:** Zero infrastructure, instant deploy, zero cost

**Cons:** API key visible in browser memory, no Python execution, no persistence

## 3.3 Phase 2 — Full Stack

In Phase 2, a FastAPI backend is added to securely proxy NVIDIA NIM API calls server-side and run user code via Piston.

---

# 4. Component Design

## 4.1 Frontend Components

### Problem Sidebar

- Renders the list of available questions
- Each question card shows title, difficulty badge (Easy/Medium/Hard), and category tag
- Active question highlighted with a green left border
- On click: loads question into editor and updates problem description

### Code Editor

- Multi-language support: Python, JavaScript, Java
- Language tabs switch the active language and load starter code
- **Run Code** button executes JavaScript inline (Phase 1) or calls backend (Phase 2)
- Output bar shows execution results or errors

### AI Chat Panel

- Displays conversation history between user and NVIDIA NIM coach
- Quick-action chips: Hint, Complexity, Optimal, Explain, Edge Cases
- Text input with `Enter` to send, `Shift+Enter` for newline
- Typing indicator shown while awaiting NIM response
- Animated fade-in per message

### API Key Modal

- Shown on first load (Phase 1 only)
- User pastes their free NVIDIA NIM API key from [build.nvidia.com](http://build.nvidia.com)
- Key stored in JS memory only (never in localStorage or cookies)

## 4.2 AI Coaching System

### Prompt Strategy

Every message to NVIDIA NIM includes:

1. **System context** — expert coding coach persona
2. **Problem context** — current problem title and language
3. **User's code** — full editor contents
4. **User's message** — what they asked

### Model Selection Strategy

| Task | Model Used | Reason |
| --- | --- | --- |
| Hints, explanations, edge cases | `meta/llama-3.1-8b-instruct` | Fast, low-latency responses |
| Code review, complexity analysis | `mistralai/mixtral-8x7b-instruct-v0.1` | Better reasoning for evaluation |
| Rate limit fallback | `mistralai/mixtral-8x7b-instruct-v0.1` | Alternative NIM endpoint |

### Coaching Modes

| Mode | Trigger | Behavior |
| --- | --- | --- |
| Hint | Hint chip | Give a directional nudge without the full answer |
| Code Review | AI Review button | Evaluate correctness, complexity, and style |
| Complexity | Complexity chip | Explain Big-O time and space complexity |
| Explanation | Explain chip | Teach the concept from scratch |
| Edge Cases | Edge Cases chip | List edge cases and gotchas |
| Freeform | User types anything | General coaching response |

---

# 5. Data Flow

## 5.1 Code Review Flow

```
User clicks "AI Review"
  → Capture editor content
  → Build prompt: problem + code + review instruction
  → POST /api/coach (FastAPI)
  → FastAPI → NVIDIA NIM (mistralai/mixtral-8x7b-instruct-v0.1)
  → Show typing indicator
  → Stream tokens back via SSE
  → Render in chat panel
```

## 5.2 Code Execution Flow

```
User clicks "Run Code"
  → Send {code, language, version} to POST /api/run
  → FastAPI → Piston API (emkc.org/api/v2/piston/execute)
  → Piston runs code in sandboxed container
  → Returns {stdout, stderr, exit_code}
  → Display in output bar
```

---

# 6. API Design (Phase 2)

## 6.1 Endpoints

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/run` | Execute code via Piston |
| POST | `/api/coach` | Proxy AI coaching request to NVIDIA NIM |
| GET | `/api/questions` | List all questions |
| GET | `/api/questions/:id` | Get question details |

## 6.2 POST /api/coach

**Request**

```json
{
  "problem": "Two Sum",
  "language": "python",
  "code": "def two_sum(nums, target): ...",
  "message": "What is the time complexity?",
  "mode": "complexity"
}
```

**Model Routing Logic**

```python
# Use Mixtral for review/complexity, Llama for everything else
HEAVY_MODES = {"review", "complexity"}
model = (
    "mistralai/mixtral-8x7b-instruct-v0.1"
    if request.mode in HEAVY_MODES
    else "meta/llama-3.1-8b-instruct"
)

response = await nvidia_nim_client.chat.completions.create(
    model=model,
    messages=messages,
    max_tokens=512,
    stream=True,
    base_url="https://integrate.api.nvidia.com/v1"
)
```

**Response** — Server-Sent Events stream of NVIDIA NIM tokens.

## 6.3 POST /api/run

**Request**

```json
{
  "language": "python",
  "code": "print('hello')",
  "version": "3.10"
}
```

**Response**

```json
{
  "stdout": "hello\n",
  "stderr": "",
  "exit_code": 0
}
```

---

# 7. Question Schema

```json
{
  "id": "two-sum",
  "title": "Two Sum",
  "difficulty": "easy",
  "category": "Arrays",
  "company_tags": ["Google", "Amazon", "Meta"],
  "description": "Given an array...",
  "starter": {
    "python": "def two_sum(nums, target):\n    pass",
    "javascript": "function twoSum(nums, target) {}",
    "java": "class Solution { ... }"
  },
  "examples": [
    { "input": "[2,7,11,15], target=9", "output": "[0,1]" }
  ],
  "test_cases": [
    { "input": [[2,7,11,15], 9], "expected": [0,1] }
  ],
  "hints": ["Try using a hash map", "Store complements as keys"],
  "solution": "...",
  "time_complexity": "O(n)",
  "space_complexity": "O(n)"
}
```

---

# 8. Infrastructure & Cost Plan

## 8.1 Free Tier Summary

| Service | What It's Used For | Free Limit | Cost |
| --- | --- | --- | --- |
| Vercel | Frontend hosting | 100GB bandwidth/mo | $0 |
| Render | FastAPI backend | 750 hrs/mo | $0 |
| Supabase | Auth + DB | 500MB, 50k MAU | $0 |
| Piston API | Code execution | Public free instance | $0 |
| NVIDIA NIM API | AI coaching (primary + fallback) | Unlimited prototyping on DGX Cloud | **$0** |
| **Total** |  |  | **$0/mo** |

> ✅ 100% free. NVIDIA NIM is the **sole AI provider**. No other AI APIs are used.
> 

## 8.2 Scale Triggers

Upgrade only when:

- **Render** — backend runs >750 hrs/mo → paid plan ($7/mo)
- **Supabase** — DB exceeds 500MB or >50k users
- **NVIDIA NIM** — prototyping limits are hit → register for NVIDIA AI Enterprise (free 90-day trial for higher throughput)

---

# 9. Development Roadmap

## Phase 1 — MVP ✅ (Complete)

**Goal:** Prove the concept as a single, zero-infrastructure HTML file.

### UI & Editor

- [x]  Single `coding-coach.html` — no build step, no server required
- [x]  3-column layout: Problem Sidebar / Code Editor / AI Chat Panel
- [x]  Dark IDE-style theme with animated grid background and glow orbs
- [x]  Language tabs: Python, JavaScript, Java with per-language starter code
- [x]  6 curated problems with difficulty badges and category tags
- [x]  Active question highlighting with animated left border

### AI Integration

- [x]  NVIDIA NIM API integration with `meta/llama-3.1-8b-instruct` (free tier)
- [x]  API key modal — NVIDIA NIM key stored in JS memory only, never persisted
- [x]  AI Review button — sends full problem + code context to NIM
- [x]  Freeform chat interface with the AI coach
- [x]  Quick-action chips: Hint, Complexity, Optimal, Explain, Edge Cases
- [x]  Animated typing indicator while awaiting NIM response
- [x]  Message fade-in animation per response

### Code Execution

- [x]  Inline JavaScript execution via `eval()` in browser
- [x]  `console.log` override for stdout capture
- [x]  Output bar showing results or runtime errors

---

## Phase 2 — Full Stack 🔧 (In Progress)

**Goal:** Add a backend for secure AI proxying, real multi-language code execution, and user accounts.

### 2.1 Project Setup & Infrastructure

- [x]  Initialise monorepo: `/frontend` (Next.js) and `/backend` (FastAPI)
- [x]  Configure Vercel for auto-deploy on push to `main`
- [x]  Deploy FastAPI to Render free tier (`uvicorn main:app --host 0.0.0.0 --port $PORT`)
- [x]  Configure environment variables: `NVIDIA_API_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`
- [x]  Add CORS middleware to FastAPI allowing Vercel domain
- [x]  Set up GitHub repo with branch protection rules on `main`
- [x]  Add `Dockerfile` for local development parity

### 2.2 Frontend Migration (Next.js + React)

- [x]  Scaffold Next.js 14 app with App Router and TypeScript
- [x]  Migrate layout to React components:
    - [x]  `<ProblemSidebar />` — question list with difficulty/category filters
    - [x]  `<CodeEditor />` — Monaco Editor via `@monaco-editor/react`
    - [x]  `<AIChatPanel />` — messages, typing indicator, quick chips, SSE streaming
    - [x]  `<OutputBar />` — execution result with status colour coding
    - [x]  `<Header />` — nav, mode switcher, user avatar dropdown
    - [x]  `<APIKeyModal />` — NVIDIA NIM key entry for Phase 1 compat
- [x]  Add Tailwind CSS with custom dark theme config
- [x]  Implement dark/light mode toggle with `next-themes`
- [ ]  Make layout responsive: collapsible sidebar on tablet, stacked on mobile

### 2.3 Backend API (FastAPI)

- [ ]  `POST /api/coach` — proxy NVIDIA NIM API call server-side
    - [ ]  Validate request body (problem, code, message, language, mode)
    - [ ]  Route to correct NIM model based on `mode` (llama for hints, mixtral for review)
    - [ ]  Build structured system prompt with coaching persona
    - [ ]  Stream NIM response tokens back via Server-Sent Events
    - [ ]  Handle 429 rate limit: switch to alternate NIM model for that request
    - [ ]  Log request count and model used per session for monitoring
- [ ]  `POST /api/run` — execute code via Piston API
    - [ ]  Map language string to Piston runtime + version
    - [ ]  POST to `https://emkc.org/api/v2/piston/execute`
    - [ ]  Return `stdout`, `stderr`, `exit_code` to frontend
    - [ ]  Enforce 10-second execution timeout
    - [ ]  Sanitise code input (reject obvious infinite loops heuristically)
- [ ]  `GET /api/questions` — return question bank as paginated JSON
- [ ]  `GET /api/questions/:id` — single question with hints, test cases, solution
- [ ]  Add IP-based rate limiting using `slowapi` (10 req/min per IP on `/api/coach`)
- [ ]  Add `/health` endpoint for Render uptime monitoring

### 2.4 Question Bank Expansion

- [ ]  Migrate questions from JS array to JSON files in `/backend/questions/`
- [ ]  Expand to 50+ problems across categories:
    - [ ]  Arrays & Hashing — 10 problems (e.g. Two Sum, Group Anagrams, Top K Elements)
    - [ ]  Two Pointers & Sliding Window — 8 problems
    - [ ]  Stack & Queue — 6 problems (e.g. Valid Parentheses, Min Stack)
    - [ ]  Binary Search — 6 problems (e.g. Search in Rotated Array, Koko Eating Bananas)
    - [ ]  Linked Lists — 6 problems (e.g. Reverse List, Detect Cycle)
    - [ ]  Trees & Graphs — 8 problems (e.g. Level Order BFS, Number of Islands)
    - [ ]  Dynamic Programming — 6 problems (e.g. Climbing Stairs, Coin Change)
- [ ]  Add `hints[]`, `time_complexity`, `space_complexity`, `test_cases[]` per question
- [ ]  Add `company_tags[]` field (Google, Meta, Amazon, Apple, Microsoft)
- [ ]  Auto-validate user code against test cases after `/api/run` returns

### 2.5 Auth & User Accounts (Supabase)

- [ ]  Create Supabase project (free tier: 500MB DB, 50k MAU)
- [ ]  Enable GitHub OAuth via Supabase Auth dashboard
- [ ]  Protect `/api/coach` — require valid Supabase JWT in `Authorization` header
- [ ]  Set up `@supabase/ssr` session handling in Next.js middleware
- [ ]  Create `user_progress` database table:
    
    ```sql
    CREATE TABLE user_progress (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id uuid REFERENCES auth.users ON DELETE CASCADE,
      question_id text NOT NULL,
      status text CHECK (status IN ('attempted', 'solved')),
      language text,
      code text,
      solved_at timestamptz,
      attempts integer DEFAULT 0,
      UNIQUE(user_id, question_id)
    );
    ```
    
- [ ]  Show ✅ solved / 🔄 attempted badges on sidebar question cards
- [ ]  Persist last-used code per question per user in `user_progress.code`

---

## Phase 3 — Mock Interview Mode 🚀 (Planned)

**Goal:** Simulate real technical interviews with AI evaluation and performance analytics.

### 3.1 Interview Session Engine

- [ ]  Add "Interview Mode" toggle in header (hides hints, locks AI chat)
- [ ]  Build countdown timer component (configurable: 20 / 45 / 60 min)
- [ ]  Show warning toast at 5-minute mark
- [ ]  Auto-submit code snapshot when timer reaches 0
- [ ]  Disable quick-action chips during interview mode
- [ ]  Store session: `{ start_time, end_time, question_id, language, code_snapshots[], final_code }`
- [ ]  Save session to Supabase `interview_sessions` table

### 3.2 AI Evaluator (Post-Interview via NVIDIA NIM)

- [ ]  After session ends, send full context to NIM (`mistralai/mixtral-8x7b`) for evaluation
- [ ]  Evaluation criteria:
    - [ ]  Correctness — does solution pass all test cases?
    - [ ]  Time & space complexity — is it optimal?
    - [ ]  Code quality — readability, naming conventions, edge case handling
    - [ ]  Efficiency — lines of code, unnecessary work
- [ ]  Generate performance report as JSON:
    
    ```json
    {
      "score": 78,
      "correctness": "pass",
      "complexity": { "time": "O(n)", "optimal": true },
      "feedback": "Your approach is correct. Consider renaming variables for clarity.",
      "suggested_topics": ["Hash Maps", "Two Pointers"]
    }
    ```
    
- [ ]  Render report as a styled results page with score badge
- [ ]  Compare user solution vs optimal solution side-by-side

### 3.3 Company-Specific Question Sets

- [ ]  Filter sidebar by `company_tags[]`
- [ ]  Curate 10–15 questions per top company:
    - [ ]  Google — focus: graphs, DP, string manipulation
    - [ ]  Meta — focus: arrays, trees, recursion
    - [ ]  Amazon — focus: OOP design, heaps, BFS/DFS
    - [ ]  Microsoft — focus: strings, linked lists, recursion
    - [ ]  Apple — focus: binary search, arrays, system thinking
- [ ]  Add "Company Interview Pack" landing page per company

### 3.4 Leaderboard & Social

- [ ]  Create `leaderboard` Supabase table (fastest correct solve per question)
- [ ]  Public `/leaderboard` page with top 10 per problem
- [ ]  Shareable result card (og:image generated server-side) for Twitter/LinkedIn
- [ ]  Weekly featured challenge — one problem highlighted per week with community rankings

### 3.5 Analytics Dashboard

- [ ]  User `/profile` page showing:
    - [ ]  Problems solved by difficulty (bar chart with Recharts)
    - [ ]  Activity streak calendar (GitHub-style contribution graph)
    - [ ]  Category performance radar chart (strength vs weakness by topic)
    - [ ]  Average solve time trend over last 30 days (line chart)
    - [ ]  Total sessions, total problems attempted, current streak
- [ ]  All charts use Recharts (free, client-side, no external API)

---

# 10. Security Considerations

- **Phase 1:** User provides own NVIDIA NIM API key; stored in JS memory only — never in localStorage, cookies, or any persistent storage
- **Phase 2:** NVIDIA NIM API key stored server-side as `NVIDIA_API_KEY` env var; frontend never sees it
- **Code Execution:** All user code runs in sandboxed Piston containers with CPU/memory limits
- **Input Sanitisation:** All code sent to Piston is treated as untrusted; 10s timeout enforced
- **Rate Limiting:** FastAPI endpoints rate-limited per IP using `slowapi` to prevent abuse
- **Auth:** Supabase JWT verified server-side on all protected endpoints

---

# 11. References

- [NVIDIA NIM API Catalog (Free)](https://build.nvidia.com)
- [NVIDIA NIM LLM API Docs](https://docs.api.nvidia.com/nim/reference/llm-apis)
- [NVIDIA Developer Program (Free Signup)](https://developer.nvidia.com/developer-program)
- [Piston Code Execution API](https://github.com/engineer-man/piston)
- [Supabase Free Tier](https://supabase.com/pricing)
- [Vercel Free Tier](https://vercel.com/pricing)
- [Render Free Tier](https://render.com/pricing)
- [Monaco Editor for React](https://github.com/suren-atoyan/monaco-react)