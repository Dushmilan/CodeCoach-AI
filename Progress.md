# CodeCoach AI — Progress

## ✅ Done

### Phase 1 — API Refactoring
- Refactored `api/run.py` and `api/questions.py` to FastAPI `Depends` + `@lru_cache`
- `dependency_overrides` tests for both endpoints
- Fixed route-ordering bug in `api/questions.py`
- Cleaned up `app/main.py` imports

### Phase 2 — Question Repository Port/Adapter
- `QuestionRepository` ABC at `app/ports/question_repository.py`
- `FileQuestionRepository` adapter at `app/repositories/file_question_repository.py`
- `QuestionsService` fully async with repository injection
- Updated `api/questions.py` route handlers

### Phase 3 — Code Executor Port & Validation Refactor
- `CodeExecutor` port + `ExecutionResult` dataclass at `app/ports/code_executor.py`
- `PistonExecutor` adapter at `app/adapters/piston_executor.py`
- Three validation use cases accept `executor: CodeExecutor` (port)
- `mock_piston_service` fixture uses `AsyncMock(spec=CodeExecutor)`
- All 31 validation tests pass
- Cleaned up dead validation code (deleted old endpoint, 6 old test files)
- Docker Piston container running on localhost:2000 with Python 3.10.0, Node 18.15.0, Java 15.0.2
- `PistonService` reads `PISTON_API_URL` env var
- Integration tests (4/4 fast) pass against local Piston

### Phase 4 — HTTP Client Port
- `HttpClient` port interface at `frontend/src/lib/http-client.ts`
- `FetchClient` adapter at `frontend/src/lib/fetch-client.ts`
- `QuestionService`, `CodeExecutionService`, `CoachingService` all use `HttpClient` injection

### Step 1 — Language Support & Validate Fix
- JavaScript and Java enabled in editor constants
- `validateCode` service iterates test cases via `/api/run/` (was calling deleted `/api/validate/validate`)
- Frontend TypeScript compiles with 0 errors in our files

### Step 2 — Submit Endpoint
- `POST /api/submit/` endpoint at `app/api/submit.py`
- Accepts `question_id`, `language`, `code`; runs all test cases via Piston
- Returns `{ passed, total, passed_count, results[] }`
- Hidden test cases redact input/expected/actual
- 4 unit tests (all pass)

### Step 3 — Two-Button UI
- Run button → first 3 visible test cases via `/api/run/`
- Submit button → all test cases (including hidden) via `/api/submit/`
- Green Submit button next to Run button in code editor toolbar

### Step 4 — NVIDIA API Key Settings
- Settings gear icon in header
- SettingsModal component with password input + show/hide toggle
- `useSettings` hook (localStorage-backed)
- API key sent as `X-NVIDIA-API-Key` header on coaching requests
- Backend `get_nim_service` accepts header, falls back to `NVIDIA_API_KEY` env var

### Step 5 — Progress Persistence
- `userProgress` (solved/attempted) persisted in localStorage via `useLocalStorage` hook
- Survives page refresh

### Step 6 — Frontend Tests
- Vitest + jsdom + @testing-library installed
- `vitest.config.ts` created
- Unit tests for `CodeExecutionService` (`runCode`, `validateCode`, `submitCode`)
- **Note:** vitest native binding issue on Windows (`rolldown`) — requires `npm i` after deleting `package-lock.json` + `node_modules`
- Playwright e2e tests not yet written

## 🔜 Next

### Backend
- (none planned — all planned endpoints exist)

### Frontend
- Run `npm i` from scratch to fix vitest native binding
- Write Vitest tests for hooks (`useCodeExecution`, `useSettings`, etc.)
- Write Playwright smoke test (browse → edit → run → submit → coaching)

### Infrastructure
- Docker Compose for full-stack local dev (frontend + backend + Piston)
- Production CORS origins config
- HTTPS/SSL for production

### Future Features
- Supabase auth (Google OAuth optional, API key storage tied to account)
- Rich progress dashboard (solved count, streak, topic mastery)
- Question authoring UI (admin panel for adding new questions)
