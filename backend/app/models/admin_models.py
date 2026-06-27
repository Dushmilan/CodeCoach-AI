from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class UserAdminUpdate(BaseModel):
    role: Optional[str] = Field(
        None, description="User role (user, admin, super_admin)"
    )
    is_active: Optional[bool] = Field(None, description="User account active status")
    oauth_provider: Optional[str] = Field(None, description="OAuth provider")


class UserDetailResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: datetime
    is_active: bool
    role: str
    oauth_provider: Optional[str]
    oauth_id: Optional[str]


class StatsResponse(BaseModel):
    users: Dict[str, Any]
    questions: Dict[str, Any]
    courses: Dict[str, Any]
    system: Dict[str, Any]
    generation: Dict[str, Any]


class QuestionFilter(BaseModel):
    difficulty: Optional[str] = None
    category: Optional[str] = None
    has_solution: Optional[bool] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


class QuestionImportResult(BaseModel):
    total: int
    successful: int
    failed: int
    errors: List[Dict[str, Any]]


class FeatureFlagUpdate(BaseModel):
    enabled: Optional[bool] = None
    rollout_pct: Optional[int] = Field(None, ge=0, le=100)
    target_roles: Optional[List[str]] = None
    description: Optional[str] = None


class GenerationJobCreate(BaseModel):
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    count: Optional[int] = Field(None, gt=0, le=100)
    model: Optional[str] = None


class CourseProgressDetail(BaseModel):
    course_id: str
    completed_lessons: List[str]
    last_accessed_lesson_id: Optional[str]
    progress: float


class AuditLogFilter(BaseModel):
    user_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    level: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(50, ge=1, le=100)
