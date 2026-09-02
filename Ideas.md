# CodeCoach AI — Ideas & Progress Tracker

> Status legend: 🔴 Not started · 🟡 Partial / foundation only · 🟢 Mostly built · ✅ Done
> Trackable with checkboxes — tick `[x]` as work lands.
> Audit date: Sep 02, 2026 (branch `feat/125-coach-skill-context-cache` — audited against code). Companion status doc: [Progress.md](./Progress.md).

This is a **closed / private** product. Defensibility therefore rides on the
product's own data and UX personality, not on an open-source community.

## Idea overview

| # | Idea | Status | Key blocker |
|---|------|--------|-------------|
| 1 | Mistake-memory moat | ✅ Done (+ learner-context shipped `f246c4a`) | No blocker — submissions + error graph + SM-2 + analytics + learner-context caching landed; backfill only |
| 2 | Segment moat | 🟡 | No professor/class dashboard |
| 3 | Forgetting-curve UI | ✅ Done | None — `/dashboard` memory graph live |
| 4 | Never-alone rescue contract | ✅ Done | None — durable queue + T1→T2→T3 live; flow-map retired to animate |
| 5 | See-how-you-think replay | 🟡 | `ProblemFlowMap` static list, not journey replay |
| 6 | Live interviewer theater | 🔴 | Needs session/event engine |
| 7 | Time-travel debugging | 🟡 | `trace_instrumenter` exists for animation only; needs generic user-code tracing |
| 8 | Reverse interview | 🔴 | Cheap — `CoachingMode.SENIOR` + prompt not yet added |
| 9 | Honourable mentions | 🔴 | Backlog |

---

## 1. The mistake-memory moat (double-down)

Without OSS, defensibility now rides on proprietary data, and this is the best
candidate:

- Persistent, per-user error graph + spaced-repetition quizzes on your own past bugs.
- Learning analytics ("recursion plateau detected") that giants won't repackage for individual students.

Why it's leverage: every session compounds switching cost. Five years of a
user's mistake-history is a moat nobody can walk into. This is the thing you
gather user data for.

### Status: ✅ Done — plus learner-context shipped (`f246c4a` Sep 02)

**Detailed explanation:** The core product promise is that every run/submit/diagnosis
a user makes is persisted per-user. From that history we derive (a) an error graph
linking questions → failing concepts → recurring error signatures, (b) a spaced-repetition
scheduler (SM-2/FSRS) that quizzes you on your _own_ past bugs, and (c) learning-analytics
signals like "recursion plateau detected." Now **unblocked**: `SubmissionORM` (`submissions` table, `d9e1f2a3b4c5`) is live, and `LearnerContextService` (`backend/app/services/learner_context_service.py`, `backend/app/core/cache_keys.py`) composes cached skill graph + recent attempts into coach prompts (`feat/125`).

**The critical gap (was):** the codebase stored completed lessons (`course_progress`),
usage events, and skill-graph learning events, but never persisted actual code attempts
— now **RESOLVED**: `submissions` + `review_cards` + `error_graph` + learner-context `f246c4a` are at head; diagnosis capture remains the only open wire (Piston `run`/`submit` already best-effort).

### Progress

- [x] Add a `submissions` schema (user_id, question_id, code, language, passed, error signature, attempt index, created_at) — `SubmissionORM` `d9e1f2a3b4c5`
- [x] Wire submission capture into `submit.py` / `run.py` (and diagnosis) — `submit.py:100` persisted + `run.py:59` `question_id` crash capture; skill-graph emission `submit.py:127` `sub:{id}`; diagnosis wire still open
- [x] Supabase repository implementation behind a `ports/` interface (match the `sql_*` pattern) — `SqlSubmissionRepository` via `app/ports/submission_repository.py`
- [x] Derive per-user error graph from attempt history (`GET /api/mistakes/graph`)
- [x] Spaced-repetition scheduler producing review sessions from own past bugs (SM-2, `/api/reviews/*`)
- [x] Learning-analytics signals ("recursion plateau detected")
- [x] Learner-aware coaching (shipped `f246c4a`): `LearnerContextService` + `cache_keys.py` + `PromptBuilder` injection + `submit`/`skills` invalidation + `MainWorkspace` full description + `learner-context-invalidated` refresh
- [ ] Backfill/adopt for existing questions where feasible

### Next steps

1. ~~Design the attempt-history schema~~ — DONE (`submissions`)
2. Wire diagnosis capture (last open)
3. ~~Build the error-graph derivation~~ — DONE (Aug 24)
4. ~~Build the spaced-repetition review endpoint~~ — DONE (Aug 24); frontend review UI is the follow-up

