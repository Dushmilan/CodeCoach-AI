"""OpenTelemetry tracing (Phase 3: OTLP export, opt-in).

Disabled by default — :func:`setup_tracing` flips the module flag and
installs an SDK ``TracerProvider`` only when ``OTEL_ENABLED`` is set.
Every failure degrades to stdout logging + NoOp spans, never to a
broken request path.
"""

import logging

logger = logging.getLogger(__name__)

_ENABLED = False


def is_enabled() -> bool:
    """Whether request spans are created (set by :func:`setup_tracing`)."""
    return _ENABLED


def build_tracer_provider(endpoint: str, sampler_ratio: float = 1.0):
    """Build (but do not install) an OTLP-exporting ``TracerProvider``."""
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
        OTLPSpanExporter,
    )
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased

    exporter = OTLPSpanExporter(endpoint=f"{endpoint.rstrip('/')}/v1/traces")
    provider = TracerProvider(
        sampler=ParentBased(root=TraceIdRatioBased(sampler_ratio))
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    return provider


def setup_tracing(
    enabled: bool = False,
    endpoint: str = "http://localhost:4318",
    sampler_ratio: float = 1.0,
) -> bool:
    """Install the global OTLP tracer provider when enabled.

    Returns True when spans will be exported, False otherwise (disabled
    or any setup failure — the app keeps running on NoOp spans).
    """
    global _ENABLED
    if not enabled:
        _ENABLED = False
        return False
    try:
        from opentelemetry import trace

        trace.set_tracer_provider(build_tracer_provider(endpoint, sampler_ratio))
    except Exception as exc:  # noqa: BLE001 - tracing must never break the app
        logger.warning("OTel setup failed (%s) — tracing disabled", exc)
        _ENABLED = False
        return False
    _ENABLED = True
    return True
