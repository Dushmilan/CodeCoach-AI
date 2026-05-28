# Issues

## I1 — `@lru_cache()` prevents question reload from disk

**Status:** ✅ Fixed & Closed  
**Severity:** Critical  
**Files affected:**
- `backend/app/api/questions.py:10-12`

**Root cause:** `get_questions_service()` was decorated with `@lru_cache()`, creating a single `QuestionsService` instance per server process lifetime. Questions generated after server start were never visible until restart.

**Fix:** Removed `@lru_cache()`. A fresh service (and its `FileQuestionRepository`) is created per request, re-reading the JSON file from disk each time.

---

## I2 — No error handling in repository load — one bad question kills all

**Status:** ✅ Fixed & Closed  
**Severity:** High  
**Files affected:**
- `backend/app/repositories/file_question_repository.py:26-32`

**Root cause:** `_load()` iterated `Question(**item)` without try/except. A single malformed question (invalid types, missing fields) would throw a Pydantic validation error and crash the entire load, yielding zero questions.

**Fix:** Wrapped each `Question(**item)` in try/except. Malformed questions are logged as warnings and skipped; valid questions continue loading.

---

## I3 — Pydantic schema too strict for NIM-generated data (root cause of formatting failures)

**Status:** ✅ Fixed & Closed  
**Severity:** High  
**Files affected:**
- `backend/app/models/schemas.py`

**Root cause:** The NIM-based question generator (`generate_questions.py`) outputs questions in a flexible JSON format where several fields are not plain strings but complex types:

| Generator Output | Schema Expected | What happened |
|---|---|---|
| `input` / `expected_output` as dict | `str` | Pydantic validation error |
| `description` as dict or list | `str` | Pydantic validation error |
| `starter` as string or list `[{language, code}]` | `StarterCode` object | Pydantic validation error |
| `solution` as dict | `str` | Pydantic validation error |
| Example missing `output` key (uses `expected_output` instead) | — | Missing required field |

When these validation errors occurred inside `_load()` (I2), they crashed the entire load, not just the individual question. The combination of I2 + I3 meant **zero** of the 18 AI-generated questions were loadable.

**Fix:** Made the schema flexible to accept the NIM generator's output format:
- `TestCase`/`Example` `input`/`output`, `expected_output`: `Union[str, Dict, list, int, float, None]` → auto-converted to JSON string via `field_validator`
- `Example`: `model_validator` maps `expected_output` → `output`; `output` defaults to `""`
- `StarterCode`: all fields default to `""`
- `Question.description`: accepts `Union[str, Dict, List]` → normalized to string
- `Question.starter`: accepts `Union[StarterCode, str, List, Dict]` — normalizes string to empty starter, list-of-lang-code to flat dict via `model_validator`
- `Question.solution`: accepts `Union[str, Dict]` → auto-converted to string

**Lesson learned:** The NIM generator and the Pydantic schemas were developed independently. Future NIM generator changes should include schema validation tests to catch drift early.

---

## I4 — `HTTPException` swallowed by generic handler in search endpoint

**Status:** ✅ Fixed & Closed  
**Severity:** Low  
**Files affected:**
- `backend/app/api/questions.py:93-129`

**Root cause:** `search_questions` raised `HTTPException(400)` for empty queries, but the outer `except Exception` caught it and re-raised as 500 instead of propagating the 400.

**Fix:** Added `except HTTPException as he: raise he` before the generic exception handler.

---

## I5 — Integration test assumes companies exist in real data

**Status:** ✅ Fixed & Closed  
**Severity:** Low  
**Files affected:**
- `backend/tests/integration/test_questions_endpoints.py:149-161`

**Root cause:** `test_get_companies` asserted specific company names ("Google", "Amazon", etc.) that do not exist in `sample_questions.json` (all `company_tags` are empty).

**Fix:** Relaxed assertion to verify the API returns a valid `list` without checking specific values.

---

## I6 — Resizing feature broken: Panel overlap and drag-resize erratic behavior

**Status:** ✅ Fixed & Closed  
**Severity:** Medium  
**Files affected:**
- `frontend/src/components/layout/elements/CodeEditorContainer.tsx`

**Root cause:** 
1. **Event Swallowing:** Monaco Editor captured mouse events immediately upon enter, interrupting `mousemove` drag operations.
2. **Layout Overflow:** Hardcoded 500px `maxHeight` for the output panel caused the layout to overflow/overlap when the browser window was smaller than the panel height.
3. **Text Selection Interference:** Missing `select-none` during drag caused browser-native text selection to interfere with resizing.

**Fix:** 
1. **Global Drag Overlay:** Added a `fixed inset-0` transparent overlay that appears only during resize, intercepting all mouse events and blocking interaction with the Monaco editor until the drag completes.
2. **Dynamic Height Capping:** Switched from hardcoded 500px to dynamic `maxHeight` calculation (`containerHeight - 150px`) to guarantee at least 150px of breathing room for the editor regardless of screen size.
3. **Selection Lock:** Added `select-none` to the resize overlay to ensure smooth dragging without accidental text highlighting.
