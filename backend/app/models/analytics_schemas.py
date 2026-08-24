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
