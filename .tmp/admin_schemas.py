from pydantic import BaseModel, Field
from typing import Optional, List


class UserAnalyticsResponse(BaseModel):
    total_users: int = Field(description="Total number of users")
    active_users: int = Field(description="Number of active users")
    new_users_30d: int = Field(description="Users created in last 30 days")
    role_distribution: dict = Field(description="User count by role")


class QuestionProgressResponse(BaseModel):
    total: int = Field(description="Total number of questions")
    by_difficulty: dict = Field(description="Question count by difficulty")


class SystemSettings(BaseModel):
    piston_url: str = Field(default="http://piston:2000/api/v2")
    piston_timeout: int = Field(default=30)
    piston_memory_limit: str = Field(default="256m")
    piston_cpu_limit: str = Field(default="0.5")
    enabled_languages: List[str] = Field(default=["python", "javascript", "java", "c"])


class SettingsUpdateRequest(BaseModel):
    piston_url: Optional[str] = None
    piston_timeout: Optional[int] = None
    piston_memory_limit: Optional[str] = None
    piston_cpu_limit: Optional[str] = None
    enabled_languages: Optional[List[str]] = None
