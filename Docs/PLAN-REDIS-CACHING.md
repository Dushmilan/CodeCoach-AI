# Plan: Redis Caching for CodeCoach AI

## 1. Rationale

The backend currently has:

- **File-based repositories** — `sample_questions.json`, `data/courses/`, `data/user_progress.json` — all read from disk on every request
- **External API calls** — NVIDIA NIM (AI coaching, ~5-60s), Piston (code execution, ~1-5s)
- **Computed data** — question stats, difficulty/category counts — recalculated each time
- **No in-memory cache** beyond `lru_cache` on `get_settings()` (single-threaded, lost on restart)

Adding Redis eliminates repeated I/O for hot paths and avoids redundant external API calls for identical inputs.

---

## 2. Caching Opportunities Matrix

| Data                         | Source           | Access Pattern        | Volatility                      | Value  | Proposed TTL | Cache Key Pattern                |
| ---------------------------- | ---------------- | --------------------- | ------------------------------- | ------ | ------------ | -------------------------------- |
| **Question list/detail**     | JSON file / SQL  | Read-heavy, unbounded | Rarely changes                  | ⭐⭐⭐ | 5 min        | `questions:{type}:{params_hash}` |
| **Course/module/lesson**     | JSON files       | Read-heavy, unbounded | Never changes (curated)         | ⭐⭐⭐ | 1 hr         | `courses:{course_id}:{field}`    |
| **AI coaching (structured)** | NVIDIA NIM API   | On-demand             | Bounded (deterministic)         | ⭐⭐⭐ | 24 hr        | `nim:coaching:{content_hash}`    |
| **Code execution (run)**     | Piston API       | On-demand             | Deterministic per input         | ⭐⭐⭐ | 1 hr         | `exec:run:{content_hash}`        |
| **Code execution (submit)**  | Piston API       | On-demand             | Deterministic per input         | ⭐⭐⭐ | 1 hr         | `exec:submit:{content_hash}`     |
| **Code validation**          | Static validator | On-demand             | Deterministic                   | ⭐⭐   | 30 min       | `exec:validate:{content_hash}`   |
| **Piston runtimes**          | Piston API       | On startup            | Static                          | ⭐⭐   | 1 hr         | `piston:runtimes`                |
| **Question stats**           | Computed         | Read-heavy            | Derived; changes with questions | ⭐⭐   | 5 min        | `questions:stats:{lang}`         |
| **User progress**            | JSON file / SQL  | Per-user, write-heavy | Volatile per action             | ⭐     | None (skip)  | N/A                              |
| **AI coaching (stream)**     | NVIDIA NIM API   | Streaming             | Non-deterministic               | ⭐     | Skip         | N/A                              |

---

## 3. Infrastructure

### 3.1 Redis Service (docker-compose.yml)

```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: codecoach-redis
    restart: unless-stopped
    ports:
      - '6379:6379'
    volumes:
      - redis-data:/data
    networks:
      - codecoach-network
    healthcheck:
      test: ['CMD', 'redis-cli', 'ping']
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  redis-data:
```

Add `redis` to `depends_on` for `backend`.

### 3.2 Redis Config (backend/app/core/config.py)

```python
# Redis
REDIS_URL: str = "redis://redis:6379/0"
REDIS_TTL_DEFAULT: int = 300       # 5 min
REDIS_TTL_STATIC: int = 3600       # 1 hr
REDIS_TTL_AI: int = 86400          # 24 hr
REDIS_TTL_EXECUTION: int = 3600    # 1 hr
REDIS_ENABLED: bool = True
REDIS_MAXMEMORY: str = "512mb"
REDIS_MAXMEMORY_POLICY: str = "allkeys-lru"
```

### 3.3 Dependency (backend/requirements.txt)

```
redis[hiredis]>=5.0,<6
```

---

## 4. Redis Client Service

New file: `backend/app/services/redis_service.py`

### API

