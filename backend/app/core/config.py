from typing import List, Optional, Union
from pydantic import Field, validator
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Database Settings
    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "https://localhost:3000",
            "https://*.vercel.app",
        ]
    )

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Security Settings
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1", "*.vercel.app"]
    )

    # Supabase Settings
    SUPABASE_URL: str = Field(..., env="SUPABASE_URL")
    SUPABASE_KEY: str = Field(..., env="SUPABASE_KEY")
    SUPABASE_JWT_SECRET: str = Field(..., env="SUPABASE_JWT_SECRET")

    # External API Keys
    NVIDIA_API_KEY: Optional[str] = Field(default=None, env="NVIDIA_API_KEY")
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # CodeCoach AI Configuration
    NVIDIA_BASE_URL: str = Field(default="https://integrate.api.nvidia.com/v1", env="NVIDIA_BASE_URL")
    PISTON_API_URL: str = Field(default="https://emkc.org/api/v2/piston", env="PISTON_API_URL")
    RATE_LIMIT_COACH_PER_MINUTE: int = Field(default=10, env="RATE_LIMIT_COACH_PER_MINUTE")
    RATE_LIMIT_RUN_PER_MINUTE: int = Field(default=20, env="RATE_LIMIT_RUN_PER_MINUTE")

    # Environment
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")

    # Sentry
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()