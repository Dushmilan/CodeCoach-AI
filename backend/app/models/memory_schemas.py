"""Pydantic schemas for forgetting-curve memory graph (Idea #3)."""

from typing import List, Optional

from pydantic import BaseModel, Field


class TopicMemory(BaseModel):
    topic: str = Field(..., description="Question category (e.g. Arrays)")
    totalCards: int = Field(..., description="Total review cards for the topic")
    dueCount: int = Field(..., description="Due cards in this topic")
    avgIntervalDays: float = Field(..., description="Mean SM-2 interval for the topic")
    daysSinceLastTouch: Optional[int] = Field(
        None, description="Days since the last submission or review for this topic"
    )
    lapseCount: int = Field(0, description="Total lapses in this topic")
    energyCostMinutes: int = Field(..., description="Estimated re-learn cost")
    cardIds: List[str] = Field(default_factory=list)


class MemoryGraphResponse(BaseModel):
    topics: List[TopicMemory]
    totalDue: int
    totalCards: int
    oldestDueDays: Optional[int] = None
