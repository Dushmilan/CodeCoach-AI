"""Unit tests for structured logging (Phase 1: baseline stdlib JSON)."""

import io
import json
import logging

import pytest


def test_setup_logging_production_emits_json(monkeypatch):
    from app.core import logging as app_logging

    monkeypatch.setenv("LOG_LEVEL", "INFO")
    stream = io.StringIO()

    root = logging.getLogger()
    old_handlers = root.handlers[:]
    old_level = root.level
    try:
        app_logging.setup_logging(environment="production", stream=stream)
        logging.getLogger("phase1.probe").info("hello-phase1")
        line = stream.getvalue().strip().splitlines()[-1]
        payload = json.loads(line)
        assert payload["message"] == "hello-phase1"
        assert payload["level"] == "INFO"
        assert payload["logger"] == "phase1.probe"
    finally:
        root.handlers = old_handlers
        root.level = old_level


def test_setup_logging_redacts_secrets(monkeypatch):
    from app.core import logging as app_logging

    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("JWT_SECRET_KEY", "super-secret-jwt-value")
    stream = io.StringIO()

    root = logging.getLogger()
    old_handlers = root.handlers[:]
    old_level = root.level
    try:
        app_logging.setup_logging(environment="production", stream=stream)
        logging.getLogger("phase1.secret").info(
            "connecting with key=%s", "super-secret-jwt-value"
        )
        out = stream.getvalue()
        assert "super-secret-jwt-value" not in out
        assert "***" in out
    finally:
        root.handlers = old_handlers
        root.level = old_level


def test_setup_logging_nonprod_emits_text_and_respects_level(monkeypatch):
    from app.core import logging as app_logging

    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    stream = io.StringIO()

    root = logging.getLogger()
    old_handlers = root.handlers[:]
    old_level = root.level
    try:
        app_logging.setup_logging(environment="testing", stream=stream)
        logging.getLogger("phase1.noise").info("suppressed-info")
        logging.getLogger("phase1.sig").warning("visible-warning")
        out = stream.getvalue()
        assert "suppressed-info" not in out
        assert "visible-warning" in out
        with pytest.raises(json.JSONDecodeError):
            json.loads(out.strip().splitlines()[-1])
    finally:
        root.handlers = old_handlers
        root.level = old_level
