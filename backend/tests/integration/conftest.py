"""Set env vars before any app imports to ensure rate limits apply in tests."""

import os

os.environ["COACH_RATE_LIMIT"] = "1000/minute"
os.environ["RUN_RATE_LIMIT"] = "1000/minute"
os.environ["REDIS_ENABLED"] = "false"
os.environ["USER_RATE_LIMIT_PER_MINUTE"] = "1000"
