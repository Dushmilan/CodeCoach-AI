# CodeCoach AI — Engineering Manifesto

## Project

Private AI-powered coding practice platform for university students. Practice coding interview questions with instant feedback, AI coaching, animated solutions, progress tracking, and a skill graph — powered by Groq. This is a closed-source project.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, Pydantic v2 |
| Frontend | Next.js 14 (App Router), React 18, TypeScript |
| Editor | Monaco Editor (`@monaco-editor/react`) |
| Styling | Tailwind CSS 3, `tailwind-merge`, `clsx` |
| Code Exec | Piston (self-hosted Docker container) |
| AI Coach | Groq (LLaMA 3.3 70B versatile / LLaMA 3.1 8B instant) |
| Testing | pytest (backend), Vitest (frontend) |
| Infra | Docker Compose, Supabase PostgreSQL (async SQLAlchemy) + Redis |

## Architecture

**Clean Architecture / Hexagonal (Ports/Adapters)** — backend only.

```
backend/app/
  ports/          Abstract interfaces (ABCs)
  adapters/       Concrete implementations of ports
    code_wrappers/      Language-specific code test harnesses (Python/JS/Java)
    coaching_prompts/   Per-mode AI prompt templates (hint/review/explain/debug/freeform/animate)
    coaching_response_parser.py  Structured JSON response extraction + fallback
  use_cases/      Single-responsibility validation logic
  services/       Business logic (wraps ports, delegates to adapters)
    execution_result_formatter.py  Piston API response → uniform dict
    static_code_validator.py       Pre-flight code surface checks
  repositories/   SQLAlchemy repositories (sql_*, Supabase/PostgreSQL only)
  api/            FastAPI route handlers (thin)
  models/         Pydantic schemas
  middleware/     Rate limiting
  dependencies/   FastAPI Depends injection
```

**Feature-based** — frontend only.

```
frontend/src/
  features/       {auth, coaching, code-execution, question, curriculum, skill-graph,
                   rescue, animation, usage}/ {hook, service, types}
  components/     Reusable UI (editor, chat, sidebar, header, layout, rescue, visualization, admin)
  lib/            HTTP client port/adapter (FetchClient)
  hooks/          Shared hooks (useLocalStorage, useDebounce)
  providers/      ThemeProvider, AuthProvider, Toast, Usage context
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

## Language Wrapper Convention

Every language supported by Piston execution must have a code wrapper in `backend/app/adapters/code_wrappers/`. The wrapper adds a test harness to raw user code (function definitions) before sending it to Piston, so the code reads from stdin and writes to stdout.

**Pattern for adding a new language:**

1. Create a `backend/app/adapters/code_wrappers/<language>_wrapper.py` with a class implementing `CodeWrapper` (ABC from `base.py`)
2. Instantiate it in `adapters/code_wrappers/__init__.py` and add it to `WRAPPERS` dict
3. The wrapper must handle:
   - Extracting the function/method name from the starter code
   - Reading stdin and passing it as the function argument
   - Stripping JSON string quotes from stdin when the test data is JSON-encoded
   - Printing the return value to stdout (booleans as lowercase, objects/arrays as JSON)
4. For single `String`-param Java functions: use direct invocation (no reflection, no helpers)
5. For multi-param or complex-return Java functions: use reflection + embedded helpers (`__convertArg`, `__toJson`, `__JsonParser`)

See `PythonCodeWrapper`, `JavaScriptCodeWrapper`, and `JavaCodeWrapper` as reference implementations.

## Critical Rules

1. **Never edit** `__pycache__/`, `node_modules/`, `venv/`, `.next/`, `*.db`, `*.sqlite`
2. **Never commit** `.env`, `.env.local`, API keys, secrets
3. **Never use `Any` in TypeScript** — prefer specific types or `unknown`
4. **Never use `print()` in backend`** — use `logging` module
5. **Never mutate state directly** — use `useCallback`, `useMemo` for derived values
6. **Always add tests** for new endpoints, services, or use cases
7. **Always run lint + typecheck + tests** before claiming work is done
8. **Every new language must add a wrapper class** in `adapters/code_wrappers/` and register it in the `WRAPPERS` dict — without a wrapper, the Piston submit/validate flow will send bare function definitions that produce no output
9. **Always update Progress.md on feature completion** — after any feature, fix, or significant change, update `Progress.md` to reflect the new state (test counts, questions count, new capabilities) and `Ideas.md` if scope changed. This keeps the project compass accurate for all agents.
10. **Update knowledge graph on task completion** — after every feature, fix, or debugging task finishes, run `graphify update .` to refresh the code knowledge graph, then `git add graphify-out/` and commit it alongside the feature changes. This keeps the graph in sync for all agents and tools.
11. **Use graphify for codebase questions** — when you need to understand the codebase structure, find relationships between files, or scan for relevant code, use `graphify query "<question>"` or `graphify explain "<concept>"` instead of raw grep/glob. This returns a focused subgraph faster and with more context than ad-hoc searches.

## Session Context — Bug Fix (May 28, 2026)

**Problem:** 18 AI-generated questions not loading in frontend — 3 interacting bugs:
1. `@lru_cache()` on questions API cached stale data (`backend/app/api/questions.py:10-12`)
2. No error handling in `FileQuestionRepository._load()` (`backend/app/repositories/file_question_repository.py:26-32`)
3. Pydantic schemas too strict for NIM generator's flexible output format (`backend/app/models/schemas.py`)

**Schema flexibility pattern** (for NIM-generated data):
- TestCase/Example input/output fields: `Union[str, Dict, list, int, float, None]` with `field_validator` → JSON string
- Question description: `Union[str, Dict, List]` → normalized to string
- Question starter: `Union[StarterCode, str, List, Dict]` → normalized via `model_validator`
- Question solution: `Union[str, Dict]` → converted to string
- Example: `model_validator` maps `expected_output` → `output` when missing

**Result:** All 18 questions load. 296 backend tests pass. See `Issues.md` for full details.

**Lesson:** NIM generator output and Pydantic schemas must be validated together. Add schema-level tests for generated data to catch format drift.

## AI Agent Permissions

- ✅ Read/write any source file under `backend/` and `frontend/src/`
- ✅ Create new files following existing patterns
- ✅ Edit `CLAUDE.md`, `AGENTS.md`, `opencode.json`/`.opencode/*` with review
- ❌ Do not delete files without confirming
- ❌ Do not modify CI/CD workflows without reviewing current pipelines
- ❌ Do not run destructive database operations
