# Curriculum Deployment Workflow

The versioned curriculum repository under `backend/data/courses/` is the
**canonical source of truth** for courses, modules, lessons, exercises,
starter code, and test cases. The database (PostgreSQL/Supabase) is a
generated deployment target.

## Repository layout

```
backend/data/courses/<language>/<course-slug>/
├── course.json      # course metadata (id, title, language, order, version)
├── modules.json     # {"items": [module...]} (id, course_id, order, version)
└── lessons.json     # {"items": [lesson...]} (id, module_id, type, order, version)
```

Every course, module, and lesson carries a `version` integer (starts at 1).
Bump it when the content changes so consumers can detect revisions.

## Validation

Two layers keep the repository healthy:

1. **Unit tests** (pure data, no DB):
   - `backend/tests/unit/test_curriculum_seed.py` — schema validity, unique
     IDs, ordering, exercise→question linkage.
   - `backend/tests/unit/test_verify_curriculum.py` — the verifier's integrity
     gate on real + synthetic content.

2. **Verifier script** (`backend/scripts/verify_curriculum.py`):
   ```bash
   python scripts/verify_curriculum.py
   ```
   Runs schema lint, version presence, unique-ID, referential-integrity, and
   orphan checks (lesson→module, module→course, exercise→question). Exit 0 =
   valid, 1 = violation.

CI runs a `curriculum-validation` job whenever a PR touches curriculum data.

## Seeding

```bash
# Normal (idempotent) seed — existing courses/modules/lessons are skipped
python scripts/seed_curriculum.py

# Force re-seed — deletes each course subtree first, then inserts it
python scripts/seed_curriculum.py --force

# Verify-only — validates repo content (+ compares DB counts if reachable)
python scripts/seed_curriculum.py --verify
```

`--force` is destructive: it deletes the course + its modules + lessons
before re-inserting. Do not use it against production without a backup.

## Re-seeding semantics

| Flag       | Behavior                                                              |
|------------|-----------------------------------------------------------------------|
| (none)     | Insert missing rows; leave existing rows untouched (idempotent)       |
| `--force`  | Delete course subtree, then insert fresh                             |
| `--verify` | Integrity gate only; writes nothing                                  |

## DB count integrity check

`--verify` with a reachable `DATABASE_URL` compares repo counts
(courses/modules/lessons) against the database and fails on mismatch.
Without a database it still runs the full pure-data gate.
