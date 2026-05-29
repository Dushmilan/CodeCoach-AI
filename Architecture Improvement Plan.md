# Architecture Improvement Plan

All three items have been completed.

---

## 1. Deepen the CodeExecutor Port — DONE

- Added `evaluate_suite()` to `CodeExecutor` port with `TestCaseResult` dataclass
- Implemented per-language test runners (Python, JS, Java) in `PistonService` — single Piston request for entire test suites
- `submit.py` simplified to single `evaluate_suite()` call
- Frontend lesson page uses batch `/api/submit/` endpoint

## 2. Unify Domain Models (Question vs Lesson) — DONE

- Added `question_id: Optional[str]` to `Lesson` schema in `course_schemas.py`
- Lesson page fetches linked `Question` by ID for `starter` and `test_cases`
- Fully backward-compatible with existing lesson data

## 3. Dissolve the QuestionValidator God Module — DONE

- Extracted 8 use cases to `backend/app/use_cases/question_validation/` package
- `question_validator.py` reduced from 995 lines to ~120 lines (facade only)
- Backward-compatible re-exports preserved — 275 unit tests pass
