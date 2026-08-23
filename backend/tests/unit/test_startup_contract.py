"""Unit tests for application startup behaviour.

Verifies the migration-only startup contract: the lifespan must NEVER run
schema DDL (``create_all`` etc.), must not require a reachable database to boot,
and must wire up Redis when enabled.
"""

import logging

import pytest


class TestStartupDoesNotMutateSchema:
    @pytest.mark.asyncio
    async def test_lifespan_never_runs_ddl_and_inits_redis(self, monkeypatch):
        import app.core.database as database_module

        logging.disable(logging.CRITICAL)
        try:
            executed: list[str] = []

            class _FakeResult:
                def __init__(self, value):
                    self.value = value

                def scalar_one(self):
                    return self.value

            class _FakeSession:
                async def __aenter__(self):
                    return self

                async def __aexit__(self, *args):
                    return None

                async def execute(self, stmt):
                    executed.append(str(stmt).lower())
                    return _FakeResult(False)

            class _FakeMaker:
                def __call__(self):
                    return _FakeSession()

            monkeypatch.setattr(database_module, "async_session_maker", _FakeMaker())

            redis_calls = {"init": 0, "close": 0}

            class _FakeRedisCache:
                def __init__(self, url):
                    redis_calls["init"] += 1

                async def close(self):
                    redis_calls["close"] += 1

            monkeypatch.setattr("app.main.RedisCache", _FakeRedisCache)

            from app.main import app, settings

            monkeypatch.setattr(settings, "REDIS_ENABLED", True)

            async with app.router.lifespan_context(app):
                assert redis_calls["init"] == 1
            assert redis_calls["close"] == 1

            assert executed, "expected the migration check to hit the DB"
            for stmt in executed:
                assert "create" not in stmt
                assert "drop" not in stmt
        finally:
            logging.disable(logging.NOTSET)

    @pytest.mark.asyncio
    async def test_lifespan_starts_without_database(self, monkeypatch):
        import app.core.database as database_module

        logging.disable(logging.CRITICAL)
        try:

            class _ExplodingSession:
                async def __aenter__(self):
                    raise RuntimeError("database unreachable")

                async def __aexit__(self, *args):
                    return None

            class _ExplodingMaker:
                def __call__(self):
                    return _ExplodingSession()

            monkeypatch.setattr(
                database_module, "async_session_maker", _ExplodingMaker()
            )

            monkeypatch.setattr(
                "app.main.RedisCache",
                lambda url: type(
                    "NoopRedis",
                    (),
                    {"close": (lambda self: None)},
                )(),
            )

            from app.main import app, settings

            monkeypatch.setattr(settings, "REDIS_ENABLED", False)

            async with app.router.lifespan_context(app):
                pass
        finally:
            logging.disable(logging.NOTSET)
