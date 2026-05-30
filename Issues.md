# Issues Log

## 🟠 I1 — Mark Complete sends wrong URL + missing `course_id`

**Priority:** Critical  
**Component:** Learn Modules Fetching (Lesson Page)  
**Status:** Open  

### Description

The "Mark Complete" button on the lesson page and the auto-complete on successful code submission both fail silently. The frontend posts to a non-existent URL, and even if the URL were correct, the required `course_id` query parameter is missing.

### Root Cause

**Frontend** (`frontend/src/app/learn/lesson/[lessonId]/page.tsx:100`):
```typescript
await api.post(`/api/progress/complete`, { lesson_id: lesson.id });
```
Sends `POST /api/progress/complete` with JSON body `{ lesson_id: "..." }`.

**Backend** (`backend/app/api/progress.py:47-48`):
```python
@router.post("/{lesson_id}/complete")
async def mark_lesson_complete(
    lesson_id: str,
    course_id: str,  # query param, required
    ...
```
Expects `POST /api/progress/{lesson_id}/complete?course_id=...`.

Two mismatches:
1. Wrong URL path — frontend omits `{lesson_id}` from the path
2. Missing `course_id` query parameter — backend validates `lesson.course_id != course_id`

### Fix

Change `handleMarkComplete` at `page.tsx:100`:
```typescript
await api.post(`/api/progress/${lesson.id}/complete?course_id=${lesson.course_id}`);
```

### Test Strategy

- E2E: Click Mark Complete → assert `POST /api/progress/{id}/complete?course_id={course_id}` returns 200
- E2E: Submit exercise with all tests passing → assert auto-complete fires correctly
- Integration: `POST /api/progress/{lesson_id}/complete?course_id=...` with valid/invalid course_id returns correct status

---

## 🟠 I2 — `isCompleted` state never loaded from backend

**Priority:** High  
**Component:** Learn Modules Fetching (Lesson Page)  
**Status:** Open  

### Description

`isCompleted` is initialized to `false` on mount and never fetched from the backend. When a user revisits an already-completed lesson:
- The Mark Complete button shows as active (not greyed out / "Completed")
- `handleSubmitCode` (L144) unconditionally calls `handleMarkComplete()` on every successful submission since `!isCompleted` is always `true`
- The button in the theory section at L299-306 shows "Mark Complete" instead of "Completed"

### Root Cause

`frontend/src/app/learn/lesson/[lessonId]/page.tsx:66`:
```typescript
const [isCompleted, setIsCompleted] = useState(false);
```
No `useEffect` to fetch progress from `GET /api/progress/{course_id}` and check if `lesson.id` is in the `completed_lessons` array.

`handleSubmitCode` (`page.tsx:144`):
```typescript
if (isAuthenticated && !isCompleted) {
  await handleMarkComplete();
}
```
Guard is always `true` → unnecessary API call on every submission for already-completed lessons.

### Fix

Add a `useEffect` after progress loads:
```typescript
useEffect(() => {
  if (!lesson || !isAuthenticated) return;
  api.get(`/api/progress/${lesson.course_id}`)
    .then((p: any) => setIsCompleted(p.completed_lessons?.includes(lesson.id) ?? false))
    .catch(() => {});
}, [lesson?.id, lesson?.course_id, isAuthenticated]);
```

### Test Strategy

- E2E: Mark lesson complete → navigate away → navigate back → assert button shows "Completed" and is disabled
- Unit: Assert `isCompleted` is `true` when `completed_lessons` includes the lesson ID

---

## 🟡 I3 — `get_optional_current_user` unreachable `None` guard

**Priority:** Medium  
**Component:** Backend Auth  
**Status:** Open  

### Description

The `get_optional_current_user` dependency is designed to allow unauthenticated access to `GET /api/courses/` by returning `None`. However, the `HTTPBearer(auto_error=True)` dependency raises `HTTPException(403)` before the function body runs, making the `if credentials is None` guard dead code. Unauthenticated users get a 403 on the course listing endpoint.

### Root Cause

**`backend/app/api/auth.py:14-15, 34-43`**:
```python
security = HTTPBearer(auto_error=True)  # raises 403 on missing/invalid header

async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserResponse | None:
    if credentials is None:  # DEAD CODE — security raises before this line
        return None
```

