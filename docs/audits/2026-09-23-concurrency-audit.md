# Concurrency Audit — Classroom Data Under Parallel Users (Issue #295)

**Date:** 2026-09-23
**Auditor:** automated agent session (Playwright MCP + chrome-devtools MCP + OTEL)
**Branch:** `test/295-concurrency-audit`
**Parent:** full-product audit — #294
**Verdict:** reads stay consistent and the stampede lock holds, but **concurrent submissions from the same user corrupt skill state (lost updates)** — 1 high-severity defect.

**Scope boundary:** correctness under concurrency (lost updates, double-counts, cache
stampede, isolation) — **not** capacity/load benchmarking.

---

## 1. Environment & isolation

| Component | Value |
| --- | --- |
| Branch DB | `codecoach_295_concurrency_audit` (separate from #294's DB) |
| Redis | **DB 1** (`redis://localhost:6379/1`) — isolated from #294's DB 0 |
| Backend | FastAPI/uvicorn `http://localhost:8001` |
| Frontend | Next.js dev `http://localhost:3020` (`API_URL=http://localhost:8001`) |
| Code execution | Piston `http://localhost:2000/api/v2` |
| Tracing | OTEL enabled → same OTLP receiver on `:4318` |
| Seed | `seed_e2e.py` + `seed_classroom_demo.py` (15 students, 2 classrooms, 19 enrollments) + `seed_skill_graph.py` |

---

## 2. Protocol

### Wave A — browser-realistic, concurrent sessions

| Session | Browser profile | Activity |
| --- | --- | --- |
| Student `mia` | Playwright MCP | login → `/problems/two-sum` → run + submit ×3 |
| Professor `professor.ada` | chrome-devtools (isolated context) | `/professor/analytics` reloaded ×4 during the submits |

**Ruling:** the issue's topology named a third browser (the `browser` tool) for the TA.
That tool requires the OpenCode desktop app and was **not connected** in this
environment, so Wave A ran **two** independent profiles instead of three. TA analytics
is covered functionally in #294 (both sections, scope enforced); its concurrency
exposure is identical to the professor's read path, which this wave exercises.
Cost if wrong: a third-profile-specific timing issue would be missed.

### Wave B — amplified parallel HTTP (where races actually hide)

`httpx.AsyncClient` + `asyncio.gather` against `:8001`, script `/tmp/opencode/wave_b.py`.

---

## 3. Results

### Invariants

| Invariant | Result | Evidence |
| --- | --- | --- |
| No lost **writes** (submissions persisted) | ✅ PASS | 12 concurrent → 12 rows; 22 total for `mia` |
| No lost **updates** (skill state) | ❌ **FAIL** | see C1 |
| No cross-user interference | ✅ PASS | 8 concurrent distinct users → each exactly 1/1 |
| Stampede lock held | ✅ PASS | 30 concurrent cold GETs → `courses` seq_scan **+1** |
| Invalidation convergence | ✅ PASS | PUT 200 → cache key deleted (`ttl=-2`) |
| Isolation intact | ✅ PASS | plain student → instructor API `403`; enrollments 19→19 |
| Zero 5xx under load | ✅ PASS | backend log: 0 five-hundreds; 25/25 mixed read/write = 200 |

### Wave A (2 concurrent browser sessions)

- Student `mia`: `run0:pass,run1:pass,run2:pass`
- Professor: `reload0:ok,reload1:ok,reload2:ok,reload3:ok` (no errors beyond the expected anonymous 401 probe)
- Screenshots: `.playwright-mcp/audit/j295-a1-student.png`, plus chrome-devtools professor capture

### Wave B numbers

| Scenario | Requests | HTTP | Observed |
| --- | --- | --- | --- |
| same_user (12× `mia`) | 12 | all 200 | 12 submissions, 12 events, **skill evidence 5/3 (should be 12/12)** |
| sequential control (`ava`, 3×) | 3 | all 200 | skill evidence **3/3 — correct** |
| distinct_users (8 students) | 8 | all 200 | each user exactly **1/1 — correct** |
| mixed read/write (20 reads + 5 writes) | 25 | all 200 | zero 5xx |
| duplicate (3 identical `ivy`) | 3 | all 200 | 3 attempt rows (attempt-history semantics; client dedupes) |
| stampede (30 cold GETs) | 30 | all 200 | `courses` seq_scan +1 |

### Read consistency

`GET /api/instructor/classrooms-analytics` matched the DB exactly after the waves
(`mia`: attempted 22 / solved 22; `avg_solved 4.0`). The read/aggregate path is correct —
the defect is confined to the skill-state write path.

---

## 4. Finding

### C1 — Concurrent submissions from the same user lose skill-state updates — **High** — #301

- **Where:** `backend/app/services/skill_graph_service.py::ingest_events` (per event:
  `get_states()` → `apply_event()` → `save_state()`), persisted by
  `backend/app/repositories/sql_skill_graph_repository.py::save_state` (SELECT then
  UPDATE). No row lock, no atomic `evidence_count = evidence_count + 1`, no
  transaction spanning the read-modify-write.
- **Behaviour:** 12 concurrent submissions by one user → 12 submission rows and 12
  learning events, but `user_skill_states.evidence_count` ended at **arrays=5,
  hash-maps=3** (expected 12/12). After the full run, `mia` had **22** passed
  submissions but only **arrays=12, hash-maps=9** evidence — a persistent undercount
  of mastery/evidence.
- **Control proving it is a race (not a cap):** the same action **sequentially**
  (`ava`, 3×) yields exactly 3/3.
- **Impact:** concurrent activity (double-taps, multiple tabs, retries, class-wide
  bursts) silently corrupts each learner's skill graph → wrong mastery, wrong
  "what's next", wrong analytics/coaching signals. Data integrity, not just UX.
- **Repro:**
  1. Login as a student; POST `/api/submit/` for `two-sum` with passing code.
  2. Fire N concurrent identical requests.
  3. Compare `submissions` count (N) with `user_skill_states.evidence_count` (< N).
- **Evidence:** `/tmp/opencode/wave_b.py`; DB queries in this report; OTEL spans on `:4318`.

---

## 5. Non-findings (verified good)

- Submissions are never lost (row-per-attempt).
- Distinct users do not interfere with each other's state.
- Analytics reads are consistent with the DB and do not 5xx while writes are in flight.
- The anonymous course-list stampede lock and write-invalidation both hold.
- Role isolation is enforced (403), and seeded classroom data was not altered.

## 6. Limitations

- Wave A used **two** browser profiles (see ruling) — the third (`browser` tool) was unavailable.
- Duplicate-retry behaviour is attempt-history semantics; server-side idempotency was
  not in scope and the client already de-duplicates double submits.
- No load/capacity benchmarking (out of scope).