```python
class RedisCache:
    def __init__(self, redis_url: str):
        self._pool = ConnectionPool.from_url(redis_url, max_connections=20)

    async def get(self, key: str) -> Optional[Any]: ...
    async def set(self, key: str, value: Any, ttl: int = 300) -> None: ...
    async def delete(self, pattern: str) -> int: ...
    async def exists(self, key: str) -> bool: ...
    async def ttl(self, key: str) -> int: ...
    async def close(self) -> None: ...
    def key(self, *parts: str) -> str:  # -> "codecoach:prefix:suffix"
```

### Key Namespacing

All keys follow: `codecoach:{service}:{rest}`

| Namespace | Pattern Example                                                      |
| --------- | -------------------------------------------------------------------- |
| questions | `codecoach:questions:list:{"difficulty":"easy","category":"arrays"}` |
| courses   | `codecoach:courses:detail:c01`                                       |
| nim       | `codecoach:nim:coaching:{sha256[:16]}`                               |
| exec      | `codecoach:exec:run:{sha256[:16]}`                                   |
| piston    | `codecoach:piston:runtimes`                                          |

### Hash-based Keys

For execution and AI coaching, use SHA-256 of normalized inputs:

```python
def _content_hash(*parts: str) -> str:
    normalized = ":".join(parts)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]
```

---

## 5. Service Integration Points

### 5.1 Questions Service (`app/services/questions_service.py`)

```
Cache Strategy:
  GET  /api/questions/               → cache with TTL 5min
  GET  /api/questions/{id}           → cache with TTL 5min
  GET  /api/questions/categories     → cache with TTL 5min
  GET  /api/questions/companies      → cache with TTL 5min
  GET  /api/questions/stats          → cache with TTL 5min
  POST /api/questions/validate       → cache with TTL 5min (by question_id)

Invalidation:
  add_question()          → DELETE codecoach:questions:*
  validate_question()     → DELETE codecoach:questions:validation:{id}
```

Implementation pattern:

```python
async def get_all_questions(self, ...) -> List[QuestionSummary]:
    cache_key = self.cache.key("questions", "list", self._params_hash(difficulty, category, page, per_page))
    cached = await self.cache.get(cache_key)
    if cached:
        return [QuestionSummary(**item) for item in cached]
    result = await self.repository.get_summaries(...)
    await self.cache.set(cache_key, [r.model_dump() for r in result], ttl=300)
    return result
```

### 5.2 Course Service (`app/services/course_service.py`)

```
Cache Strategy:
  GET  /api/courses/                     → cache with TTL 1hr (skip user progress in cached version)
  GET  /api/courses/{id}                 → cache with TTL 1hr
  GET  /api/courses/lessons/{id}         → cache with TTL 1hr
  GET  /api/courses/lessons/{id}/adjacent → cache with TTL 1hr

Invalidation:
  No writes to courses; never invalidates naturally.
  For admin edits (future): DELETE codecoach:courses:*
```

### 5.3 NIM Service (`app/services/nim_service.py`)

```
Cache Strategy:
  POST /api/coach/structured    → cache structured response with TTL 24hr

Implementation:
  - Content hash = sha256(problem + code + message + mode + difficulty + lesson_context)
  - Skip caching for streaming (non-deterministic by nature)
  - Cache hit returns structured dict directly, skips NIM API call
```

### 5.4 Code Execution (`app/services/piston_service.py`)

```
Cache Strategy:
  POST /api/run/                → cache ExecutionResult with TTL 1hr
  POST /api/submit/             → cache List[TestCaseResult] with TTL 1hr
  POST /api/run/validate        → cache validation dict with TTL 30min
  GET  /api/run/languages       → cache filtered runtimes with TTL 1hr
  GET  /api/run/runtimes        → cache with TTL 1hr

Implementation:
  - Content hash = sha256(language + code + stdin + version)  for /run
  - Content hash = sha256(language + code + question_id + test_cases_json)  for /submit
  - test_cases_json = json.dumps(test_cases, sort_keys=True)
  - Cache hit returns deserialized pydantic model directly
```

