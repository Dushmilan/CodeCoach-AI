"""Request-ID middleware — correlation for every request.

Reads an incoming ``X-Request-ID`` or generates one, binds it to a
:class:`contextvars.ContextVar` for the request lifetime, and echoes it back
on the response. Phase 3 (OTel) will also bind ``trace_id``/``span_id`` here.
"""

import logging
import time
import uuid
from contextvars import ContextVar
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"

request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_request_id() -> Optional[str]:
    """Return the request ID bound to the current context, if any."""
    return request_id_ctx.get()


class CorrelationFilter(logging.Filter):
    """Inject live ``request_id`` (and future OTel ``trace_id``/``span_id``).

    Runs before formatters so every record carries correlation keys even
    when the emitting code knows nothing about the current request.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if not getattr(record, "request_id", None):
            record.request_id = get_request_id() or "-"
        if not getattr(record, "trace_id", None):
            record.trace_id = "-"
        if not getattr(record, "span_id", None):
            record.span_id = "-"
        return True


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Bind and echo ``X-Request-ID`` for request correlation."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        token = request_id_ctx.set(request_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
            latency_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.info(
                "http.request",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "latency_ms": latency_ms,
                },
            )
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            request_id_ctx.reset(token)
