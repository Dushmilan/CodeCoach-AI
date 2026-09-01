"""Unit tests for WorkspaceService — Redis-backed draft code + chat + last-visited."""

import pytest
from app.services.workspace_service import WorkspaceService


class FakeCache:
    def __init__(self):
        self.store: dict[str, object] = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value, ttl: int = 300):
        self.store[key] = value

    async def delete(self, pattern: str):
        self.store.pop(pattern, None)
        return 1


@pytest.mark.asyncio
async def test_save_and_get_code(monkeypatch):
    monkeypatch.setenv("REDIS_TTL_WORKSPACE", "604800")
    cache = FakeCache()
    svc = WorkspaceService(cache)  # type: ignore[arg-type]
    await svc.save_code("u1", "q1", "python", "print('hi')")
    data = await svc.get_code("u1", "q1", "python")
    assert data is not None
    assert data["code"] == "print('hi')"
    assert data["language"] == "python"
    assert "updated_at" in data
    meta = await svc.get_meta("u1", "q1")
    assert meta is not None
    assert meta["language"] == "python"
    last = await svc.get_last_visited("u1")
    assert last is not None
    assert last["question_id"] == "q1"


@pytest.mark.asyncio
async def test_get_code_missing_returns_none():
    cache = FakeCache()
    svc = WorkspaceService(cache)  # type: ignore[arg-type]
    assert await svc.get_code("u1", "q-missing", "python") is None


@pytest.mark.asyncio
async def test_delete_code():
    cache = FakeCache()
    svc = WorkspaceService(cache)  # type: ignore[arg-type]
    await svc.save_code("u1", "q1", "python", "code")
    await svc.delete_code("u1", "q1", "python")
    assert await svc.get_code("u1", "q1", "python") is None


@pytest.mark.asyncio
async def test_graceful_no_cache():
    svc = WorkspaceService(cache=None)
    await svc.save_code("u1", "q1", "python", "code")
    assert await svc.get_code("u1", "q1", "python") is None
    assert await svc.get_chat("u1", "q1") == []
    assert await svc.get_last_visited("u1") is None
    await svc.append_chat("u1", "q1", [{"role": "user", "content": "hi"}])
    await svc.clear_chat("u1", "q1")
    await svc.delete_code("u1", "q1", "python")


@pytest.mark.asyncio
async def test_chat_append_and_get():
    cache = FakeCache()
    svc = WorkspaceService(cache)  # type: ignore[arg-type]
    await svc.append_chat("u1", "q1", [{"role": "user", "content": "hello"}])
    await svc.append_chat(
        "u1",
        "q1",
        [{"role": "assistant", "content": "hi there", "structured": {"summary": "s"}}],
    )
    msgs = await svc.get_chat("u1", "q1")
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["structured"]["summary"] == "s"


@pytest.mark.asyncio
async def test_chat_cap_truncation():
    cache = FakeCache()
    svc = WorkspaceService(cache)  # type: ignore[arg-type]
    svc.max_chat_messages = 3
    for i in range(5):
        await svc.append_chat("u1", "q1", [{"role": "user", "content": f"msg {i}"}])
    msgs = await svc.get_chat("u1", "q1")
    assert len(msgs) == 3
    assert msgs[0]["content"] == "msg 2"
    assert msgs[-1]["content"] == "msg 4"


@pytest.mark.asyncio
async def test_chat_content_truncation():
    cache = FakeCache()
    svc = WorkspaceService(cache)  # type: ignore[arg-type]
    svc.max_chat_chars = 5
    await svc.append_chat("u1", "q1", [{"role": "user", "content": "123456789"}])
    msgs = await svc.get_chat("u1", "q1")
    assert msgs[0]["content"] == "12345"


@pytest.mark.asyncio
async def test_clear_chat():
    cache = FakeCache()
    svc = WorkspaceService(cache)  # type: ignore[arg-type]
    await svc.append_chat("u1", "q1", [{"role": "user", "content": "hi"}])
    await svc.clear_chat("u1", "q1")
    assert await svc.get_chat("u1", "q1") == []


@pytest.mark.asyncio
async def test_last_visited():
    cache = FakeCache()
    svc = WorkspaceService(cache)  # type: ignore[arg-type]
    await svc.set_last_visited("u1", "q42", "java")
    data = await svc.get_last_visited("u1")
    assert data["question_id"] == "q42"
    assert data["language"] == "java"
    assert "visited_at" in data


@pytest.mark.asyncio
async def test_oversized_code_not_saved():
    cache = FakeCache()
    svc = WorkspaceService(cache)  # type: ignore[arg-type]
    svc.max_code_bytes = 5
    await svc.save_code("u1", "q1", "python", "123456")
    assert await svc.get_code("u1", "q1", "python") is None
