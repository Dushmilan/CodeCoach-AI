"""In-process rate limiter — maintained drop-in replacement for slowapi.

slowapi (0.1.9) is unmaintained since 2022 (audit M-08 / SEC-3). This module
provides the same public surface the app already uses:

- ``limiter`` singleton with a ``limit(limit_value)`` decorator
- lazy, env-driven limit strings (``COACH_RATE_LIMIT()`` etc.)
- ``RateLimitExceeded`` exception + ``_rate_limit_exceeded_handler`` (429)
- ``app.state.limiter.reset()`` for test isolation

The store is an in-process sliding window keyed by client IP. That matches
slowapi's in-memory default behaviour; if multi-process sharing is ever needed,
swap the store for a Redis-backed one without touching any decorator call site.
"""

import inspect
import os
import time
from collections import defaultdict, deque
from functools import wraps
from inspect import signature
from typing import Callable, Deque, Optional, Union

from fastapi import Request
from starlette.responses import JSONResponse, Response

# Units supported by slowapi/limits strings: "10/minute", "100/hour", etc.
_UNIT_SECONDS = {
    "second": 1,
    "minute": 60,
    "hour": 3600,
    "day": 86400,
}


class RateLimitExceeded(Exception):
    """Raised when a request exceeds its configured limit."""

    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(detail)
        self.detail = detail


def get_remote_address(request: Request) -> str:
    """Client IP used as the limit key (127.0.0.1 when unavailable)."""
    if not request.client or not request.client.host:
        return "127.0.0.1"
    return request.client.host


def _parse_limit(limit_value: str) -> tuple[int, int]:
    """Parse ``"10/minute"`` -> (amount, window_seconds)."""
    try:
        amount_str, unit = limit_value.split("/")
        amount = int(amount_str)
        window = _UNIT_SECONDS[unit]
    except (ValueError, KeyError) as e:
        raise ValueError(
            f"Invalid rate limit {limit_value!r}; expected e.g. '10/minute'"
        ) from e
    if amount <= 0:
        raise ValueError(f"Rate limit amount must be positive: {limit_value!r}")
    return amount, window


class Limiter:
    """Per-IP sliding-window rate limiter.

    Keeps a timestamp deque per (IP, limit-string) pair; requests older than
    the window are pruned before counting. ``reset()`` clears all counters.
    """

    # Cap on tracked keys so a distributed IP flood cannot grow memory without
    # bound. Past the cap, expired windows are swept; if still over, the store
    # is cleared (fail-open: limiter resets rather than OOM).
    _MAX_KEYS = 10_000

    def __init__(self, key_func: Callable[[Request], str] = get_remote_address):
        self.key_func = key_func
        self.enabled = True
        # key -> (window_seconds, deque of monotonic event timestamps)
        self._windows: dict[str, tuple[int, Deque[float]]] = defaultdict(
            lambda: (0, deque())
        )

    def reset(self) -> None:
        self._windows.clear()

    def _sweep_expired(self, now: float) -> None:
        """Drop expired keys when the store grows near the cap; clears if the
        flood outpaces expiry (fail-open rather than OOM). Runs only when the
        store is large so the common case stays O(1)."""
        if len(self._windows) < self._MAX_KEYS // 2:
            return
        expired = [
            key
            for key, (window, events) in self._windows.items()
            if not events or now - events[-1] >= window
        ]
        for key in expired:
            del self._windows[key]
        if len(self._windows) > self._MAX_KEYS:
            self._windows.clear()

    def check(
        self, request: Request, limit_value: Union[str, Callable[[], str]]
    ) -> None:
        """Record one hit; raise RateLimitExceeded when the window is full."""
        if not self.enabled:
            return
        limit_str = limit_value() if callable(limit_value) else limit_value
        amount, window_seconds = _parse_limit(limit_str)
        key = f"{self.key_func(request)}|{limit_str}"
        now = time.monotonic()
        window, events = self._windows[key]
        if window != window_seconds:
            window = window_seconds
            self._windows[key] = (window, events)
        while events and now - events[0] >= window:
            events.popleft()
        if len(events) >= amount:
            raise RateLimitExceeded(
                f"Rate limit exceeded: {amount} per 1 {limit_str.split('/')[1]}"
            )
        events.append(now)
        self._sweep_expired(now)

    def limit(
        self, limit_value: Union[str, Callable[[], str]]
    ) -> Callable[[Callable], Callable]:
        """Decorator applying the limit to an endpoint.

        The decorated endpoint must accept a ``request: Request`` parameter
        (FastAPI injects it) — same requirement as slowapi.
        """

        def decorator(func: Callable) -> Callable:
            # Locate the request parameter to pull it from kwargs/args.
            request_index: Optional[int] = None
            for idx, name in enumerate(signature(func).parameters):
                if name == "request":
                    request_index = idx
                    break
            if request_index is None:
                raise ValueError(
                    f"@limiter.limit requires a `request: Request` parameter "
                    f"on {func.__module__}.{func.__name__}"
                )

            if inspect.iscoroutinefunction(func):

                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    request = kwargs.get("request")
                    if request is None and args:
                        request = args[request_index]
                    self.check(request, limit_value)
                    return await func(*args, **kwargs)

                return async_wrapper

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                request = kwargs.get("request")
                if request is None and args:
                    request = args[request_index]
                self.check(request, limit_value)
                return func(*args, **kwargs)

            return sync_wrapper

        return decorator


# Lazy, env-driven limit strings (read at request time).
def _rate_limit(env_key: str, default: str) -> Callable[[], str]:
    return lambda: os.getenv(env_key, default)


COACH_RATE_LIMIT: Callable[[], str] = _rate_limit("COACH_RATE_LIMIT", "10/minute")
COACH_WARM_RATE_LIMIT: Callable[[], str] = _rate_limit(
    "COACH_WARM_RATE_LIMIT", "30/minute"
)
RUN_RATE_LIMIT: Callable[[], str] = _rate_limit("RUN_RATE_LIMIT", "30/minute")
QUESTIONS_RATE_LIMIT: Callable[[], str] = _rate_limit(
    "QUESTIONS_RATE_LIMIT", "100/minute"
)

# Singleton used by routers and app.state.limiter.
limiter = Limiter()


async def _rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> Response:
    """429 response for the in-process limiter."""
    return JSONResponse({"error": exc.detail}, status_code=429)
