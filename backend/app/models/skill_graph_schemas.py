from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.schemas import Question


class LearningEventType(str, Enum):
    LESSON_COMPLETED = "lesson_completed"
    QUESTION_STARTED = "question_started"
    CODE_RUN = "code_run"
    SUBMISSION_PASSED = "submission_passed"
    SUBMISSION_FAILED = "submission_failed"
    HINT_REQUESTED = "hint_requested"
    SOLUTION_REVEALED = "solution_revealed"
    DIAGNOSIS_CREATED = "diagnosis_created"
    REVIEW_COMPLETED = "review_completed"
    REVIEW_ANSWERED = "review_answered"


class SkillStatus(str, Enum):
    NEW = "new"
    LEARNING = "learning"
    DEVELOPING = "developing"
    STRONG = "strong"
    NEEDS_REVIEW = "needs_review"


class Trend(str, Enum):
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"


class Skill(BaseModel):
    slug: str = Field(..., description="Unique skill slug")
    name: str = Field(..., description="Human-readable skill name")
    description: str = Field(default="", description="Skill description")
    parent_id: Optional[str] = Field(None, description="Parent skill slug (hierarchy)")
    prerequisite_ids: List[str] = Field(
        default_factory=list, description="Skills that must be mastered first"
    )


class QuestionSkill(BaseModel):
    question_id: str = Field(..., description="Question ID")
    skill_slug: str = Field(..., description="Skill slug exercised by the question")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Skill weight")


class LearningEvent(BaseModel):
    id: Optional[str] = Field(None, description="Event ID (idempotency key)")
    user_id: str = Field(..., description="User ID")
    event_type: LearningEventType = Field(..., description="Event type")
    question_id: Optional[str] = Field(None, description="Question ID if applicable")
    lesson_id: Optional[str] = Field(None, description="Lesson ID if applicable")
    skill_slug: Optional[str] = Field(None, description="Explicit skill slug")
    metadata: Dict[str, object] = Field(
        default_factory=dict, description="Event metadata"
    )
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the event happened",
    )

    @field_validator("metadata", mode="before")
    @classmethod
    def coerce_metadata(cls, value: object) -> object:
        if value is None:
            return {}
        return value


class UserSkillState(BaseModel):
    user_id: str = Field(..., description="User ID")
    skill_slug: str = Field(..., description="Skill slug")
    mastery_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_count: int = Field(default=0, ge=0)
    recent_error_count: int = Field(default=0, ge=0)
    distinct_question_ids: List[str] = Field(
        default_factory=list, description="Question IDs seen for this skill"
    )
    last_seen_at: Optional[datetime] = Field(None)
    last_reviewed_at: Optional[datetime] = Field(None)
    status: SkillStatus = Field(default=SkillStatus.NEW)
    trend: Trend = Field(default=Trend.STABLE)


class SkillSummary(BaseModel):
    skill_slug: str = Field(..., description="Skill slug")
    name: str = Field(..., description="Skill name")
    mastery_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    status: SkillStatus = Field(...)
    trend: Trend = Field(...)
    evidence_count: int = Field(...)
    recent_error_count: int = Field(...)
    last_seen_at: Optional[datetime] = Field(None)
    last_reviewed_at: Optional[datetime] = Field(None)


class SkillGraphEdge(BaseModel):
    source: str = Field(..., description="Prerequisite skill slug")
    target: str = Field(..., description="Dependent skill slug")
    relation: str = Field(default="prerequisite")


class SkillGraphResponse(BaseModel):
    skills: List[SkillSummary] = Field(default_factory=list)
    edges: List[SkillGraphEdge] = Field(default_factory=list)


class RecommendationReason(str, Enum):
    WEAK_SKILL = "weak_skill"
    MISSING_PREREQUISITE = "missing_prerequisite"
    DUE_FOR_REVIEW = "due_for_review"
    NEW_SKILL = "new_skill"
    STRENGTHEN = "strengthen"


class Recommendation(BaseModel):
    skill_slug: str = Field(..., description="Recommended skill")
    name: str = Field(..., description="Skill name")
    reason: RecommendationReason = Field(..., description="Why it is recommended")
    reason_text: str = Field(..., description="Human-readable explanation")
    suggested_question_id: Optional[str] = Field(
        None, description="Optional question to practice"
    )


class EventIngestResult(BaseModel):
    accepted: int = Field(default=0, ge=0)
    skipped: int = Field(default=0, ge=0)
    duplicate: int = Field(default=0, ge=0)
    invalid: int = Field(default=0, ge=0)


class RecommendedQuestion(BaseModel):
    """A practice recommendation resolved to a concrete question."""

    skill_slug: str = Field(..., description="Recommended skill slug")
    skill_name: str = Field(..., description="Recommended skill name")
    reason: RecommendationReason = Field(..., description="Why it is recommended")
    reason_text: str = Field(..., description="Human-readable explanation")
    question: Question = Field(..., description="The recommended question")
