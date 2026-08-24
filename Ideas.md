# CodeCoach AI — Ideas & Progress Tracker

> Status legend: 🔴 Not started · 🟡 Partial / foundation only · 🟢 Mostly built · ✅ Done
> Trackable with checkboxes — tick `[x]` as work lands.
> Audit date: Aug 14, 2026. Status reflects work merged to `main` / the current
> `feat/skill-graph-recommendations` branch. Companion status doc: [Progress.md](./Progress.md).

This is a **closed / private** product. Defensibility therefore rides on the
product's own data and UX personality, not on an open-source community.

## Idea overview

| # | Idea | Status | Key blocker |
|---|------|--------|-------------|
| 1 | Mistake-memory moat | 🔴 | No attempt-history persistence |
| 2 | Segment moat | 🟡 | No professor/class dashboard |
| 3 | Forgetting-curve UI | 🔴 | Depends on #1 |
| 4 | Never-alone rescue contract | 🟢 | Missing re-surface loop |
| 5 | See-how-you-think replay | 🟡 | Flow-map is per-solve, not journey replay |
| 6 | Live interviewer theater | 🔴 | Needs session/event engine |
| 7 | Time-travel debugging | 🔴 | Needs tracing executor |
| 8 | Reverse interview | 🔴 | Cheap — reuses coaching modes |
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

### Status: ✅ Done — plateau signals landed (Aug 24): GET /api/analytics/signals over bounded recent submissions (1000), LearningSignals banner on /dashboard

**Detailed explanation:** The core product promise is that every run/submit/diagnosis
a user makes is persisted per-user. From that history we derive (a) an error graph
linking questions → failing concepts → recurring error signatures, (b) a spaced-repetition
scheduler (SM-2/FSRS) that quizzes you on your _own_ past bugs, and (c) learning-analytics
signals like "recursion plateau detected."

**The critical gap:** the codebase stores completed lessons (`course_progress`),
usage events, and skill-graph learning events, but **never persists a user's actual
code attempts**. There is no `submissions` / attempt-history table and no per-attempt
error log. Without this data layer, ideas #3 and #5 are also blocked.

### Progress

- [ ] Add a `submissions` schema (user_id, question_id, code, language, passed, error signature, attempt index, created_at)
- [ ] Wire submission capture into `submit.py` / `run.py` (and diagnosis)
- [ ] Supabase repository implementation behind a `ports/` interface (match the `sql_*` pattern)
- [x] Derive per-user error graph from attempt history (`GET /api/mistakes/graph`)
- [x] Spaced-repetition scheduler producing review sessions from own past bugs (SM-2, `/api/reviews/*`)
- [x] Learning-analytics signals ("recursion plateau detected")
- [ ] Backfill/adopt for existing questions where feasible

### Next steps

1. ~~Design the attempt-history schema~~ — DONE (`submissions`)
2. Capture on every Piston run and AI diagnosis (run.py / diagnosis capture still open)
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

### Status: 🟢 Mostly built — memory graph dashboard landed (Aug 24, 2026)

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

1. Land #1's scheduler first (this is a pure UI on top)
2. Design the memory-graph dashboard
3. Ship one "due now" review card on the existing home page as a first slice

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

### Status: ✅ Done — re-surface loop + time-based escalation landed (Aug 24, 2026)

**Detailed explanation:** The intervention half is implemented: `RescueIntervention` /
`ProblemFlowMap` / `SolutionFlowMap` components, `use-rescue-contract` hook,
backend flow-map API (`GET /questions/{id}/flow-map`, regenerate), and diagnosis
with AI fallback to a deterministic outline. The "every abandoned problem
resurfaces tomorrow as a tiny step" half is now **built**: a durable server-side
queue (`rescue_queue` table + `/api/rescue/*`) schedules tomorrow-09:00
resurfacing, survives reloads, and honors dismissals permanently.

### Progress

- [x] Rescue contract hook (`use-rescue-contract.hook.ts`)
- [x] `RescueIntervention` + `ProblemFlowMap` / `SolutionFlowMap` components
- [x] Flow-map API: lazy fetch-or-generate + regenerate, 503 fallback to deterministic outline
- [x] Submission diagnosis service (AI diagnosis, blueprint labels)
- [x] Capture abandoned problems (durable: `POST /api/rescue/{id}/abandon`; localStorage kept as offline fallback)
- [x] Re-surface queue: tomorrow's tiny step for every abandoned problem (`GET /api/rescue/due`, "Back tomorrow" section on `/problems`)
- [x] Time-based stuck escalation (X min → scaffold, Y min → re-plan) — `useRescueContract` now fires `onEscalateToT2`/`onEscalateToT3` once per tier, wired to AI coach `explain`/`review` messages + drawer open

### Next steps

1. Persist abandoned sessions (rides #1's attempt layer)
2. Add the daily re-surface queue endpoint + UI

---

## 5. "See how you think" — replay of your own attempt-journey

After you solve a problem, AI renders an animated map of your process: every
attempt, where you errored, what you almost got, how your code evolved.

- It's metacognition as product — "watch how you debugged." Deeply personal, emotionally resonant, zero competition.

Why it's a moat: it needs your full attempt-history (the data you're already
gathering for idea #1), and it makes users look back at themselves — rare and
addictive. Nobody else can show you your brain.

### Status: 🟡 Partial — per-solve flow map only, not journey replay

**Detailed explanation:** The flow-map feature (`frontend/src/features/flow-map/`,
ReactFlow rendering, layout, status, export) shows an AI-rendered solution map
for a single solve. It is **not** a replay of the user's _attempt journey_ (every
attempt, where they errored, how their code evolved). That replay is entirely
dependent on #1's attempt-history persistence — the flow-map infra is the
rendering layer we'd reuse.

### Progress

- [x] Flow-map generation (lazy fetch-or-generate, regenerate)
- [x] ReactFlow renderer + layout + status + export
- [x] AI diagnosis of a submission
- [ ] Persist full attempt journey per problem (needs #1)
- [ ] Animated replay timeline over the stored journey
- [ ] "Where you errored / what you almost got" highlights

### Next steps

1. Blocked on #1's attempt-history layer
2. Reuse the flow-map renderer to animate the journey replay

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

### Status: 🔴 Not started

**Detailed explanation:** Piston (`piston_service.py`) is stdout/exit-code only —
it has **no step/trace support**. So this needs a new `tracing_executor` that
AST-rewrites user code to inject `trace(scope)` calls (Python via `ast`, JS via
a small transform), runs the instrumented program in the existing sandbox, and
returns a `TraceTimeline` (line, vars, call stack, memory delta per step).
Frontend gets a `TimelineScrubber` (play/pause, forward/back, var inspector)
rendered over the editor, reusing flow-map ReactFlow renderers. Largest
engineering cost of the whole doc; request-scoped, zero data needed.

### Progress

- [ ] AST instrumentation for Python (`ast` rewrite → `trace(scope)`)
- [ ] AST/transform instrumentation for JavaScript
- [ ] `TracingExecutor` port + service running instrumented code in sandbox
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

## Suggested execution order

1. **#8 Reverse interview** — smallest effort, validates the persona engine
2. **#6 Live interviewer theater** — flagship, rides existing SSE + persona engine
3. **#1 Attempt-history + mistake memory** — unblocks #3 and #5; the compounding moat
4. **#7 Time-travel debugging** — largest cost, self-contained
5. **#3 / #5** — consume #1's data once it lands
6. **#2 professor dashboard / #4 re-surface loop** — segment + retention completions