---

## 6. Cache Invalidation Strategy

| Trigger               | Invalidation                                 |
| --------------------- | -------------------------------------------- |
| New question added    | `DELETE codecoach:questions:*`               |
| Question validated    | `DELETE codecoach:questions:validation:{id}` |
| Course edited (admin) | `DELETE codecoach:courses:*`                 |
| User completes lesson | No invalidation needed (progress not cached) |
| Redis memory pressure | `allkeys-lru` eviction (Redis config)        |
| Server restart        | All caches cold (expected)                   |

### Lazy Invalidation

Default strategy: TTL-based expiration. Most data in this app changes infrequently enough that TTL expiry is sufficient.

### Explicit Invalidation (for admin operations)

When questions/courses are modified via admin endpoints, explicitly delete the affected key patterns. For writes via the public API (add_question), delete the broader pattern `codecoach:questions:*` to force re-cache on next read.

---

## 7. Graceful Degradation

- **Redis unreachable → app continues** (`redis.exceptions.ConnectionError` caught, fall through to source)
- No retry logic in hot path — fail fast and use source data
- `REDIS_ENABLED=False` bypasses Redis entirely (test/dev mode)
- Writes never depend on cache — cache is write-around

### Wrapper / Mixin

Optional: a `@cached(ttl=300)` decorator or `CacheMixin` base class to reduce boilerplate:

```python
class CachedQuestionsService(QuestionsService):
    async def get_all_questions(self, difficulty=None, category=None, page=1, per_page=20):
        return await self._with_cache(
            "questions", "list",
            lambda: super().get_all_questions(difficulty, category, page, per_page),
            ttl=300,
            difficulty=difficulty, category=category, page=page, per_page=per_page,
        )
```

But **prefer explicit inline caching** in each service method for clarity and debuggability.

---

## 8. Implementation Phases

### Phase 1: Foundation (2-3 hr)

| Step | File                                    | Description                                    |
| ---- | --------------------------------------- | ---------------------------------------------- |
| 1.1  | `docker-compose.yml`, `.env`            | Add Redis service + env vars                   |
| 1.2  | `backend/requirements.txt`              | Add `redis[hiredis]`                           |
| 1.3  | `backend/app/core/config.py`            | Add Redis settings                             |
| 1.4  | `backend/app/services/redis_service.py` | Create RedisCache class                        |
| 1.5  | `backend/app/main.py`                   | Initialize Redis on startup, close on shutdown |
| 1.6  | `backend/app/api/dependencies.py`       | Add `get_redis_cache()` dependency             |

### Phase 2: Service Integration (4-6 hr)

| Step | File                   | Changes                                                                       |
| ---- | ---------------------- | ----------------------------------------------------------------------------- |
| 2.1  | `piston_service.py`    | Cache `get_runtimes`, `execute`, `evaluate_suite`                             |
| 2.2  | `nim_service.py`       | Cache `get_structured_coaching_response`                                      |
| 2.3  | `questions_service.py` | Cache `get_all_questions`, `get_question_by_id`, stats, categories, companies |
| 2.4  | `course_service.py`    | Cache `list_courses`, `get_course_with_modules`, `get_lesson`                 |
| 2.5  | `submit.py` (api)      | Cache submit results                                                          |
| 2.6  | `run.py` (api)         | Cache run results                                                             |

### Phase 3: Testing & Validation (2-3 hr)

| Step | Description                                         |
| ---- | --------------------------------------------------- |
| 3.1  | Unit tests for `RedisCache` (mock redis)            |
| 3.2  | Integration tests with testcontainers/real Redis    |
| 3.3  | Cache hit/miss assertions in existing service tests |
| 3.4  | Verify graceful degradation when Redis is down      |
| 3.5  | Verify cache invalidation triggers                  |

---

## 9. Testing Strategy

### Unit Tests