---

## 2. Own the whitespace giants ignore → a segment moat

Closed-source lets you be ruthlessly niche without community backlash:

- The first-30-days student (tutorial → first-interview brain, not interview grinders).
- Non-CS majors and underrepresented beginners — no one serves them well.
- A specific university ecosystem via curriculum-aligned courses + a professor dashboard (one professor = a whole class).

Why it's leverage: giants fight for the crowded middle (interview grinders).
Owning one underserved segment makes you the default, not a choice.

### Status: 🟡 Partial — curriculum exists, no professor ecosystem

**Detailed explanation:** The curriculum half is built: Python Fundamentals —
modules, lessons, progress tracking, exercises, `/learn`. The segment-moat half
is not: there is no professor/class dashboard, no roster/classroom model, and no
first-30-days onboarding funnel. The "one professor = a whole class" flywheel
needs a teaching view.

### Progress

- [x] Curriculum: Python Fundamentals — 5 modules / 36 lessons (21 theory + 15 exercises)
- [x] `/learn` dashboard, `/[courseId]` module tree, `/lesson/[lessonId]` viewer + adjacent navigation
- [x] Progress tracking (completed lessons, continue-where-you-left-off)
- [x] Curriculum content pipeline (database is the single source of truth; `sync_local_to_db.py` idempotent bootstrap)
- [ ] First-30-days onboarding funnel (tutorial → first-interview brain)
- [ ] Non-CS / underrepresented-beginner content persona
- [ ] Professor dashboard (class roster, per-class progress, assignment view)
- [ ] Class/roster data model (course-level, not per-user)

### Next steps

1. Define the class/roster data model
2. Professor dashboard (reads existing course + progress data, class-level views)
3. Onboarding funnel for the first-30-days segment

---

## 3. Make the entire UI the forgetting curve (not just a quiz feature)

Your mistake-memory moat is currently a feature. Weaponize it: rebuild the
dashboard so every screen is organized around what you're about to forget, not
problem lists.

- "⚠️ You're at 6 days since touching recursion — 5-min refresher now, or you relearn it in 30 min later."
- The home page is your memory graph. Physics: spaced repetition + energy-cost ("intervene in 5 min to save 30").

Why it's a moat: nobody does this. Giants are content repositories; you'd be the
first memory-first coding platform. It makes your mistake-data the literal
skeleton of the product — impossible to copy without rebuilding their whole UX.

### Status: ✅ Done — memory graph dashboard landed (Aug 24, 2026), verified Sep 02

**Detailed explanation:** The home page (and every screen) should be organized
around _what you're about to forget_. Every card is a "days since you touched X"
decision powered by the #1 scheduler. Now built on the #1 SM-2 data layer:
`MemoryGraphService` aggregates review cards + submissions by `category` into
`GET /api/memory/graph`, and `MemoryGraph.tsx` + `/dashboard` render the per-topic
energy-cost view ("6 days since recursion — 5-min refresher").

### Progress

- [x] Student home page as memory graph ("6 days since recursion — 5-min refresher now")
- [x] Per-topic last-touched + energy-cost copy ("intervene in 5 min to save 30")
- [x] Review queue surfaced on every screen (MemoryGraph + ReviewsDueQueue on `/dashboard`; ReviewsDueQueue + RescueDueQueue on `/problems`)
- [x] Student `/dashboard` route

### Next steps

1. ~~Land #1's scheduler first~~ — DONE
2. ~~Design the memory-graph dashboard~~ — DONE
3. ~~Ship one "due now" review card~~ — DONE (`ReviewsDueQueue`)

---

## 4. The "never-alone" rescue contract (abandonment intervention)

Churn's #1 killer isn't difficulty — it's silent giving-up. Promise (and honor)
a contract:

- If a user is "stuck" past X min, AI auto-intervenes with escalating scaffolds and
  never leaves you alone with failure for more than Y minutes — until you either
  pass or the AI personally re-plans your path.
- Every abandoned problem is captured and resurfaces tomorrow as a tiny step (no-loss economy).

Why it's out-of-the-box + sticky: it's a UX personality giant can't copy, great
for the beginner segment, low churn = compounding retention.

### Status: ✅ Done — re-surface loop + time-based escalation landed (Aug 24, 2026), verified Sep 02 — flow-map retired to animate

