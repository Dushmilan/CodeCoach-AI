from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel


class AnalyticsSignal(BaseModel):
    type: Literal["plateau"]
    skill: str
    title: str
    detail: str
    evidence: dict
    severity: Literal["warning", "info"] = "warning"
    first_seen_at: datetime
    last_seen_at: datetime


class AnalyticsSignalsResponse(BaseModel):
    signals: List[AnalyticsSignal]
    total: int


class ClassStudentSummary(BaseModel):
    """Per-student rollup over existing progress + submissions (read-only)."""

    user_id: str
    username: str = ""
    completed_lessons: int = 0
    completion_pct: float = 0.0
    attempted: int = 0
    solved: int = 0


class ClassAnalyticsResponse(BaseModel):
    total_students: int = 0
    avg_completion: float = 0.0
    avg_solved: float = 0.0
    students: List[ClassStudentSummary] = []
