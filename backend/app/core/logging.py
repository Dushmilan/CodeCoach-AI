"""Structured logging (Phase 1: baseline stdlib JSON).

Production emits JSON to stdout (one object per line) so log collectors can
parse it. Non-production keeps a human-readable text format for local dev.
"""

import json
import logging
import os
import re
import sys
from datetime import datetime, timezone


_SECRET_ENV_KEYS = ("JWT_SECRET_KEY", "GROQ_API_KEY")
_REDACT_PATTERNS = (
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-~+/=]+"),
    re.compile(r"(?i)(password\s*[:=]\s*)\S+"),
)


def _redact_text(text: str) -> str:
    """Replace known secrets and secret-shaped patterns with ``***``."""
    if not isinstance(text, str):
        return text
    redacted = text
    for key in _SECRET_ENV_KEYS:
        secret = os.getenv(key, "")
        if secret and len(secret) >= 4 and secret in redacted:
            redacted = redacted.replace(secret, "***")
    for pattern in _REDACT_PATTERNS:
        redacted = pattern.sub(r"\1***", redacted)
    return redacted


class RedactingFilter(logging.Filter):
    """Strip secrets from the rendered message before any formatter runs."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            rendered = record.getMessage()
        except Exception:  # noqa: BLE001 - logging must never raise
            return True
        redacted = _redact_text(rendered)
        if redacted != rendered:
            record.msg = redacted
            record.args = ()
        return True


class JsonFormatter(logging.Formatter):
    """Format records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": _redact_text(record.getMessage()),
        }
        if record.exc_info and record.exc_info[0] is not None:
            payload["exc_info"] = _redact_text(self.formatException(record.exc_info))
        return json.dumps(payload, separators=(",", ":"))


def setup_logging(
    level: str | None = None,
    environment: str | None = None,
    stream=None,
) -> None:
    """Configure the root logger.

    Args:
        level: Log level name (defaults to ``LOG_LEVEL`` env, ``INFO``).
        environment: ``production`` emits JSON; anything else emits text.
            Defaults to the ``ENVIRONMENT`` env var (fail-closed: unset
            means production).
        stream: Output stream (defaults to ``sys.stdout``).
    """
    resolved_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    resolved_env = (environment or os.getenv("ENVIRONMENT", "production")).lower()
    out = stream if stream is not None else sys.stdout

    handler = logging.StreamHandler(out)
    handler.addFilter(RedactingFilter())
    if resolved_env == "production":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(getattr(logging, resolved_level, logging.INFO))
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