### Fix

Change `auto_error=False` in the `security` instantiation for the optional variant, or create a separate `security_optional = HTTPBearer(auto_error=False)`:

```python
security_optional = HTTPBearer(auto_error=False)

async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_optional),
) -> UserResponse | None:
    if credentials is None:
        return None
```

**Note:** `get_current_user` (L18-31) should keep `auto_error=True` — it requires auth.

### Test Strategy

- Integration: `GET /api/courses/` without Authorization header → assert `200` (currently gets `403`)
- Integration: `GET /api/courses/` with valid token → assert `200` with courses
- Integration: `GET /api/courses/` with invalid token → assert `200` (returns courses without progress)

---

## 🔵 I4 — `useAdjacentLessons` re-fetches entire course on every lesson page load

**Priority:** Low  
**Component:** Learn Modules Fetching (Lesson Page)  
**Status:** Open  

### Description

Every time a lesson page loads, `useAdjacentLessons` fetches the entire course (all modules + all lessons) via `GET /api/courses/{course_id}` just to determine the previous/next lesson IDs for navigation arrows.

### Root Cause

`frontend/src/app/learn/lesson/[lessonId]/page.tsx:28-52`:
```typescript
function useAdjacentLessons(lesson: LessonSummary | null) {
  // ...
  useEffect(() => {
    if (!lesson) return;
    const fetchAdjacent = async () => {
      const course = await api.get<CourseDetail>(`/api/courses/${lesson.course_id}`);
      const allLessons = course.modules.flatMap(m => m.lessons);
      // find currentIndex, set prevId/nextId
    };
    fetchAdjacent();
  }, [lesson]);
}
```

This endpoint returns nested course data including all module/lesson content, not just IDs. A lighter endpoint (e.g., returning just `{ prev_id, next_id }` given a `lesson_id`) would be more efficient.

### Fix

**Option A (lightweight):** Add a backend endpoint `GET /api/courses/lessons/{lesson_id}/adjacent` that returns `{ prev_id, next_id }` without loading the full course tree.

**Option B (immediate):** Share the course data already fetched by `useCourse` on the `[courseId]` page via context or URL params (only applicable when navigating from the course page).

### Test Strategy

- Integration: New endpoint returns correct prev/next IDs for first, middle, and last lessons
- E2E: Navigation arrows work correctly between lessons

---

## 🔵 I5 — Per-item error handling gap in `FileCourseRepository._load_file`

**Priority:** Low  
**Component:** Curriculum Data Loading  
**Status:** Open  

### Description

`FileCourseRepository._load_file` iterates over parsed JSON items and calls `model(**item)` without a try/except per item. A single malformed JSON entry (e.g., wrong type, missing required field) crashes the entire course loading process — all courses, modules, and lessons fail to load.

### Root Cause

**`backend/app/repositories/file_course_repository.py:37-38`**:
```python
for item in items:
    obj = model(**item)
    target[obj.id] = obj
```

No per-item `try/except`. A `ValidationError` on any item propagates up through `_load()`, leaving the repository in an empty state.

### Fix

Wrap in try/except with logging:
```python
for item in items:
    try:
        obj = model(**item)
        target[obj.id] = obj
    except Exception as e:
        logger.warning(f"Skipping malformed item in {path}: {e}")
```

### Test Strategy

- Unit: Inject a JSON file with one valid and one malformed item → assert valid items load and malformed items are skipped
- Unit: Assert `_courses`, `_modules`, `_lessons` dicts contain correct items after partial failure

---

## Summary

| # | Issue | Priority | Affected Files | Depends On |
|---|-------|----------|----------------|------------|
| I1 | Mark Complete wrong URL + missing `course_id` | 🔴 Critical | `lesson/[lessonId]/page.tsx`, `progress.py` | — |
| I2 | `isCompleted` never loaded from backend | 🟠 High | `lesson/[lessonId]/page.tsx` | I1 (same component) |
| I3 | `get_optional_current_user` dead `None` guard | 🟡 Medium | `auth.py` | — |
| I4 | `useAdjacentLessons` wasteful course fetch | 🔵 Low | `lesson/[lessonId]/page.tsx` | — |
| I5 | `FileCourseRepository` per-item error gap | 🔵 Low | `file_course_repository.py` | — |
