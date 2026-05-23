# CodeCoach AI — Context

## Domain Glossary

| Term | Meaning |
|---|---|
| **Coach** | AI-powered assistant that provides hints, reviews, explanations, and debugging help |
| **Question** | A coding problem with description, examples, test cases, starter code, and solution |
| **Test Case** | Input/expected-output pair; can be visible (shown to student) or hidden |
| **Execution** | Running user code against test cases via Piston sandbox |
| **Validation** | Pre-submission checks on question quality (structure, test cases, starter code, solution, time limits, signatures, output format) |
| **Submission** | Full test suite run (all test cases including hidden) |
| **Run** | Quick test (first 3 visible test cases) |
| **Piston** | Self-hosted Docker container for safe multi-language code execution |

## Data Flow

```
User Code → FastAPI → PistonService → CodeWrapper (wrap code)
                                  → ExecutionResultFormatter → JSON response
                                  → Piston Container (Docker)
                                  ↓
                         ExecutionResult {stdout, stderr, exit_code, signal, execution_time, memory}

AI Coaching → FastAPI → NIMService → coaching_prompts/ (build prompt per mode)
                                  → NIM API (NVIDIA)
                                  → CoachingResponseParser (extract structured JSON)
                                  ↓
                         StructuredCoachingResponse {summary, hints, code_review, ...}

Questions → FastAPI → QuestionsService → QuestionRepository
                                  → FileQuestionRepository → sample_questions.json
                                  → validation status persisted to separate JSON file
```

## Architecture Decisions

### ADR-1: Ports/Adapters (Hexagonal) Backend
**Status:** Adopted
**Context:** Need to swap out Piston for another executor, JSON files for a database.
**Decision:** Core logic depends on abstract ports (`CodeExecutor`, `QuestionRepository`). Adapters implement them.

### ADR-2: Feature-Based Frontend
**Status:** Adopted
**Context:** Services, hooks, and types for a domain belong together.
**Decision:** Each feature (`coaching/`, `code-execution/`, `question/`) has its own `.service.ts`, `.hook.ts`, `.types.ts`.

### ADR-3: HTTP Client Port on Frontend
**Status:** Adopted
**Context:** Need testable HTTP interactions without mocking `fetch`.
**Decision:** `HttpClient` interface + `FetchClient` adapter. Services inject the client.

### ADR-4: No Required Auth
**Status:** Adopted
**Context:** Students should start solving without friction.
**Decision:** Anonymous progress via localStorage. Auth (Supabase) is optional future feature.

### ADR-5: Two-Button Workflow (Run / Submit)
**Status:** Adopted
**Context:** Students need fast feedback loops AND a final check.
**Decision:** Run = first 3 visible test cases (fast). Submit = all test cases (complete).

## File-to-Concept Mapping

| Concept | Backend File | Frontend File |
|---|---|---|---|
| AI Coaching | `backend/app/api/coach.py`, `backend/app/services/nim_service.py`, `backend/app/adapters/coaching_prompts/`, `backend/app/adapters/coaching_response_parser.py` | `frontend/src/features/coaching/` |
| Code Execution | `backend/app/api/run.py`, `backend/app/services/piston_service.py`, `backend/app/adapters/code_wrappers/`, `backend/app/services/execution_result_formatter.py`, `backend/app/services/static_code_validator.py` | `frontend/src/features/code-execution/`, `frontend/src/lib/client-js-executor.ts` |
| Questions | `backend/app/api/questions.py`, `backend/app/repositories/file_question_repository.py` | `frontend/src/features/question/` |
| Submission | `backend/app/api/submit.py` | (same as code-execution) |
| Validation | `backend/app/use_cases/`, `backend/app/services/question_validator.py` | — |
| Health | `backend/app/api/health.py` | — |
| Auth | `backend/app/api/auth.py`, `backend/app/services/auth_service.py` | — |

## Key Constraints

- **3 languages only**: Python, JavaScript, Java
- **Piston API timeout**: 30s per execution
- **Rate limits**: Coach 10/min, Run 30/min, Questions 100/min
- **Hidden test cases**: Input/expected/output redacted in response
- **Progress**: localStorage only (no server-side persistence yet)