**Detailed explanation:** The intervention half is implemented: `RescueIntervention` +
`ProblemFlowMap` (static checkpoint list, `frontend/src/components/rescue/ProblemFlowMap.tsx` via `rescue.checkpoints.ts`), `use-rescue-contract` hook
(`frontend/src/features/rescue/use-rescue-contract.hook.ts`). The former AI `SolutionFlowMap`/`FlowMapService` (ReactFlow + `flow_map_*` `backend/` files, `GET /questions/{id}/flow-map`) was **removed** and replaced by the canonical **Animate** pipeline (`SolutionAnimationService` + `trace_instrumenter`/`trace_parser` + `AnimationScript`, `POST /api/coach/animate`). The "every abandoned problem
resurfaces tomorrow as a tiny step" half is **built**: durable server-side queue
(`rescue_queue` table `f2a3b4c5d6e7` + `/api/rescue/*` `rescue.py`) schedules tomorrow-09:00
resurfacing, survives reloads, honors dismissals permanently. Diagnosis uses deterministic fallback (no backend flow-map API — checkpoints are frontend-local).

### Progress

- [x] Rescue contract hook (`use-rescue-contract.hook.ts`)
- [x] `RescueIntervention` + `ProblemFlowMap` (checkpoint list via `rescue.checkpoints.ts`; former `SolutionFlowMap`/ReactFlow removed, now `animate` via `AnimationScript`)
- [x] Flow-map rendering: static checkpoint list (no backend `flow-map` API; `ProblemFlowMap` is UI-only; AI flow maps replaced by `POST /api/coach/animate`)
- [x] Submission diagnosis service (deterministic outline)
- [x] Capture abandoned problems (durable: `POST /api/rescue/{id}/abandon`; localStorage kept as offline fallback `rescue.storage.ts`)
- [x] Re-surface queue: tomorrow's tiny step for every abandoned problem (`GET /api/rescue/due`, "Back tomorrow" section on `/problems`)
- [x] Time-based stuck escalation (X min → scaffold, Y min → re-plan) — `useRescueContract` now fires `onEscalateToT2`/`onEscalateToT3` once per tier, wired to AI coach `explain`/`review` messages + drawer open

### Next steps

