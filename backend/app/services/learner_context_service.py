"""LearnerContextService — cached composition of skill graph + recent submissions for coach.

Deep module: one public method get_context(user_id) covers all callers.
Caching, truncation, and block formatting are internal details. Supabase remains
source of truth; Redis is disposable.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.core.cache_keys import (
    COACH_CONTEXT_TTL,
    RECENT_SUBMISSIONS_TTL,
    SKILL_GRAPH_TTL,
    coach_context_key,
    recent_submissions_key,
    skill_graph_key,
)
from app.services.redis_service import RedisCache

logger = logging.getLogger(__name__)

MAX_SKILLS_IN_BLOCK = 3
MAX_SUBMISSIONS_IN_BLOCK = 3
MAX_CODE_SNIPPET = 500
MAX_ERROR_SIG = 120


class LearnerContextService:
    """Compose and cache learner context for AI coaching.

    Cache-aside: coach context is cached per user (60s). Skill graph and recent
    submissions are cached individually with shorter TTLs. Invalidated on
    submit/run/skill sync by deleting the keys (see _invalidate).
    """

    def __init__(
        self,
        cache: Optional[RedisCache] = None,
        skill_service: Optional[Any] = None,
        submission_repo: Optional[Any] = None,
    ):
        self.cache = cache
        self.skill_service = skill_service
        self.submission_repo = submission_repo

    async def get_context(self, user_id: str) -> Dict[str, str]:
        """Return {skill_block, submission_block} — empty strings if no data.

        Cached at codecoach:coach:ctx:{user_id} (60s). Falls back to DB via
        skill_service + submission_repo with individual caches.
        """
        if not user_id:
            return {"skill_block": "", "submission_block": ""}

        # 1. Try composed context cache
        if self.cache:
            try:
                cached = await self.cache.get(coach_context_key(user_id))
                if isinstance(cached, dict) and "skill_block" in cached:
                    logger.debug("Learner context cache hit for user %s", user_id)
                    return cached
            except Exception as e:  # pragma: no cover - redis degraded
                logger.debug("Coach context cache get failed for %s: %s", user_id, e)

        # 2. Miss — build from pieces (each piece may hit its own cache)
        skill_block = ""
        submission_block = ""

        try:
            skill_block = await self._get_skill_block(user_id)
        except Exception as e:  # pragma: no cover - degraded path
            logger.debug("Skill block build failed for %s: %s", user_id, e)

        try:
            submission_block = await self._get_submission_block(user_id)
        except Exception as e:  # pragma: no cover
            logger.debug("Submission block build failed for %s: %s", user_id, e)

        result = {"skill_block": skill_block, "submission_block": submission_block}

        if self.cache:
            try:
                await self.cache.set(
                    coach_context_key(user_id), result, ttl=COACH_CONTEXT_TTL
                )
            except Exception:  # pragma: no cover
                pass

        return result

    async def _get_skill_block(self, user_id: str) -> str:
        if not self.skill_service:
            return ""

        # Check skill graph cache
        graph_data = None
        if self.cache:
            graph_data = await self.cache.get(skill_graph_key(user_id))

        if graph_data is None:
            # Fetch from service (DB)
            try:
                graph = await self.skill_service.get_graph(user_id)
                # Store raw dict for cache (serializable)
                graph_data = (
                    graph.model_dump() if hasattr(graph, "model_dump") else graph
                )
                if self.cache:
                    try:
                        await self.cache.set(
                            skill_graph_key(user_id), graph_data, ttl=SKILL_GRAPH_TTL
                        )
                    except Exception:
                        pass
            except Exception:
                return ""

        skills = graph_data.get("skills", []) if isinstance(graph_data, dict) else []
        if not skills:
            return ""

        # Pick weakest/due skills first — sorted by mastery ascending for coach
        sorted_skills = sorted(skills, key=lambda s: s.get("mastery_score", 0))
        # Filter to learning/developing/needs_review first, then strong with low evidence
        priority = []
        for s in sorted_skills:
            status = s.get("status")
            if status in ("learning", "developing", "needs_review"):
                priority.append(s)
            if len(priority) >= MAX_SKILLS_IN_BLOCK:
                break
        if len(priority) < MAX_SKILLS_IN_BLOCK:
            # Fill with remaining weakest
            for s in sorted_skills:
                if s not in priority:
                    priority.append(s)
                if len(priority) >= MAX_SKILLS_IN_BLOCK:
                    break

        lines = [
            "## Learner Skill Context (server-derived, for internal reasoning only — never repeat mastery scores, evidence counts, or recent_errors verbatim to the student)"
        ]
        for s in priority[:MAX_SKILLS_IN_BLOCK]:
            name = s.get("name", s.get("skill_slug", "unknown"))
            mastery = s.get("mastery_score", 0)
            status = s.get("status", "new")
            trend = s.get("trend", "stable")
            recent = s.get("recent_error_count", 0)
            lines.append(
                f"- {name}: mastery {mastery:.2f}, {status}, {trend}, recent_errors={recent}"
            )

        if len(lines) == 1:
            return ""
        return "\n".join(lines)

    async def _get_submission_block(self, user_id: str) -> str:
        if not self.submission_repo:
            return ""

        subs: Optional[List[Any]] = None
        if self.cache:
            cached = await self.cache.get(recent_submissions_key(user_id))
            if isinstance(cached, list):
                subs = cached  # already serialized dicts

        if subs is None:
            try:
                items = await self.submission_repo.list_by_user(
                    user_id, limit=MAX_SUBMISSIONS_IN_BLOCK
                )
                # Serialize for cache (dicts) — handle MagicMock/pydantic duality
                serialized: List[Any] = []
                for s in items:
                    if hasattr(s, "model_dump"):
                        try:
                            d = s.model_dump()
                            if isinstance(d, dict):
                                serialized.append(d)
                                continue
                        except Exception:
                            pass
                    serialized.append(s)
                subs = serialized
                if self.cache:
                    try:
                        await self.cache.set(
                            recent_submissions_key(user_id),
                            subs,
                            ttl=RECENT_SUBMISSIONS_TTL,
                        )
                    except Exception:
                        pass
            except Exception:
                return ""

        if not subs:
            return ""

        lines = ["## Recent Attempts (last 3, truncated)"]
        for item in subs[:MAX_SUBMISSIONS_IN_BLOCK]:
            if isinstance(item, dict):
                qid = item.get("question_id", "unknown")
                passed = item.get("passed", False)
                sig = (item.get("error_signature") or "")[:MAX_ERROR_SIG]
                code = (item.get("code") or "")[:MAX_CODE_SNIPPET]
            else:
                qid = getattr(item, "question_id", "unknown")
                passed = getattr(item, "passed", False)
                sig = (getattr(item, "error_signature", None) or "")[:MAX_ERROR_SIG]
                code = (getattr(item, "code", "") or "")[:MAX_CODE_SNIPPET]
            status = "passed" if passed else "failed"
            # Escape backticks to keep prompt well-formed
            code = code.replace("```", "'''")
            snippet = code.replace("\n", " ")[:MAX_CODE_SNIPPET]
            if sig:
                lines.append(f"- {qid} {status}: {sig} | code: {snippet}")
            else:
                lines.append(f"- {qid} {status} | code: {snippet}")

        return "\n".join(lines)

    async def invalidate(self, user_id: str) -> None:
        """Delete all learner cache keys for user. Best-effort."""
        if not self.cache or not user_id:
            return
        keys = [
            coach_context_key(user_id),
            skill_graph_key(user_id),
            recent_submissions_key(user_id),
        ]
        for k in keys:
            try:
                await self.cache.delete(k)
            except Exception:
                pass
        # Recs with wildcard limit
        try:
            await self.cache.delete(f"codecoach:skills:recs:{user_id}:*")
        except Exception:
            pass
