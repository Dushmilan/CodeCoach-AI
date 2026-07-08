import os
from typing import Callable
from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize rate limiter — used by FastAPI app.state.limiter
limiter = Limiter(key_func=get_remote_address)


def _rate_limit(env_key: str, default: str) -> Callable[[], str]:
    """Deferred rate limit string — reads env var at request time."""
    return lambda: os.getenv(env_key, default)


COACH_RATE_LIMIT: Callable[[], str] = _rate_limit("COACH_RATE_LIMIT", "10/minute")
RUN_RATE_LIMIT: Callable[[], str] = _rate_limit("RUN_RATE_LIMIT", "30/minute")
QUESTIONS_RATE_LIMIT: Callable[[], str] = _rate_limit(
    "QUESTIONS_RATE_LIMIT", "100/minute"
)
