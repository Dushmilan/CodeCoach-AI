# Curriculum & Question Data Management

The **database (PostgreSQL/Supabase) is the single source of truth** for
questions, courses, modules, lessons, exercises, starter code, and test cases.
The application never reads content from the filesystem at runtime. Committed
JSON under `backend/data/courses/{c,java}/` is a transient bootstrap source
consumed by `sync_local_to_db.py` only.

## Data model

| Table            | Purpose                                             |
|------------------|-----------------------------------------------------|
| `questions`      | Question bank (difficulty, category, test cases…)   |
| `courses`        | Course metadata (id, title, language, order)        |
| `modules`        | Module metadata (course_id, title, order)           |
| `lessons`        | Lesson content (theory/exercise, order, question link) |
| `users`          | Accounts (auth, roles, plans)                       |
| `course_progress`| Per-user progress                                   |
| `submissions`    | Attempt history (incl. adapter-state status columns) |
| `coaching_interactions`, `execution_jobs` | Adapter-state audit              |
| `rescue_queue`   | Abandoned-problem re-surface queue                  |
| `review_cards`   | SM-2 spaced-repetition cards                        |
| `skills`, `question_skills`, `learning_events`, `user_skill_states` | Skill graph |
| `usage_*`, `rate_limit_events`, `user_daily_usage` | Usage metering |

All application repositories are SQL-backed (see `app/repositories/`) and are
selected unconditionally by `app/api/dependencies.py`.

## One-time bootstrap from a JSON export

`backend/scripts/sync_local_to_db.py` upserts a local JSON export
(`backend/questions/sample_questions.json` + `backend/data/courses/**`) into the database. It
is **idempotent and non-destructive**: missing rows are inserted, existing
rows with the same ID are updated, and unrelated database data is never
deleted. Safe to re-run.

> Note: `backend/questions/` is currently absent from the checkout — only
> `backend/data/courses/{c,java}/` exists. The sync script's question path
> resolves relative to `backend/`; syncing questions requires that export to
> be present.

New questions pass the `full_validate` gate (including the non-skippable
`ANIMATION` use case: `examples[0].input` must trace and the family must
compile via `scene_planner.py` + `AnimationValidator`).

```bash
python scripts/sync_local_to_db.py            # uses DATABASE_URL from .env
python scripts/sync_local_to_db.py --url postgresql://...
```

The local JSON files are a transient bootstrap only and are not required at
runtime; the database remains the canonical store.

## Tests

Test fixtures are defined in code (`tests/conftest.py`) and seed the isolated
`codecoach_test` schema directly — no data files are involved. The sync
utility itself is covered by `tests/unit/test_local_sync.py`. Shared auth
builders live in `tests/fixtures/auth_helpers.py`; the live-question inventory
is pinned in `tests/fixtures/live_question_ids.json` (107 ids). Tests refuse
non-local databases (`tests/db_guard.py`) unless `ALLOW_PRODUCTION_TEST_DB=1`.
