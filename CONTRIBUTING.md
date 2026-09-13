# CodeCoach AI — Internal Development Guide

> For uni students: this is the day-to-day manual. [AGENTS.md](./AGENTS.md) is the law,
> [README.md](./README.md) is the onboarding overview. If they disagree, AGENTS.md wins.

CodeCoach AI is a **private, closed-source project**. There is no public
contribution workflow: no forks, no external pull requests, and no public issue
labels. Students work through assigned Issues, one branch + one worktree each.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Mandatory project rules](#mandatory-project-rules)
- [Development Setup](#development-setup)
- [Your first task (checklist)](#your-first-task-checklist)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Coding Conventions](#coding-conventions)
- [Documentation](#documentation)

## Code of Conduct

Internal contributors follow the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).

## Mandatory project rules

Read [AGENTS.md](./AGENTS.md) first. The hard rules always apply:

1. **Production-first engineering** — reliable, maintainable, observable, safe to operate.
2. **TDD always** — every code change starts as a failing test (red → green → refactor).
   Docs-only changes are the only exception (say so explicitly in the PR).
3. **Supabase is the only database** — no MySQL, SQLite, local/self-hosted Postgres,
   or any other store. Tests use the isolated `codecoach_test` schema only.
4. **Every question must be visualizable** — the `ANIMATION` validation gate is not
   skippable: `examples[0].input` must be traceable, the algorithm resolvable via
   `reference_solutions.py`, the family compilable
   (`array/backtrack/stack/linked_list/tree/graph/grid/intervals`), `animation.steps >= 3`.
5. **Graphify-first exploration** — `graphify query` / `path` / `explain` before any
   grep/read/glob; `graphify update .` after code changes.
6. **One session = one branch + one worktree** — never share a worktree, never work on `main`.
7. **Caveman-review before every commit** — fix every `bug:`/`risk:`/`nit:` finding.
8. **Docker rebuild after code changes** — rebuild the affected image before commit.

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+ with `pnpm` 9+
- Docker & Docker Compose
- Git + `gh` CLI
- A Supabase project (PostgreSQL) + Groq API key — see
  [backend/docs/CURRICULUM_DEPLOYMENT.md](./backend/docs/CURRICULUM_DEPLOYMENT.md).
  TEST wiring lives in [Docs/TEST_ENVIRONMENT.md](./Docs/TEST_ENVIRONMENT.md).
  There is no local Postgres for runtime; tests use the isolated `codecoach_test`
  schema via `DATABASE_URL` + `DATABASE_SEARCH_PATH`.

### Quick start with Docker

```bash
cp .env.example .env          # fill GROQ_API_KEY, JWT_SECRET_KEY, DATABASE_URL, Supabase keys
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Animation viewer: http://localhost:9000 (or `pnpm dev:all` in `frontend/`)

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
pnpm dev          # app only
pnpm dev:all      # app + Motion Canvas viewer (:9000) together
```

### Piston (code execution)

```bash
docker run -d -p 2000:2000 --name piston ghcr.io/engineer-man/piston
```

## Your first task (checklist)

Good first tasks: fix a small bug, add a missing test, or improve an error message.
Ask a maintainer to point you at an Issue.

- [ ] `git worktree list` — check which directories/branches others own.
- [ ] `gh issue list --state open` — pick an Issue (or `gh issue create` first).
- [ ] `git fetch origin && git worktree add ../CodeCoach-AI-<slug> -b <type>/<issue>-<slug> origin/main`
- [ ] `graphify query "<what you are changing>"` before reading code.
- [ ] Write the failing test first (TDD red), watch it fail for the right reason.
- [ ] Implement the smallest fix (green), then clean up (refactor).
- [ ] Run the gates: `ruff check . && ruff format . --check`, relevant `pytest` tiers,
      `pnpm lint && pnpm typecheck && pnpm test:run`.
- [ ] `git add` + `git diff --staged`, load `caveman-review`, fix **all** findings, re-stage.
- [ ] `git push -u origin <branch>`, open a PR with `Closes #<issue-number>`.

## Making Changes

### One session = one branch + one worktree

Parallel sessions must never share a directory or branch:

```bash
git fetch origin
git worktree add ../CodeCoach-AI-<slug> -b <type>/<issue>-<slug> origin/main
cd ../CodeCoach-AI-<slug>
```

- Resuming a remote branch: `git fetch origin && git worktree add ../CodeCoach-AI-<slug> <branch>`.
- Never `git checkout` a branch checked out in another worktree; never switch branches
  with a dirty tree — create a new worktree instead.
- Cleanup from the main checkout: `git worktree remove ../CodeCoach-AI-<slug> && git worktree prune`.
- No direct commits or pushes to `main` — all changes go through a branch + PR.

### Branch naming

Format: `<type>/<issue-number>-<kebab-slug>` where `<type>` is `feat|fix|chore|docs|refactor|test`

- `feat/42-ai-animation-viewer` — new features
- `fix/101-monaco-render` — bug fixes
- `chore/88-coverage-bump` — maintenance
- `docs/157-readme-onboarding` — documentation
- `test/55-add-e2e` — tests

If no Issue exists, create one first (`gh issue create`), then branch. Trivial no-issue
work is the only exception: `<type>/no-issue-<slug>` (call it out in the PR).
Always branch from latest `origin/main`. One Issue = one branch. Open the PR with
`Closes #<issue-number>`.

### Commit messages

Write clear, conventional commits:

```
feat(skill-graph): add recommendation endpoint and Practice Next UI

- Add GET /api/skills/recommended-questions
- Add RecommendedQuestions component with prerequisite ordering
- Add unit + simulation tests
```

Docs-only changes: say so explicitly (`docs(157): …`, PR notes "docs-only, no TDD").

## Testing

### Backend (pytest)

```bash
cd backend
python -m pytest tests/unit/           # Unit tests (82 files)
python -m pytest tests/integration/    # Integration tests (33 files) — needs isolated schema
python -m pytest tests/security/       # Security tests (5 files)
python -m pytest tests/performance/    # Performance tests (2 files)
python -m pytest tests/contract/       # OpenAPI contract tests (1 file)
python -m pytest tests/simulation/     # Skill-graph simulation (2 files)
python -m pytest tests/migrations/     # Migration tests (2 files)
python -m pytest                        # All tiers
```

Integration tests need `DATABASE_URL` pointed at the isolated schema (see `tests/conftest.py`).
Never touch the production schema from tests.

### Frontend (Vitest + Playwright)

```bash
cd frontend
pnpm lint              # ESLint (0 warnings)
pnpm typecheck         # TypeScript check (tsc --noEmit, 0 errors)
pnpm test:run          # Vitest single run (80 files)
npx playwright test    # E2E (15 specs; requires backend :8000 + frontend :3000 + viewer :9000)
```

### Before committing

```bash
# Backend
cd backend && ruff check . && ruff format . --check && python -m pytest tests/unit

# Frontend
cd frontend && pnpm lint && pnpm typecheck && pnpm test:run
```

Keep the whole suite green and respect the coverage budget
(`qa/enforce_coverage_budget.py`). Flaky tests are quarantined via
`backend/tests/enforce_flaky_quarantine.py` — quarantine, don't commit flakes.

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
  use_cases/      # Validation logic (incl. ANIMATION gate)
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
- Rebuild the affected Docker image after code changes, before commit.

## Questions?

Ask a maintainer, or check [README.md](./README.md) (onboarding),
[Progress.md](./Progress.md) (status), and [Ideas.md](./Ideas.md) (backlog).
