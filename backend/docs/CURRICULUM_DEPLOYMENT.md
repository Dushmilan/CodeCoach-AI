# Curriculum & Question Data Management

The **database (PostgreSQL/Supabase) is the single source of truth** for
questions, courses, modules, lessons, exercises, starter code, and test cases.
There are no checked-in data files: the application never reads content from
the filesystem at runtime.

## Data model

| Table            | Purpose                                             |
|------------------|-----------------------------------------------------|
| `questions`      | Question bank (difficulty, category, test cases…)   |
| `courses`        | Course metadata (id, title, language, order)        |
| `modules`        | Module metadata (course_id, title, order)           |
| `lessons`        | Lesson content (theory/exercise, order, question link) |
| `users`          | Accounts (auth, roles, plans)                       |
| `course_progress`| Per-user progress                                   |

All application repositories are SQL-backed (see `app/repositories/`) and are
selected unconditionally by `app/api/dependencies.py`.

## One-time bootstrap from a JSON export

`backend/scripts/sync_local_to_db.py` upserts a local JSON export
(`questions/sample_questions.json` + `data/courses/**`) into the database. It
is **idempotent and non-destructive**: missing rows are inserted, existing
rows with the same ID are updated, and unrelated database data is never
deleted. Safe to re-run.

```bash
python scripts/sync_local_to_db.py            # uses DATABASE_URL from .env
python scripts/sync_local_to_db.py --url postgresql://...
```

The local JSON files are a transient bootstrap only and are not required at
runtime; the database remains the canonical store.

## Tests

Test fixtures are defined in code (`tests/conftest.py`) and seed the isolated
`codecoach_test` schema directly — no data files are involved. The sync
utility itself is covered by `tests/unit/test_local_sync.py`.
