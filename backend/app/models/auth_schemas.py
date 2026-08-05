from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    password: str = Field(..., min_length=6, max_length=100)


class UserLoginRequest(BaseModel):
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: datetime
    is_active: bool = True
    role: str = "user"
    plan: str = "free"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
    refresh_token: Optional[str] = Field(
        None, description="Long-lived refresh token for silent re-authentication"
    )


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token issued at login")


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None


class SupabaseAuthRequest(BaseModel):
    access_token: str


class UserInDB(BaseModel):
    id: str
    username: str
    email: str
    hashed_password: str
    created_at: datetime
    is_active: bool = True
    oauth_provider: Optional[str] = None
    oauth_id: Optional[str] = None
    role: str = "user"
    plan: str = "free"
