"""Unit tests for request-ID middleware (Phase 2: correlation)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_request_id_propagated_and_visible_to_handler():
    from app.middleware.request_id import RequestIDMiddleware, get_request_id

    seen = {}

    app = FastAPI()

    @app.get("/probe")
    async def probe():
        seen["request_id"] = get_request_id()
        return {"ok": True}

    app.add_middleware(RequestIDMiddleware)

    client = TestClient(app)
    resp = client.get("/probe", headers={"X-Request-ID": "req-123"})
    assert resp.status_code == 200
    assert resp.headers["X-Request-ID"] == "req-123"
    assert seen["request_id"] == "req-123"


def test_request_id_generated_and_logged_with_egress_fields(monkeypatch):
    import io
    import json
    import logging

    from app.core import logging as app_logging
    from app.middleware.request_id import RequestIDMiddleware

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
        assert generated

        lines = stream.getvalue().strip().splitlines()
        parsed = [json.loads(line) for line in lines]
        egress = next(p for p in parsed if p.get("message") == "http.request")
        assert egress["request_id"] == generated
        assert egress["method"] == "GET"
        assert egress["path"] == "/items"
        assert egress["status"] == 200
        assert egress["latency_ms"] >= 0
    finally:
        root.handlers = old_handlers
        root.level = old_level


def test_request_id_does_not_leak_across_requests_and_logging_never_raises():
    import io
    import json
    import logging

    from app.core import logging as app_logging
    from app.middleware.request_id import RequestIDMiddleware, get_request_id

    assert get_request_id() is None

    stream = io.StringIO()
    root = logging.getLogger()
    old_handlers = root.handlers[:]
    old_level = root.level
    try:
        app_logging.setup_logging(environment="production", stream=stream)

        app = FastAPI()

        @app.get("/probe")
        async def probe():
            return {"request_id": get_request_id()}

        app.add_middleware(RequestIDMiddleware)
        client = TestClient(app)

        first = client.get("/probe", headers={"X-Request-ID": "req-A"}).headers[
            "X-Request-ID"
        ]
        second = client.get("/probe").headers["X-Request-ID"]
        assert first == "req-A"
        assert second and second != "req-A"

        # Outside any request: logging works, correlation keys degrade to "-".
        logging.getLogger("phase2.outside").info("no-context")
        payload = json.loads(stream.getvalue().strip().splitlines()[-1])
        assert payload["request_id"] == "-"
    finally:
        root.handlers = old_handlers
        root.level = old_level
        assert get_request_id() is None
