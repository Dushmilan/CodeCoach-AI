from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    timestamp: Optional[str] = None


class HintRequest(BaseModel):
    question_id: str = Field(..., description="The ID of the current question")
    code: str = Field(..., description="The current code being written")
    language: str = Field(..., description="Programming language being used")
    previous_hints: List[str] = Field(default_factory=list, description="Previous hints given")


class HintResponse(BaseModel):
    hint: str
    hint_type: str = Field(..., description="Type of hint: general, specific, or solution")
    confidence: float = Field(..., ge=0, le=1, description="Confidence level of the hint")


class ReviewRequest(BaseModel):
    question_id: str = Field(..., description="The ID of the current question")
    code: str = Field(..., description="The code to review")
    language: str = Field(..., description="Programming language")
    test_results: Optional[List[Dict[str, Any]]] = Field(None, description="Test results if available")


class ReviewResponse(BaseModel):
    overall_score: float = Field(..., ge=0, le=100, description="Overall code quality score")
    feedback: str = Field(..., description="Detailed feedback on the code")
    suggestions: List[str] = Field(..., description="List of specific suggestions")
    time_complexity: Optional[str] = Field(None, description="Time complexity analysis")
    space_complexity: Optional[str] = Field(None, description="Space complexity analysis")
    edge_cases: List[str] = Field(default_factory=list, description="Edge cases to consider")
    improvements: List[str] = Field(default_factory=list, description="Potential improvements")


class ChatRequest(BaseModel):
    question_id: str = Field(..., description="The ID of the current question")
    message: str = Field(..., description="User's message to the AI coach")
    code: Optional[str] = Field(None, description="Current code context")
    language: str = Field(..., description="Programming language")
    conversation_history: List[ChatMessage] = Field(default_factory=list, description="Previous conversation")


class ChatResponse(BaseModel):
    response: str
    follow_up_questions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
    code_suggestions: List[str] = Field(default_factory=list, description="Code suggestions if applicable")
    resources: List[str] = Field(default_factory=list, description="Helpful resources or links")