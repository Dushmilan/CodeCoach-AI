"""Centralized Redis cache keys and TTLs for learner context."""

# Skill graph
SKILL_GRAPH_TTL = 60  # seconds
SKILL_RECS_TTL = 60
RECENT_SUBMISSIONS_TTL = 30
COACH_CONTEXT_TTL = 60

# Existing TTLs (mirrors config for reference)
# REDIS_TTL_DEFAULT 300, REDIS_TTL_EXECUTION 3600, REDIS_TTL_AI 86400


def skill_graph_key(user_id: str) -> str:
    from app.services.redis_service import RedisCache

    return RedisCache.key("skills", "graph", user_id)


def skill_recs_key(user_id: str, limit: int = 5) -> str:
    from app.services.redis_service import RedisCache

    return RedisCache.key("skills", "recs", user_id, str(limit))


def recent_submissions_key(user_id: str) -> str:
    from app.services.redis_service import RedisCache

    return RedisCache.key("submissions", "recent", user_id)


def coach_context_key(user_id: str) -> str:
    from app.services.redis_service import RedisCache

    return RedisCache.key("coach", "ctx", user_id)


def learner_invalidation_patterns(user_id: str) -> list[str]:
    """Glob patterns to delete on learner mutation. Deleted via SCAN-friendly direct keys."""
    return [
        coach_context_key(user_id),
        skill_graph_key(user_id),
        recent_submissions_key(user_id),
        # recs with various limits — delete via pattern then direct
        f"codecoach:skills:recs:{user_id}:*",
    ]
