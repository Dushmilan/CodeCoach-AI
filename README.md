# CodeCoach AI

**A free, open-source AI-powered coding practice platform for university students.**

Practice DSA problems and learn programming languages with structured lessons and real-time AI coaching — no subscription needed.

---

## Table of Contents

- [What is CodeCoach AI?](#what-is-codecoach-ai)
- [Who is it for?](#who-is-it-for)
- [Features](#features)
- [Roadmap](#roadmap)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

---

## What is CodeCoach AI?

CodeCoach AI is an open-source LeetCode alternative with integrated AI coaching. It helps university students:

- **Practice coding interview questions** — 36 DSA problems (target: 90) across 14 standard topics with Python, JavaScript, and Java starter code
- **Learn programming languages** — structured C, Python, and Java curricula with interleaved theory and coding exercises (coming soon)
- **Get instant AI coaching** — hints, code reviews, explanations, and debugging help powered by NVIDIA NIM or Google Gemini (BYO API key)
- **Submit and grade** — code runs against test cases in an isolated Piston container with pass/fail results

No ads, no data selling, no subscriptions. Students bring their own free NVIDIA API key for AI coaching.

## Who is it for?

| Audience | Need |
|---|---|
| **Struggling CS students** | Hand-holding through basics, structured learning |
| **Interview grinders** | 100+ coding problems with AI coaching |
| **Non-CS majors** | Learn programming from scratch |
| **Professors** | Free, curriculum-aligned tool to recommend to classes |

Multi-institution, drop-in, voluntary — students sign up on their own time, zero course credit required.

## Features

### Built

| Feature | Description |
|---|---|---|
| **AI Coaching** | 5 modes (Hint, Review, Explain, Debug, Freeform) via NVIDIA NIM or Google Gemini — structured JSON responses + SSE streaming |
| **Code Execution** | Piston container — Python, JavaScript, Java with smart code wrapping for test harness generation |
| **Question Bank** | 36 DSA questions across 14/14 topics with full CRUD, search, filter by difficulty/category |
| **Submit & Grade** | Run code against visible + hidden test cases, pass/fail reporting |
| **Question Validation** | 7 validation use cases — structure, test cases, starter code, solution, time limits, function signature, output format |
| **Authentication** | JWT-based email/password registration + login, bcrypt hashing |
| **Frontend Workspace** | Monaco Editor, collapsible sidebar, dark/light theme, resizable panels, AI chat with quick actions |
| **Testing** | 12 pytest backend test files, 20+ Vitest frontend tests, Playwright E2E tests |
| **Docker Deployment** | 3-service Docker Compose (backend, frontend, piston) |

### Planned

| Phase | Scope |
|---|---|
| **Phase 1 — DSA Ship** | 54 more questions → 90 total (24 Easy / 10 Medium / 2 Hard existing) across 14 standard topics. Google OAuth. Privacy policy page. Polish pass. |
| **Phase 2 — Curricula** | C, Python, Java language curricula with interleaved theory + coding exercises. `/learn` navigation. Context-aware AI coaching. |
| **Phase 3 — Expand** | DBMS/SQL module, OOP/Design Patterns, Web Dev (React, Node), theory/MCQ question type. Classroom dashboard. |

## Roadmap

```
Phase 1 ─── DSA Practice (current focus)
├── 100 coding questions ─── 14 standard topics
├── Google OAuth
├── Privacy policy + For Educators page
└── Polish (onboarding, empty states, error handling)

Phase 2 ─── Programming Language Curricula
├── C curriculum ─── 15-20 lessons
├── Python curriculum ─── 15-20 lessons
├── Java curriculum ─── 15-20 lessons
└── Context-aware AI coaching per lesson

Phase 3 ─── Future Modules
├── DBMS / SQL
├── OOP & Design Patterns
├── Web Development (React, Node)
├── Theory / MCQ question type
└── Classroom dashboard
```

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11+, FastAPI, Pydantic v2, Uvicorn |
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript |
| **Editor** | Monaco Editor (`@monaco-editor/react`) |
| **Styling** | Tailwind CSS 3, `tailwind-merge`, `clsx` |
| **Code Execution** | Piston (self-hosted Docker container) |
| **AI Coach** | NVIDIA NIM (LLaMA 3.1 8B) via `integrate.api.nvidia.com/v1` or Google Gemini via `generativelanguage.googleapis.com` |
| **Auth** | JWT (python-jose), bcrypt |
| **Testing** | pytest (backend), Vitest + Playwright (frontend) |
| **Infra** | Docker Compose, SQLite (file-based) |

## Architecture

### Backend — Clean Architecture / Hexagonal (Ports/Adapters)

```
backend/app/
  ports/            Abstract interfaces (ABCs)
  adapters/         Concrete implementations (PistonExecutor)
  use_cases/        Single-responsibility validation logic
  services/         Business logic wrapping ports
  repositories/     File-based JSON storage
  api/              Thin FastAPI route handlers
  models/           Pydantic schemas
  middleware/       Rate limiting
  dependencies/     FastAPI Depends injection
```

### Frontend — Feature-based

```
frontend/src/
  features/     {coaching, code-execution, question}/ {hook, service, types}
  components/   Reusable UI (editor, chat, sidebar, header, layout)
  lib/          HTTP client port/adapter (FetchClient)
  hooks/        Shared hooks (useLocalStorage, useDebounce, useTheme)
  providers/    ThemeProvider
```

### Key architectural decisions

- **BYO API key** — NVIDIA API key is stored in browser localStorage, never sent to the backend. The backend proxies requests to NVIDIA NIM using the key from the request header.
- **Code wrapping** — Every language supported by Piston has a `_wrap_<language>_code` method that adds a test harness converting stdin → function call → stdout. Without this, bare function definitions produce no output.
- **File-based storage** — Questions and users are stored in JSON files (not SQLite yet). Simple, portable, version-controllable. Migrate to a database when content scales.
- **Dependency injection** — FastAPI `Depends()` for services, constructor injection for use cases. Makes the backend testable with mocks.

## Getting Started

### Quick start with Docker

```bash
docker compose up --build
```

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Manual setup

#### Backend

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your NVIDIA API key
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
pnpm install
cp .env.example .env.local
pnpm dev
```

#### Piston (code execution)

```bash
docker run -d -p 2000:2000 --name piston ghcr.io/engineer-man/piston
```

### Environment Variables

#### Backend (`.env`)

```
NVIDIA_API_KEY=your_nvidia_nim_api_key
GOOGLE_API_KEY=your_google_gemini_api_key
JWT_SECRET_KEY=your_jwt_secret_key
PISTON_API_URL=http://localhost:2000/api/v2/piston
```

Get a free API key from [NVIDIA NIM](https://build.nvidia.com/nvidia/llama-3_1-nemotron-70b-instruct) or [Google Gemini](https://aistudio.google.com/apikey).

#### Frontend (`.env.local`)

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Project Structure

```
CodeCoach-AI/
├── backend/
│   ├── app/
│   │   ├── api/               # Route handlers
│   │   │   ├── coach.py           # AI coaching endpoints
│   │   │   ├── run.py             # Code execution endpoints
│   │   │   ├── questions.py       # Question bank endpoints
│   │   │   ├── submit.py          # Submit & grade endpoints
│   │   │   ├── question_validation.py  # Question validation endpoints
│   │   │   ├── auth.py            # Authentication endpoints
│   │   │   ├── health.py          # Health check endpoints
│   │   │   └── debug.py           # Debug endpoints
│   │   ├── models/             # Pydantic schemas
│   │   ├── ports/              # Abstract interfaces (ABCs)
│   │   ├── adapters/           # Concrete implementations
│   │   ├── services/           # Business logic
│   │   ├── use_cases/          # Validation use cases
│   │   ├── repositories/       # File-based JSON storage
│   │   ├── middleware/         # Rate limiting
│   │   └── dependencies/       # FastAPI Depends injection
│   ├── tests/                  # pytest test suite
│   └── questions/              # JSON question bank
├── frontend/
│   └── src/
│       ├── app/                # Next.js App Router pages
│       │   ├── page.tsx            # Main workspace
│       │   ├── layout.tsx          # Root layout
│       │   └── privacy/            # Privacy policy page
│       ├── components/         # Reusable UI components
│       │   ├── header/             # App header with nav
│       │   ├── sidebar/            # Question list, filters, description
│       │   ├── editor/             # Monaco Editor wrapper
│       │   ├── chat/               # AI chat panel
│       │   ├── layout/             # Layout containers
│       │   ├── settings/           # Settings modal
│       │   └── ui/                 # Primitive UI components
│       ├── features/           # Feature modules (hook + service + types)
│       ├── lib/                # HTTP client
│       ├── hooks/              # Shared hooks
│       └── providers/          # Theme provider
├── docker-compose.yml          # 3-service Docker Compose
├── goal.md                     # Project vision and scope
├── progress.md                 # Current progress summary
├── EDUCATORS.md                # One-pager for professors
└── CLAUDE.md                   # Engineering guidelines
```

## Testing

### Backend (pytest)

```bash
cd backend
python -m pytest                       # All tests
python -m pytest tests/unit/           # Unit tests
python -m pytest tests/integration/    # Integration tests
python -m pytest --cov=app             # With coverage (85% threshold)
```

### Frontend (Vitest)

```bash
cd frontend
pnpm test                             # Watch mode
pnpm test:run                         # Single run
pnpm lint                             # ESLint
pnpm typecheck                        # TypeScript check
```

### E2E (Playwright)

```bash
cd frontend
pnpm exec playwright test             # Requires dev server running
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes — follow the conventions in [CLAUDE.md](./CLAUDE.md)
4. Add or update tests
5. Run lint + typecheck + tests
6. Submit a pull request

### Conventions

- No comments in code unless logic is genuinely non-obvious
- Named exports over default exports
- Async everywhere (backend handlers, services, use cases)
- FastAPI `Depends()` for dependency injection
- Every language supported by Piston needs a `_wrap_<language>_code` method
- Never commit secrets, API keys, or `.env` files

## License

MIT — see [LICENSE](LICENSE) for details.
