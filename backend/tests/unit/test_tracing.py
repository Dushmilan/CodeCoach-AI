"""Unit tests for OpenTelemetry tracing (Phase 3: OTel export)."""


def test_build_tracer_provider_honors_sampler_ratio():
    from app.core import tracing as app_tracing

    dropped = app_tracing.build_tracer_provider(
        endpoint="http://localhost:4318", sampler_ratio=0.0
    )
    sampled = app_tracing.build_tracer_provider(
        endpoint="http://localhost:4318", sampler_ratio=1.0
    )

    assert "TraceIdRatioBased{0.0" in dropped.sampler.get_description()
    assert "TraceIdRatioBased{1.0" in sampled.sampler.get_description()


def test_otel_settings_default_to_disabled(monkeypatch, tmp_path):
    from app.core.config import get_settings

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.delenv("OTEL_ENABLED", raising=False)
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://codecoach:codecoach@127.0.0.1:5432/codecoach"
    )
    settings = get_settings()
    assert settings.OTEL_ENABLED is False
    assert settings.OTEL_EXPORTER_OTLP_ENDPOINT == "http://localhost:4318"
    assert settings.OTEL_SAMPLER_RATIO == 1.0


def test_middleware_creates_span_and_logs_trace_ids(monkeypatch):
    import io
    import json
    import logging

    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )

    from app.core import logging as app_logging
    from app.core import tracing as app_tracing
    from app.middleware.request_id import RequestIDMiddleware

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    monkeypatch.setattr(app_tracing, "_ENABLED", True)

    monkeypatch.setenv("LOG_LEVEL", "INFO")
    stream = io.StringIO()
    root = logging.getLogger()
    old_handlers = root.handlers[:]
    old_level = root.level
    try:
        app_logging.setup_logging(environment="production", stream=stream)

        app = FastAPI()

        @app.get("/items")
        async def items():
            return {"ok": True}

        app.add_middleware(RequestIDMiddleware)
        resp = TestClient(app).get("/items")
        assert resp.status_code == 200
        generated = resp.headers["X-Request-ID"]

        spans = exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].name == "GET /items"

        parsed = [json.loads(line) for line in stream.getvalue().strip().splitlines()]
        egress = next(p for p in parsed if p.get("message") == "http.request")
        assert egress["request_id"] == generated
        assert egress["trace_id"] == format(spans[0].context.trace_id, "032x")
        assert egress["span_id"] == format(spans[0].context.span_id, "016x")
    finally:
        root.handlers = old_handlers
        root.level = old_level


def test_tracing_disabled_by_default_and_failures_never_break_requests(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.core import tracing as app_tracing
    from app.middleware.request_id import RequestIDMiddleware

    assert app_tracing.setup_tracing() is False
    assert app_tracing.is_enabled() is False

    monkeypatch.setattr(
        "opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no collector")),
    )
    assert app_tracing.setup_tracing(enabled=True) is False
    assert app_tracing.is_enabled() is False

    monkeypatch.setattr(app_tracing, "_ENABLED", True)
    monkeypatch.setattr(
        "opentelemetry.trace.get_tracer",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("broken tracer")),
    )

    app = FastAPI()

    @app.get("/probe")
    async def probe():
        return {"ok": True}

    app.add_middleware(RequestIDMiddleware)
    resp = TestClient(app).get("/probe")
    assert resp.status_code == 200
    assert resp.headers["X-Request-ID"]
