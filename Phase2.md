# Phase 2 — Programming Language Curricula (Plan)

## Overview

Phase 2 adds structured language learning paths for C, Python, and Java — each with ~15–20 interleaved theory lessons and coding exercises. Context-aware AI coaching adapts hints/reviews to the current lesson topic.

---

## 1. Data Model & Storage

### New Entities
- **Course** — A language track (e.g., "Python Fundamentals"). Fields: `id`, `title`, `description`, `language`, `difficulty`, `icon`, `order`
- **Module** — A unit within a course (e.g., "Control Flow"). Fields: `id`, `course_id`, `title`, `order`
- **Lesson** — Theory or exercise within a module. Fields: `id`, `module_id`, `title`, `type` (theory | exercise), `content` (markdown body), `order`, `starter_code`, `test_cases`

### User Progress
- Extend `UserInDB` or create a `UserProgress` collection tracking:
  - `completed_lessons: list[lesson_id]`
  - `course_progress: { course_id: percentage }`
  - `exercise_scores: { lesson_id: score }`

### Storage
- JSON file-backed collections (same pattern as Phase 1 questions): `courses.json`, `modules.json`, `lessons.json`, `user_progress.json`

---

## 2. Backend (FastAPI) Extensions

### Course APIs
- `GET /api/courses` — list all courses with progress for authenticated user
- `GET /api/courses/{id}` — course detail with module/lesson tree
- `GET /api/lessons/{id}` — single lesson content

### Progress APIs
- `POST /api/progress/lesson/{id}/complete` — mark theory lesson as read
- `POST /api/progress/lesson/{id}/submit` — submit exercise code for grading
- `GET /api/progress/courses` — get progress for all enrolled courses

### Context-Aware AI Coaching
- Augment the existing coaching endpoint with a `lesson_context` field
- Inject lesson metadata into the NVIDIA NIM prompt (e.g., *"The user is on Python Lesson 4: For Loops. Restrict hints to for-loop syntax only."*)
- Rate limit: 10 requests/min (shared with Phase 1)

---

## 3. Frontend (React) Additions

### New Route
- `/learn` — main curriculum dashboard showing available courses and progress

### Lesson UI
- **Theory Lessons**: Markdown-rendered content on the left with next/prev navigation
- **Exercise Lessons**: Theory/instructions on the left, Monaco editor + AI Coach on the right (reuse Phase 1 workspace components)
- Progress indicators: checkmarks, progress bars, visual path through modules

### Navigation Updates
- Header adds a "Learn" link (between existing nav items)
- `/learn` is accessible to all users; progress tracked per authenticated user

---

## 4. Content Generation

### Curriculum Script
- `backend/scripts/generate_curriculum.py` — generates lessons per language via NVIDIA NIM
- Each language gets:
  - ~8 theory lessons (syntax, data types, control flow, functions, pointers/references, structs/classes, file I/O, standard library)
  - ~10–12 coding exercises per language
- Quality gate adapted from Phase 1: 3-round evaluation on clarity, correctness, pedagogical value

### Content Outline Per Language

| Language | Theory Lessons | Coding Exercises | Total |
|---|---|---|---|
| C | 8 | 12 | 20 |
| Python | 8 | 12 | 20 |
| Java | 8 | 12 | 20 |

---

## 5. Implementation Order

| Step | Description | Dependencies |
|---|---|---|
| 1 | Create data models and JSON storage backends | None |
| 2 | Build Course/Module/Lesson CRUD APIs | Step 1 |
| 3 | Build progress tracking APIs | Step 1 |
| 4 | Create `/learn` frontend dashboard | Step 2 |
| 5 | Build lesson viewer (theory + exercise views) | Steps 2, 4 |
| 6 | Wire exercise submission into existing Run/Submit pipeline | Steps 3, 5 |
| 7 | Inject lesson context into AI coaching prompts | Step 6 |
| 8 | Build and run curriculum generation script | Step 1 |
| 9 | Quality-gate and populate generated lessons | Step 8 |
| 10 | End-to-end testing and polish | All above |

---

## 6. Success Criteria

- All 3 courses (C, Python, Java) fully populated with ~20 lessons each
- Users can navigate from course listing → module → lesson without dead ends
- AI coaching respects lesson context (no off-topic hints)
- Exercise code submissions grade correctly against lesson test cases
- Progress persists across sessions and reflects accurately on dashboard
