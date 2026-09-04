# CodeCoach AI API Test Suite

## Overview

Production-grade pytest suite for the CodeCoach AI backend, covering unit
behavior, integrations, OpenAPI contracts, security, performance/load,
skill-graph simulations, and Alembic migrations. All repository-backed tests run
against an **isolated `codecoach_test` schema on PostgreSQL** (the same dialect
as the Supabase production database).

## Suite structure

```
tests/
├── conftest.py                 # Fixtures: app, client, isolated schema, auth mocks, 50-question seed bank
├── db_guard.py                 # Refuses non-local DB hosts (ALLOW_PRODUCTION_TEST_DB=1 override)
├── db_helpers.py               # Schema creation/teardown helpers
├── test_requirements.txt       # Test-only dependencies
├── fixtures/
│   ├── factories.py            # Test data generators
│   ├── auth_helpers.py         # Shared register/admin header builders
│   ├── live_question_ids.json  # Pinned live-question inventory (107 ids)
│   └── mock_coaching_provider.py
├── unit/            (82 files) # Services, rules, wrappers, repositories (sql_*), validators
├── integration/    (33 files)  # Endpoints against the app + isolated DB schema
├── contract/        (1 file)   # OpenAPI response-contract validation
├── security/        (5 files)  # Auth, injection, CORS, headers, abuse detection
├── performance/     (2 files)  # Load / concurrency / rate-limit stress
├── simulation/      (2 files)  # Deterministic skill-graph learner simulations
├── migrations/      (2 files)  # Alembic up/down + schema-vs-model drift
├── enforce_flaky_quarantine.py # CI gate for the flaky-test manifest
└── flaky-quarantine.json       # Quarantined flaky tests (must stay green)
```

## Database setup

Tests never touch the production schema. `conftest.py` creates an isolated
`codecoach_test` schema on the same PostgreSQL server pointed at by
`DATABASE_URL` and drops it after the run (per-worker `codecoach_test_gwN`
schemas under xdist, selected via `DATABASE_SEARCH_PATH`).

Local Postgres (recommended for speed):

```bash
docker run -d --name codecoach-testdb -e POSTGRES_DB=codecoach_test \
  -e POSTGRES_USER=codecoach -e POSTGRES_PASSWORD=codecoach \
  -p 5433:5432 postgres:16-alpine

export DATABASE_URL=postgresql://codecoach:codecoach@127.0.0.1:5433/codecoach_test
export DATABASE_SEARCH_PATH=codecoach_test
```

> Port note: the `-p 5433:5432` mapping above exposes container port 5432 as
> host port 5433. `conftest.py` defaults to `127.0.0.1:5432` when `DATABASE_URL`
> is unset — always export `DATABASE_URL` explicitly as shown.

```bash
docker run -d --name codecoach-testdb -e POSTGRES_DB=codecoach_test \
  -e POSTGRES_USER=codecoach -e POSTGRES_PASSWORD=codecoach \
  -p 5433:5432 postgres:16-alpine

export DATABASE_URL=postgresql://codecoach:codecoach@127.0.0.1:5433/codecoach_test
export DATABASE_SEARCH_PATH=codecoach_test
```

## Running

```bash
cd backend
pip install -r requirements.txt -r tests/test_requirements.txt

export GROQ_API_KEY=test_groq_key
export JWT_SECRET_KEY=test_jwt_secret
export DATABASE_URL=postgresql://codecoach:codecoach@127.0.0.1:5433/codecoach_test
export ENVIRONMENT=testing
```

Then:

```bash
python -m pytest                              # All tiers
python -m pytest tests/unit/                  # Unit tests
python -m pytest tests/integration/           # Integration tests (needs DATABASE_URL)
python -m pytest tests/contract/              # OpenAPI contract tests
python -m pytest tests/security/              # Security tests
python -m pytest tests/performance/           # Performance/load tests
python -m pytest tests/simulation/            # Skill-graph simulations (deterministic)
python -m pytest tests/migrations/            # Alembic migration tests
python -m pytest --cov=app                    # Coverage
```

Lint/format (also enforced in CI):

```bash
ruff check .
ruff format . --check
```

## Coverage and flake gates

- Coverage floors are enforced by `qa/enforce_coverage_budget.py` in CI; don't
  ship changes that drop module coverage below budget.
- Flaky tests are quarantined via `tests/enforce_flaky_quarantine.py` — a test
  that fails intermittently belongs in `flaky-quarantine.json`, not the
  committed suite.

## Environment variables

| Variable                    | Purpose                                              |
| --------------------------- | ---------------------------------------------------- |
| `DATABASE_URL`              | Postgres URL; conftest creates the isolated test schema |
| `DATABASE_SEARCH_PATH`      | Test search path (the isolated schema)               |
| `GROQ_API_KEY`              | Stubbed key for coaching tests (no live calls)       |
| `JWT_SECRET_KEY`            | Test JWT secret                                       |
| `USER_RATE_LIMIT_PER_MINUTE`| Test rate-limit override                               |
| `ENVIRONMENT=testing`       | Disables debug endpoints / strict guards              |

## Notes

- Never use blocking DB connections on the event loop — tests prefer the async
  engine/session from `app.core.database`.
- External providers (Groq, Piston, Redis) are mocked or degraded by design;
  see `tests/integration/test_external_failures.py`.
- New endpoints need: service/unit tests, integration tests, and coverage in
  `tests/contract/test_response_contracts.py`.

For general project testing info, see the [root README](../README.md).