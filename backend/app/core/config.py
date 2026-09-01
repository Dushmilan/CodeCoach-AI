from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pydantic import model_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Environment (fail-closed: unset = production for security gates)
    ENVIRONMENT: str = "production"

    # Database (Supabase/PostgreSQL is the ONLY database). No default — an
    # unconfigured deployment must fail loudly rather than hit a local DB.
    DATABASE_URL: str = ""
    # Optional Postgres schema used for tests (Supabase has one database).
    DATABASE_SEARCH_PATH: Optional[str] = None

    # Auth
    JWT_SECRET_KEY: str = ""

    # Groq (primary AI provider for coaching)
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL_EASY: str = "openai/gpt-oss-20b"
    GROQ_MODEL_MEDIUM: str = "openai/gpt-oss-120b"
    GROQ_MODEL_HARD: str = "openai/gpt-oss-120b"
    GROQ_MODEL_STREAM: str = "openai/gpt-oss-20b"
    GROQ_MODEL_ANIMATE: str = "openai/gpt-oss-120b"

    # Per-user token metering (daily caps)
    DAILY_TOKEN_INPUT_CAP: int = 250_000
    DAILY_TOKEN_OUTPUT_CAP: int = 125_000

    # Per-plan daily request caps (number of AI calls per user per day)
    FREE_DAILY_REQUEST_CAP: int = 20
    PRO_DAILY_REQUEST_CAP: int = 500

    # Per-user request rate limit (requests per minute)
    USER_RATE_LIMIT_PER_MINUTE: int = 60

    # Background coach-context warming on question enter (kill-switch)
    COACH_WARM_ENABLED: bool = True

    # Abuse detection thresholds
    ABUSE_MULTI_ACCOUNT_MIN_ACCOUNTS: int = 3
    ABUSE_BURST_MIN_EVENTS: int = 20
    ABUSE_REPEAT_MIN_EVENTS: int = 10

    @model_validator(mode="after")
    def _require_jwt_key_in_production(self):
        if self.ENVIRONMENT == "production" and not self.JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY must be set in production")
        return self

    @model_validator(mode="after")
    def _require_supabase_only_database(self):
        # Supabase/PostgreSQL is the only allowed database. Anything else (or a
        # missing value) is a misconfiguration and must fail loudly at startup
        # instead of silently falling back to a legacy driver (MySQL/SQLite/etc).
        if not self.DATABASE_URL:
            raise ValueError(
                "DATABASE_URL is required (Supabase/PostgreSQL connection string)"
            )
        supported = self.DATABASE_URL.startswith(
            "postgresql:"
        ) or self.DATABASE_URL.startswith("postgresql+")
        if not supported:
            raise ValueError(
                "DATABASE_URL must point at Supabase/PostgreSQL "
                "(postgresql:// or postgresql+...://); "
                "got an unsupported scheme"
            )
        # Supabase/pooler URLs use the bare `postgresql://` scheme, which
        # SQLAlchemy maps to psycopg2 by default. The app is async, so force
        # the asyncpg driver.
        if self.DATABASE_URL.startswith("postgresql://"):
            self.DATABASE_URL = self.DATABASE_URL.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        return self

    # Piston
    PISTON_API_URL: str = "http://piston:2000/api/v2"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_TTL_DEFAULT: int = 300
    REDIS_TTL_STATIC: int = 3600
    REDIS_TTL_AI: int = 86400
    REDIS_TTL_EXECUTION: int = 3600
    REDIS_TTL_WORKSPACE: int = 604800  # 7 days — draft code + last-visited
    REDIS_TTL_CHAT: int = 604800  # 7 days — per-question chat history
    REDIS_TTL_LAST_EXEC: int = 604800  # 7 days — last execution / submit snapshot
    REDIS_ENABLED: bool = True
    WORKSPACE_CODE_MAX_BYTES: int = 51200
    CHAT_HISTORY_MAX_MESSAGES: int = 20
    CHAT_MESSAGE_MAX_CHARS: int = 5000


def get_settings() -> Settings:
    """Construct fresh settings — no caching so env overrides (e.g. from test
    fixtures) take effect and runtime env changes are picked up."""
    return Settings()


def is_production() -> bool:
    """Fail-closed environment check: unset ENVIRONMENT = production."""
    return get_settings().ENVIRONMENT == "production"
