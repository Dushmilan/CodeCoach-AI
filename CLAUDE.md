# CodeCoach AI — Engineering Manifesto

## Project

Open-source LeetCode alternative for university students. Practice coding interview questions with instant feedback, AI coaching, and progress tracking — powered by NVIDIA's free-tier API.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, Pydantic v2 |
| Frontend | Next.js 14 (App Router), React 18, TypeScript |
| Editor | Monaco Editor (`@monaco-editor/react`) |
| Styling | Tailwind CSS 3, `tailwind-merge`, `clsx` |
| Code Exec | Piston (self-hosted Docker container) |
| AI Coach | NVIDIA NIM (LLaMA 3.1 8B) |
| Testing | pytest (backend), Vitest (frontend) |
| Infra | Docker Compose, SQLite |

## Architecture

**Clean Architecture / Hexagonal (Ports/Adapters)** — backend only.

```
backend/app/
  ports/          Abstract interfaces (ABCs)
  adapters/       Concrete implementations of ports
  use_cases/      Single-responsibility validation logic
  services/       Business logic (wraps ports)
  repositories/   Data storage (file-based, JSON)
  api/            FastAPI route handlers (thin)
  models/         Pydantic schemas
  middleware/     Rate limiting
  dependencies/   FastAPI Depends injection
```

**Feature-based** — frontend only.

```
frontend/src/
  features/       {coaching, code-execution, question}/ {hook, service, types}
  components/     Reusable UI (editor, chat, sidebar, header, layout)
  lib/            HTTP client port/adapter
  hooks/          Shared hooks (useLocalStorage, useDebounce)
  providers/      ThemeProvider
```

## Conventions

- **No comments in code** — unless the logic is genuinely non-obvious.
- **Named exports** — prefer named exports over default exports.
- **Async everywhere** — backend handlers, services, use cases are all `async def`.
- **Dependency injection** — FastAPI `Depends()` for services, constructor injection for use cases.
- **Feature hooks** — each feature has a `.hook.ts` that wraps the service for component use.
- **HTTP client port** — frontend services inject `HttpClient`, never call `fetch` directly.
- **No secrets in code** — API keys come from headers or env vars, never hardcoded.

## Commands

### Backend
```bash
uvicorn app.main:app --reload         # Dev server (port 8000)
python -m pytest                      # Run all tests
python -m pytest tests/unit/          # Unit tests only
python -m pytest tests/integration/   # Integration tests only
python -m pytest --cov=app            # With coverage
ruff check .                          # Lint
ruff format . --check                 # Format check
mypy app/                             # Type check
```

### Frontend
```bash
pnpm dev              # Dev server (port 3000)
pnpm build            # Production build
pnpm lint             # ESLint
pnpm typecheck        # TypeScript check (tsc --noEmit)
pnpm test             # Vitest
pnpm test:run         # Vitest single run
```

### Docker
```bash
docker compose up --build   # Full stack
docker compose up backend   # Backend only
docker compose up frontend  # Frontend only
```

## Critical Rules

1. **Never edit** `__pycache__/`, `node_modules/`, `venv/`, `.next/`, `*.db`, `*.sqlite`
2. **Never commit** `.env`, `.env.local`, API keys, secrets
3. **Never use `Any` in TypeScript** — prefer specific types or `unknown`
4. **Never use `print()` in backend** — use `logging` module
5. **Never mutate state directly** — use `useCallback`, `useMemo` for derived values
6. **Always add tests** for new endpoints, services, or use cases
7. **Always run lint + typecheck + tests** before claiming work is done

## AI Agent Permissions

- ✅ Read/write any source file under `backend/` and `frontend/src/`
- ✅ Create new files following existing patterns
- ✅ Edit `CLAUDE.md`, `CONTEXT.md`, `opencode.jsonc` with review
- ❌ Do not delete files without confirming
- ❌ Do not modify CI/CD workflows without reviewing current pipelines
- ❌ Do not run destructive database operations
