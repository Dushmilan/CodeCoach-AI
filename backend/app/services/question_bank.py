"""QuestionBank — deep module for question access.

Three interface methods cover all callers: query, get, add, stats.
Caching, pagination, validation, and stats computation are internal details.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from app.models.schemas import Question, QuestionSummary, Difficulty
from app.models.question_validation_schemas import (
    QuestionValidationStatus,
    QuestionValidationResult,
)
from app.ports.question_repository import QuestionRepository
from app.services.question_validator import QuestionValidatorService
from app.services.redis_service import RedisCache

logger = logging.getLogger(__name__)


# ── Interface types ───────────────────────────────────────────────────


@dataclass
class QuestionFilters:
    difficulty: Optional[Difficulty] = None
    category: Optional[str] = None
    query: Optional[str] = None
    page: int = 1
    per_page: int = 20


@dataclass
class QuestionPage:
    items: List[QuestionSummary]
    total: int
    page: int
    per_page: int


@dataclass
class QuestionStats:
    total: int
    difficulty_counts: Dict[str, int]
    category_counts: Dict[str, int]
    categories: List[str]
    companies: List[str]


# ── Deep module ───────────────────────────────────────────────────────


class QuestionBank:
    """Deep module — 3 interface methods + stats cover all callers.
    Caching, pagination, validation, and stats are internal."""

    def __init__(
        self,
        repository: QuestionRepository,
        validator: Optional[QuestionValidatorService] = None,
        cache: Optional[RedisCache] = None,
    ):
        self._repo = repository
        self._validator = validator
        self._cache = cache

    # ── Interface ─────────────────────────────────────────────────────

    async def query(self, filters: QuestionFilters) -> QuestionPage:
        if filters.query:
            summaries = await self._repo.search_summaries(
                filters.query,
                difficulty=filters.difficulty,
                category=filters.category,
            )
        else:
            summaries = await self._repo.get_summaries(
                difficulty=filters.difficulty,
                category=filters.category,
            )

        total = len(summaries)
        start = (filters.page - 1) * filters.per_page
        items = summaries[start : start + filters.per_page]

        return QuestionPage(
            items=items, total=total, page=filters.page, per_page=filters.per_page
        )

    async def get(self, question_id: str) -> Question:
        if self._cache:
            cache_key = RedisCache.key("questions", "detail", question_id)
            cached = await self._cache.get(cache_key)
            if cached is not None:
                return Question(**cached)

        question = await self._repo.get_by_id(question_id)
        if question is None:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=404, detail=f"Question not found: {question_id}"
            )

        if self._cache:
            cache_key = RedisCache.key("questions", "detail", question_id)
            await self._cache.set(cache_key, question.model_dump(), ttl=300)

        return question

    async def add(
        self, question: Question, validate: bool = True
    ) -> QuestionValidationStatus:
        validated = False
        passed = False

        if validate and self._validator:
            result = await self._validator.validate_question(question)
            await self._persist_validation_status(question.id, result)
            validated = True
            passed = bool(result.valid)
            if not passed:
                logger.warning("Question %s failed validation", question.id)

        await self._repo.add(question)
        if validated and passed:
            await self._invalidate_cache()

        return QuestionValidationStatus(
            is_validated=validated, validation_passed=passed
        )

    async def stats(self) -> QuestionStats:
        total = await self._cached_or_fetch("total_count", self._compute_total)
        difficulty_counts = await self._cached_or_fetch(
            "stats:difficulty_counts", self._compute_difficulty_counts
        )
        category_counts = await self._cached_or_fetch(
            "stats:category_counts", self._compute_category_counts
        )
        categories = await self._cached_or_fetch(
            "categories", self._repo.get_categories
        )
        companies = await self._cached_or_fetch(
            "companies", self._repo.get_company_tags
        )

        return QuestionStats(
            total=total,
            difficulty_counts=difficulty_counts,
            category_counts=category_counts,
            categories=categories,
            companies=companies,
        )

    # ── Internal: caching ─────────────────────────────────────────────

    async def _cached_or_fetch(self, name: str, fetch_fn):
        if self._cache:
            cache_key = RedisCache.key("questions", name)
            cached = await self._cache.get(cache_key)
            if cached is not None:
                return cached

        result = await fetch_fn()

        if self._cache:
            cache_key = RedisCache.key("questions", name)
            await self._cache.set(cache_key, result, ttl=300)

        return result

    async def _invalidate_cache(self):
        if self._cache:
            await self._cache.delete("codecoach:questions:*")

    # ── Internal: stats computation ───────────────────────────────────

    async def _compute_total(self) -> int:
        return await self._repo.count()

    async def _compute_difficulty_counts(self) -> Dict[str, int]:
        questions = await self._repo.get_all()
        counts = {"easy": 0, "medium": 0, "hard": 0}
        for q in questions:
            counts[q.difficulty.value] += 1
        return counts

    async def _compute_category_counts(self) -> Dict[str, int]:
        questions = await self._repo.get_all()
        counts: Dict[str, int] = {}
        for q in questions:
            counts[q.category] = counts.get(q.category, 0) + 1
        return counts

    # ── Internal: validation persistence ──────────────────────────────

    async def _persist_validation_status(
        self, question_id: str, result: QuestionValidationResult
    ):
        status = QuestionValidationStatus(
            is_validated=True,
            last_validated=result.validated_at,
            validation_passed=result.valid,
            validation_errors=[
                issue.message
                for r in result.results.values()
                for issue in r.issues
                if issue.severity.value == "error"
            ],
            validation_warnings=[
                issue.message
                for r in result.results.values()
                for issue in r.issues
                if issue.severity.value == "warning"
            ],
        )
        await self._repo.save_validation_status(question_id, status)
