import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional
from pydantic import model_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./codecoach.db"
    USE_DATABASE: bool = False

    # Auth
    JWT_SECRET_KEY: str = ""
    NVIDIA_API_KEY: Optional[str] = None

    @model_validator(mode="after")
    def _require_jwt_key_in_production(self):
        env = os.getenv("ENVIRONMENT", "development")
        if env == "production" and not self.JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY must be set in production")
        return self

    # Piston
    PISTON_API_URL: str = "http://piston:2000/api/v2"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_TTL_DEFAULT: int = 300
    REDIS_TTL_STATIC: int = 3600
    REDIS_TTL_AI: int = 86400
    REDIS_TTL_EXECUTION: int = 3600
    REDIS_ENABLED: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
