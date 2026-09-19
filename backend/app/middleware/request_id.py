"""Request-ID middleware — correlation for every request.

Reads an incoming ``X-Request-ID`` or generates one, binds it to a
:class:`contextvars.ContextVar` for the request lifetime, and echoes it back
on the response. When OTel tracing is enabled, also opens a server span and
binds ``trace_id``/``span_id`` so logs and traces correlate.
"""

import logging
import time
import uuid
from contextlib import nullcontext
from contextvars import ContextVar
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"

request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
trace_id_ctx: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
span_id_ctx: ContextVar[Optional[str]] = ContextVar("span_id", default=None)


def get_request_id() -> Optional[str]:
    """Return the request ID bound to the current context, if any."""
    return request_id_ctx.get()


def get_trace_id() -> Optional[str]:
    """Return the OTel trace ID bound to the current context, if any."""
    return trace_id_ctx.get()


def get_span_id() -> Optional[str]:
    """Return the OTel span ID bound to the current context, if any."""
    return span_id_ctx.get()


class CorrelationFilter(logging.Filter):
    """Inject live ``request_id`` (and future OTel ``trace_id``/``span_id``).

    Runs before formatters so every record carries correlation keys even
    when the emitting code knows nothing about the current request.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if not getattr(record, "request_id", None):
            record.request_id = get_request_id() or "-"
        if not getattr(record, "trace_id", None):
            record.trace_id = get_trace_id() or "-"
        if not getattr(record, "span_id", None):
            record.span_id = get_span_id() or "-"
        return True


def _maybe_request_span(request: Request):
    """Return a server-span context manager, or a null one when disabled.

    Never raises — tracing must not break the request path.
    """
    try:
        from app.core import tracing as app_tracing

        if not app_tracing.is_enabled():
            return nullcontext(None)
        from opentelemetry import trace

        return trace.get_tracer(__name__).start_as_current_span(
            f"{request.method} {request.url.path}",
            kind=trace.SpanKind.SERVER,
        )
    except Exception:  # noqa: BLE001 - tracing must never break the app
        return nullcontext(None)


def _bind_span_ids(span) -> list:
    """Bind the span's IDs to contextvars; return (var, token) pairs."""
    bound = []
    try:
        if span is not None and span.is_recording():
            span_context = span.get_span_context()
            bound.append(
                (trace_id_ctx, trace_id_ctx.set(format(span_context.trace_id, "032x")))
            )
            bound.append(
                (span_id_ctx, span_id_ctx.set(format(span_context.span_id, "016x")))
            )
    except Exception:  # noqa: BLE001 - tracing must never break the app
        pass
    return bound


def _record_span(request: Request, status_code: int, span) -> None:
    """Attach HTTP attributes to the span. Never raises."""
    try:
        if span is not None and span.is_recording():
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.route", request.url.path)
            span.set_attribute("http.status_code", status_code)
    except Exception:  # noqa: BLE001 - tracing must never break the app
        pass


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Bind and echo ``X-Request-ID`` for request correlation."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        request_token = request_id_ctx.set(request_id)
        started = time.perf_counter()
        try:
            with _maybe_request_span(request) as span:
                span_tokens = _bind_span_ids(span)
                try:
                    response = await call_next(request)
                    latency_ms = round((time.perf_counter() - started) * 1000, 2)
                    _record_span(request, response.status_code, span)
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
                    for var, token in span_tokens:
                        var.reset(token)
        finally:
            request_id_ctx.reset(request_token)