```python
# test_redis_service.py
class TestRedisCache:
    async def test_set_and_get(self, mock_redis): ...
    async def test_get_miss(self, mock_redis): ...
    async def test_ttl_set(self, mock_redis): ...
    async def test_delete_pattern(self, mock_redis): ...
    async def test_graceful_degradation(self, mock_redis_down): ...
```

### Service Tests with Cache

Extend existing tests to verify:

- First call → cache miss → data from source → cache populated
- Second call → cache hit → data from cache (verify no source access)
- After invalidation → cache miss → fresh from source

### Execution Cache Tests

```python
async def test_run_cache_hit(mock_piston, mock_redis):
    # First call hits Piston, caches result
    result1 = await piston_service.execute("python", "print(1)")
    # Second call returns cached, does NOT hit Piston
    result2 = await piston_service.execute("python", "print(1)")
    assert mock_piston.call_count == 1
```

---

## 10. Monitoring & Observability

Expose via `/health/` or `/debug/` endpoint:

```json
{
  "redis": {
    "connected": true,
    "used_memory": "12.5MB",
    "hit_rate": 0.87,
    "keys": 142,
    "uptime_seconds": 3600
  }
}
```

Track per-namespace stats:

- `codecoach:cache:hits:{namespace}` → increment on hit
- `codecoach:cache:misses:{namespace}` → increment on miss
- Compute rate in `/health/redis` handler

---

## 11. Future Considerations

- **Session-based draft caching** — store user's in-progress editor code in Redis (`codecoach:draft:{user_id}:{question_id}`), TTL 7 days, auto-save from frontend with debounce
- **Rate limit backend** — replace slowapi with Redis-based sliding window
- **WebSocket pub/sub** — for live collaboration or real-time coaching updates
- **Cache warming** — on startup, pre-load questions list and courses into cache
- **Redis Sentinel/Cluster** — when scaling beyond single instance
- **Prometheus metrics** — expose cache stats via `/metrics` endpoint

---

## 12. Rollback Plan

1. Set `REDIS_ENABLED=False` in `.env` — bypasses Redis entirely, app runs from source
2. Revert `docker-compose.yml` changes
3. Remove `redis[hiredis]` from requirements.txt

---

## Appendix A: Environment Variables

```
REDIS_URL=redis://redis:6379/0
REDIS_TTL_DEFAULT=300
REDIS_TTL_STATIC=3600
REDIS_TTL_AI=86400
REDIS_TTL_EXECUTION=3600
REDIS_ENABLED=true
REDIS_MAXMEMORY=512mb
REDIS_MAXMEMORY_POLICY=allkeys-lru
```

## Appendix B: Key Reference

| Key Pattern                       | TTL    | Size Estimate | Purpose                      |
| --------------------------------- | ------ | ------------- | ---------------------------- |
| `codecoach:questions:list:{hash}` | 300s   | ~50KB         | Paginated question summaries |
| `codecoach:questions:detail:{id}` | 300s   | ~5KB          | Single question              |
| `codecoach:questions:categories`  | 300s   | ~1KB          | Category list                |
| `codecoach:questions:companies`   | 300s   | ~1KB          | Company tag list             |
| `codecoach:questions:stats`       | 300s   | ~2KB          | Aggregated stats             |
| `codecoach:courses:list`          | 3600s  | ~5KB          | Course summaries             |
| `codecoach:courses:detail:{id}`   | 3600s  | ~20KB         | Course with modules/lessons  |
| `codecoach:courses:lesson:{id}`   | 3600s  | ~3KB          | Single lesson                |
| `codecoach:nim:coaching:{hash}`   | 86400s | ~2KB          | Structured AI response       |
| `codecoach:exec:run:{hash}`       | 3600s  | ~1KB          | Code execution result        |
| `codecoach:exec:submit:{hash}`    | 3600s  | ~5KB          | Submit/test result           |
| `codecoach:exec:validate:{hash}`  | 1800s  | ~1KB          | Code validation result       |
| `codecoach:piston:runtimes`       | 3600s  | ~10KB         | Piston runtime list          |
