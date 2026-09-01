from pydantic import BaseModel, Field
from typing import List, Optional, Any


class WorkspaceCodePut(BaseModel):
    language: str = Field(
        ..., min_length=1, max_length=20, description="Programming language"
    )
    code: str = Field(..., max_length=51200, description="Draft code (max 50KB)")


class WorkspaceCodeOut(BaseModel):
    code: str
    language: str
    updated_at: Optional[str] = None
    question_id: str


class LastVisitedOut(BaseModel):
    question_id: str
    language: Optional[str] = None
    visited_at: str


class LastVisitedPut(BaseModel):
    question_id: str = Field(..., min_length=1, max_length=100)
    language: Optional[str] = Field(None, max_length=20)


class ChatMessageIn(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., max_length=5000)
    structured: Optional[Any] = None


class ChatHistoryOut(BaseModel):
    question_id: str
    messages: List[dict]


class ChatHistoryPut(BaseModel):
    messages: List[ChatMessageIn] = Field(..., max_length=20)


class WorkspaceMetaOut(BaseModel):
    question_id: str
    language: Optional[str] = None
    last_opened_at: Optional[str] = None
