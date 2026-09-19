# Tracing (OpenTelemetry, opt-in)

Phase 3 of production logging (#209). Request spans export via OTLP/HTTP;
logs already carry `trace_id`/`span_id` (Phase 2), `-` until this is enabled.

## Enable

```bash
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318  # OTLP/HTTP receiver
OTEL_SAMPLER_RATIO=1.0                             # 0.0-1.0, e.g. 0.1 in prod
```

Default is **off** — the app runs on NoOp spans with zero export traffic.

## Backend choices (all free software; only hosting/ingest can cost)

- **Local dev:** Grafana Tempo, Jaeger (`jaeger --config` with OTLP enabled),
  or the OTel Collector → any of those. Point the endpoint above at it.
- **Managed:** Grafana Cloud, Honeycomb, Datadog, AWS X-Ray — all accept OTLP.

## Production guidance

- Start with `OTEL_SAMPLER_RATIO=0.1` (10%); raise only while debugging.
- Export runs on a background batch thread with retries; if the backend is
  down, requests still succeed (spans are dropped after retries).
- If `setup_tracing` itself fails (bad endpoint, missing packages), startup
  logs a warning and continues with tracing disabled — never a crash.
