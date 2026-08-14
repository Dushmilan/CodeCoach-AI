# CodeCoach AI — Internal Development Guide

CodeCoach AI is a **private, closed-source project**. There is no public
contribution workflow: no forks, no external pull requests, and no public issue
labels. This guide covers how the internal team works on the repository.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Coding Conventions](#coding-conventions)
- [Documentation](#documentation)

## Code of Conduct

Internal contributors follow the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).

## Mandatory project rules

Read [AGENTS.md](./AGENTS.md) first. The hard rules always apply:

1. **Production-first engineering** — reliable, maintainable, observable, safe to operate.
2. **TDD always** — every change starts as a failing test (red → green → refactor).
3. **Supabase is the only database** — no MySQL, SQLite, or other stores.
4. **Graphify-first exploration** — run `graphify query` before any raw search.
5. **Docker rebuild after code changes** — rebuild the affected image before commit.
6. **Caveman-review before every commit** — fix every bug:/risk:/nit: finding.

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+ (pnpm)
- Docker & Docker Compose
- Git
- A Supabase project (or local Postgres for development) — see [backend/docs/CURRICULUM_DEPLOYMENT.md](./backend/docs/CURRICULUM_DEPLOYMENT.md)

### Quick start with Docker

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Manual backend setup

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt -r tests/test_requirements.txt
cp .env.example .env
# Edit .env with your Groq API key, JWT secret, and Supabase DATABASE_URL
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Manual frontend setup

```bash
cd frontend
pnpm install
cp .env.example .env.local
pnpm dev
```

### Piston (code execution)

```bash
docker run -d -p 2000:2000 --name piston ghcr.io/engineer-man/piston
```

## Making Changes

### Branch naming

- `feature/<name>` — new features
- `fix/<name>` — bug fixes
- `docs/<name>` — documentation
- `refactor/<name>` — refactoring
- `test/<name>` — adding tests

### Commit messages

Write clear, conventional commits:

```
feat(skill-graph): add recommendation endpoint and Practice Next UI

- Add GET /api/skills/recommended-questions
- Add RecommendedQuestions component with prerequisite ordering
- Add unit + simulation tests
```

## Testing

### Backend (pytest)

```bash
cd backend
python -m pytest tests/unit/           # Unit tests (53 files)
python -m pytest tests/integration/    # Integration tests (23 files) — needs isolated schema
python -m pytest tests/security/       # Security tests (7 files)
python -m pytest tests/performance/    # Performance tests (4 files)
python -m pytest tests/contract/       # OpenAPI contract tests (2 files)
python -m pytest tests/simulation/     # Skill-graph simulation (8 files)
python -m pytest tests/migrations/     # Migration tests (5 files)
python -m pytest                        # All tiers
```

### Frontend (Vitest + Playwright)

```bash
cd frontend
pnpm lint              # ESLint
pnpm typecheck         # TypeScript check (tsc --noEmit)
pnpm test:run          # Vitest single run (72 files)
npx playwright test    # E2E (15 specs; requires running stack)
```

### Before merging

```bash
# Backend
cd backend && ruff check . && ruff format . --check && python -m pytest

# Frontend
cd frontend && pnpm lint && pnpm typecheck && pnpm test:run
```

Keep the whole suite green and respect the coverage budget
(`qa/enforce_coverage_budget.py`).

## Coding Conventions

### General

- **No comments** unless logic is genuinely non-obvious
- **Named exports** over default exports
- **Async everywhere** — handlers, services, use cases
- **No secrets in code** — API keys from env vars only, never committed or logged

### Backend (Python)

- Full type annotations
- Pydantic v2 schemas at API boundaries (ORM models stay distinct)
- Module-level loggers (never `print()`)
- `snake_case` functions/variables
- FastAPI `Depends()` for dependency injection (`app/api/dependencies.py`)
- Persistence behind `ports/` interfaces with `sql_*` implementations (Supabase only)
- Every Piston language needs a code wrapper in `adapters/code_wrappers/`

### Frontend (TypeScript)

- Strict mode, no `any`
- `import type` for type-only imports
- `PascalCase` components, `camelCase` functions
- Tailwind CSS only (no CSS modules, no styled-components)
- Feature-based organization (`features/{name}/{hook,service,types}`)

### File structure

```
backend/app/
  api/            # Thin route handlers
  services/       # Business logic
  use_cases/      # Validation logic
  models/         # Pydantic schemas
  ports/          # Abstract interfaces
  repositories/   # sql_* implementations (Supabase)
  adapters/       # Concrete implementations

frontend/src/
  features/       # Feature modules
  components/     # Reusable UI
  hooks/          # Shared hooks
  lib/            # HTTP client + utilities
  providers/      # Theme, Auth, Toast, Usage providers
```

## Documentation

- Source-of-truth docs are Markdown at the repository root: [README.md](./README.md),
  [Progress.md](./Progress.md), [Ideas.md](./Ideas.md), [AGENTS.md](./AGENTS.md).
- There are **no generated HTML documents** and no Markdown→HTML converter.
- Update [Progress.md](./Progress.md) when features land or scope changes; keep
  every feature marked as Built / Partial / Planned / Known Gap.
- Keep the code knowledge graph current with `graphify update .`.

## Questions?

Ask the internal team, or check [README.md](./README.md), [Progress.md](./Progress.md),
and [Ideas.md](./Ideas.md).