1. ~~Persist abandoned sessions~~ — DONE (rides #1 `submissions`)
2. ~~Add the daily re-surface queue endpoint + UI~~ — DONE

---

## 5. "See how you think" — replay of your own attempt-journey

After you solve a problem, AI renders an animated map of your process: every
attempt, where you errored, what you almost got, how your code evolved.

- It's metacognition as product — "watch how you debugged." Deeply personal, emotionally resonant, zero competition.

Why it's a moat: it needs your full attempt-history (the data you're already
gathering for idea #1), and it makes users look back at themselves — rare and
addictive. Nobody else can show you your brain.

### Status: 🟡 Partial — per-solve `ProblemFlowMap` static list, not journey replay — code-audited Sep 02

**Detailed explanation:** The flow-map feature (`frontend/src/components/rescue/ProblemFlowMap.tsx`,
static checkpoint list, plus `frontend/src/components/visualization/` for animations) shows a checkpoint map
for a single solve. It is **not** a replay of the user's _attempt journey_ (every
attempt, where they errored, how their code evolved). `submissions` history is now persisted (#1 done), so the data layer is unblocked — the renderer/timeline is still missing. Former AI flow-map was retired to `animate`.

### Progress

- [x] Flow-map checkpoint list (`ProblemFlowMap.tsx`) + rescue checkpoints (`rescue.checkpoints.ts`)
- [x] Animation visualization infra (`AnimationPlayer.tsx`, `AnimationScriptRenderer.tsx`) for canonical solutions only
- [x] AI diagnosis of a submission (deterministic fallback)
- [x] Persist full attempt journey per problem — **unblocked** (`submissions` now live, needs journey query)
- [ ] Animated replay timeline over the stored journey
- [ ] "Where you errored / what you almost got" highlights

### Next steps

1. ~~Blocked on #1's attempt-history layer~~ — UNBLOCKED Sep 02
2. Build animated replay timeline reusing `submissions` + `ProblemFlowMap` + `AnimationPlayer`

---

## 6. Live interviewer theater — the product is a person, not a problem list

Don't present a problem page — present an AI interviewer who reacts to your code
while you type: interrupts ("why did you choose a hashmap?"), changes requirements
mid-solve ("now it must handle a stream of 10M rows"), throws a curveball on your
answer. Fail = the interviewer "loses interest."

- A private, on-demand mock interview with a personality. The whole industry is problem repositories; this is a performance medium.
- Cold-start: zero user history needed — runs on day one. Rides the existing SSE streaming coach (`POST /coach/stream`) + debounced Monaco snapshots.

Why it's a moat: a UX personality and a live-reaction paradigm can't be copied by
adding database tables. Immersive, shareable, high retention.

### Status: 🔴 Not started — streaming foundation exists

**Detailed explanation:** The key foundation already exists: the backend streams
AI coaching via SSE (`POST /coach/stream` in `backend/app/api/coach.py`), the
frontend consumes it via `coaching.service.ts` / `coaching.hook.ts`, and the
editor (`CodeEditor.tsx`, Monaco) can emit change events. What's missing is the
_session engine_: a per-session interviewer state machine (attempts, last code
snapshot, curveball cursor, persona mood) that reacts to editor debounce +
run/pass events and pushes structured `CoachEvent`s (probe / interrupt /
requirement_change / reveal / escalate) over the stream. Cold-start-first — no
history required.

### Progress

- [x] SSE streaming coach endpoint (`POST /coach/stream`)
- [x] Frontend streaming consumption (`coaching.service.ts` / `coaching.hook.ts`)
- [x] Monaco editor change events (debounce hookup needed)
- [ ] Interview session schema + event union (`probe`/`interrupt`/`requirement_change`/`reveal`/`escalate`)
- [ ] `InterviewSessionService` (per-session state machine, deterministic for tests)
- [ ] `POST /interview/{question_id}/session` + `POST /interview/{question_id}/events`
- [ ] Trigger rules: silence + failed runs → interrupt/escalate; requirement mutation mid-solve
- [ ] `InterviewTheater` UI wrapping `MainWorkspace.tsx` (interviewer dock, requirement banner)

### Next steps

1. Build the shared persona/event layer (also powers #8)
2. Add session + events endpoints
3. Ship the theater UI on the streaming coach

---

## 7. Time-travel debugging as the teaching layer

Let students scrub backward and forward through their own execution — pointer
position, variables mutating, the exact frame where a value went wrong.

- Time-travel debugging (rr, Chrome DevTools) is the hottest debugging paradigm of the decade; nobody has packaged it for learners.
- Cold-start: request-scoped. Piston has no step/trace support, so build an AST-instrumented tracing executor (Python via `ast`, JS via transform) that injects `trace(scope)` calls, runs in the existing sandbox, and returns a scrubbable trace timeline.
- Tie into the existing flow-map/diagnosis/AND animation visualization.

Why it's a moat: genuinely modern technology, not a gamification skin — it makes
"watch the bug happen" possible. Self-contained and demo-able with zero user data.

### Status: 🟡 Partial — canonical tracing only (Sep 02 audit)

**Detailed explanation:** Piston (`piston_service.py`) is stdout/exit-code only —
it has **no step/trace support**. Canonical-solution tracing **is** built for animations:
`backend/app/services/trace_instrumenter.py:35` `wrap_traced_solution` injects `__trace` helper + JSON-array dump, `trace_parser.py:112` `parse_trace` normalizes `init`/`compare`/`swap`/`pointer`/`mark`/…/`return` events, `SolutionAnimationService` compiles them into `AnimationScript` for `GET /api/coach/animate`. **Missing:** generic AST-instrumented tracing of the *student's* code (Python `ast` + JS transform) producing a scrubbable `TraceTimeline` (`TraceStep`/`TraceFrame` schemas, `POST /trace`), plus `TimelineScrubber` (play/pause, var inspector) and line-highlight overlay on `CodeEditor.tsx`. Former AI flow-map is now animate.

### Progress

- [x] Canonical-solution tracing for animation: `trace_instrumenter.py` (`__trace` + `_dump_trace`) + `trace_parser.py` (`TraceEvent`, `parse_trace`) + `SolutionAnimationService` (`POST /api/coach/animate` fallback)
- [ ] AST instrumentation for student Python (`ast` rewrite → `trace(scope)`)
- [ ] AST/transform instrumentation for JavaScript
- [ ] `TracingExecutor` port + service running instrumented *student* code in sandbox
- [ ] `TraceStep` / `TraceFrame` / `TraceTimeline` schemas + `POST /trace`
- [ ] `TimelineScrubber` component (play/pause, scrub, var inspector)
- [ ] Line-highlight overlay on `CodeEditor.tsx`
- [ ] Integrate with flow-map / diagnosis / animation visualization

### Next steps

1. Prove AST instrumentation on the 3 seed languages with round-trip fidelity
2. Return a trace timeline from a `/trace` endpoint
3. Build the scrubber UI

---

## 8. Reverse interview — you are the senior - Next up

After solving, the AI becomes your confused junior dev, and you must explain and
defend your code line-by-line as if onboarding them. When you hand-wave, it asks
follow-ups until you've taught it.

- Feynman technique as roleplay: answering is the fastest way to learn; the junior forces completeness.
- Cold-start: zero data, reuses existing `explain`/`review` coaching modes with a new `senior` persona + prompt template.

Why it's leverage: cheap to ship first (no realtime needed) and it validates the
shared persona engine that powers ideas #6 and #7.

### Status: 🔴 Not started — cheapest genuinely-new win

**Detailed explanation:** `CoachingMode` (`backend/app/models/schemas.py`) already
has hint/review/explain/debug/freeform/animate. This adds a `senior` mode where the
AI role-plays a confused junior dev: you explain your code line-by-line, it asks
follow-ups when you hand-wave, and it tracks "do I understand now?" It's mostly a
prompt template + a mode toggle in the AI coaching pane — no realtime, no new
infra. Cheap, and it validates the persona engine that #6 and #7 reuse.

### Progress

- [ ] New `CoachingMode.SENIOR` in `schemas.py`
- [ ] Junior-dev persona prompt in `coaching_prompts.py` (asks follow-ups on hand-waving)
- [ ] Mode picker in the AI coaching pane
- [ ] Prompt-persona + endpoint tests

### Next steps

1. Add the `senior` persona prompt + mode
2. Wire the mode picker in the AI Coach pane
3. Test; then reuse the persona layer for #6

---

## 9. Honourable mentions (kept from the brainstorm)

- The takeover: the AI writes the worst-possible, technically-valid solution and you refactor it to pass — learn to read bad code like a senior.
- Adversarial twin: a second AI instance attacks your solution with a visible "attack log" (`[twin] tried input [5,1,5,1] → wrong answer`); you defend by patching.
- Talk-it-out contract: you speak your plan ("I'll use a sliding window, O(n)"), the AI pins it on screen and holds you to it when your code contradicts your mouth.
- Failure-velocity score: a metric rewarding HOW you try (quick failed attempts → correctly diagnosed), reframing slow beginners as great learners.
- One-line takeaway + prove-it: the AI freezes the one-sentence takeaway you learned; a retrieval quiz later proves you actually learned it.
- Error-signature whitelist: anonymous aggregate "3800 people hit this exact IndexError; 71% fixed it with one line" — GDPR-safe, works on aggregate data.
- Privacy-first session diffs: record your session as a diff (struggle → insight → solve) that's ephemeral by default, opt-in to keep — turns data collection into a psychological unlock.
- Serialized episodes: each DSA topic is an ongoing story where your code choices change the narrative.
- Voice-driven mentor persona: a session-aware coaching pane that argues against your overconfidence.

### Status: 🔴 Backlog — none started

**Detailed explanation:** These were captured from the brainstorm to avoid losing
them. Several are cheap re-skins of existing infrastructure (adversarial twin and
the takeover reuse Piston + coaching modes; failure-velocity reuses the attempt
data from #1; one-line takeaway reuses coaching modes). They get promoted to
numbered ideas when chosen.

### Progress

- [ ] Adversarial twin (attack log over existing diagnosis) — cheap, builds on #6's persona engine
- [ ] The takeover (review-first pedagogy, reuses `review` mode)
- [ ] Failure-velocity score (needs #1's attempt data)
- [ ] One-line takeaway + prove-it (retrieval quiz, partial dependence on #1)
- [ ] Talk-it-out contract (needs speech-to-text)
- [ ] Error-signature whitelist (needs aggregate data + privacy design)
- [ ] Privacy-first session diffs (opt-in collection model)
- [ ] Serialized episodes (content pipeline work)
- [ ] Voice-driven mentor persona (needs speech infra)

### Next steps

1. Promote chosen items to numbered ideas
2. Cheapest first: adversarial twin and the takeover (no new data needed)

---

## Suggested execution order (updated Sep 02 — code-audited)

1. **#8 Reverse interview** — smallest effort, validates the persona engine (`CoachingMode.SENIOR`, `coaching_prompts.py` junior persona, mode picker) — cheapest genuinely-new win
2. **#6 Live interviewer theater** — flagship, rides existing SSE (`POST /coach/stream`) + persona engine from #8
3. **#5 Attempt-journey replay** — now **unblocked** by #1 `submissions` (audited Sep 02); animate with existing `ProblemFlowMap` + `AnimationPlayer`
4. **#7 Time-travel debugging — student-code path** — canonical trace done; add generic `TracingExecutor` + `POST /trace` + `TimelineScrubber`
5. **#2 professor dashboard** — define `class`/`roster` model + class-level views (reads existing `course_progress`)
6. **#1 residual** — diagnosis capture
7. **#9 Honourable mentions** — promote after #8: adversarial twin / takeover (cheap, no data)
