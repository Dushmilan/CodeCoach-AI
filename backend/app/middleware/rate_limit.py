import os
from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize rate limiter — used by FastAPI app.state.limiter
limiter = Limiter(key_func=get_remote_address)

COACH_RATE_LIMIT = os.getenv("COACH_RATE_LIMIT", "10/minute")
RUN_RATE_LIMIT = os.getenv("RUN_RATE_LIMIT", "30/minute")
QUESTIONS_RATE_LIMIT = os.getenv("QUESTIONS_RATE_LIMIT", "100/minute")
