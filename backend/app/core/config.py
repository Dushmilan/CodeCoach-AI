from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./codecoach.db"
    USE_DATABASE: bool = False
    
    # Auth
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    NVIDIA_API_KEY: Optional[str] = None
    
    # Piston
    PISTON_API_URL: str = "http://piston:2000/api/v2"

@lru_cache
def get_settings() -> Settings:
    return Settings()
