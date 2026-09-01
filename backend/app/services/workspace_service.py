"""Workspace + chat persistence backed by Redis.

Gracefully degrades when Redis is unavailable (cache is None or disabled):
all methods become no-ops / return None or empty lists, never raise.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.services.redis_service import RedisCache

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkspaceService:
    """Per-user workspace (draft code, last-visited, chat) stored in Redis."""

    def __init__(self, cache: Optional[RedisCache]):
        self.cache = cache
        settings = get_settings()
        self.ttl_workspace = settings.REDIS_TTL_WORKSPACE
        self.ttl_chat = settings.REDIS_TTL_CHAT
        self.ttl_last_exec = settings.REDIS_TTL_LAST_EXEC
        self.max_code_bytes = settings.WORKSPACE_CODE_MAX_BYTES
        self.max_chat_messages = settings.CHAT_HISTORY_MAX_MESSAGES
        self.max_chat_chars = settings.CHAT_MESSAGE_MAX_CHARS

    @staticmethod
    def _code_key(user_id: str, question_id: str, language: str) -> str:
        return RedisCache.key("workspace", "code", user_id, question_id, language)

    @staticmethod
    def _meta_key(user_id: str, question_id: str) -> str:
        return RedisCache.key("workspace", "meta", user_id, question_id)

    @staticmethod
    def _chat_key(user_id: str, question_id: str) -> str:
        return RedisCache.key("chat", user_id, question_id)

    @staticmethod
    def _last_visited_key(user_id: str) -> str:
        return RedisCache.key("workspace", "last_visited", user_id)

    @staticmethod
    def _last_exec_key(user_id: str, question_id: str, language: str) -> str:
        return RedisCache.key("exec", "last", user_id, question_id, language)

    @staticmethod
    def _last_submit_key(user_id: str, question_id: str) -> str:
        return RedisCache.key("submit", "last", user_id, question_id)

    async def save_code(
        self, user_id: str, question_id: str, language: str, code: str
    ) -> None:
        if not self.cache:
            return
        if len(code.encode("utf-8")) > self.max_code_bytes:
            logger.warning(
                "Workspace code too large: user=%s q=%s lang=%s bytes=%d",
                user_id,
                question_id,
                language,
                len(code.encode("utf-8")),
            )
            return
        payload = {"code": code, "language": language, "updated_at": _now_iso()}
        try:
            await self.cache.set(
                self._code_key(user_id, question_id, language),
                payload,
                ttl=self.ttl_workspace,
            )
            await self.cache.set(
                self._meta_key(user_id, question_id),
                {"language": language, "last_opened_at": _now_iso()},
                ttl=self.ttl_workspace,
            )
            await self.cache.set(
                self._last_visited_key(user_id),
                {
                    "question_id": question_id,
                    "language": language,
                    "visited_at": _now_iso(),
                },
                ttl=self.ttl_workspace,
            )
        except Exception as e:  # pragma: no cover
            logger.debug("save_code failed: %s", e)

    async def get_code(
        self, user_id: str, question_id: str, language: str
    ) -> Optional[Dict[str, Any]]:
        if not self.cache:
            return None
        try:
            return await self.cache.get(self._code_key(user_id, question_id, language))
        except Exception as e:  # pragma: no cover
            logger.debug("get_code failed: %s", e)
            return None

    async def delete_code(self, user_id: str, question_id: str, language: str) -> None:
        if not self.cache:
            return
        try:
            await self.cache.delete(self._code_key(user_id, question_id, language))
        except Exception as e:  # pragma: no cover
            logger.debug("delete_code failed: %s", e)

    async def get_meta(
        self, user_id: str, question_id: str
    ) -> Optional[Dict[str, Any]]:
        if not self.cache:
            return None
        try:
            return await self.cache.get(self._meta_key(user_id, question_id))
        except Exception as e:  # pragma: no cover
            logger.debug("get_meta failed: %s", e)
            return None

    async def get_last_visited(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not self.cache:
            return None
        try:
            return await self.cache.get(self._last_visited_key(user_id))
        except Exception as e:  # pragma: no cover
            logger.debug("get_last_visited failed: %s", e)
            return None

    async def set_last_visited(
        self, user_id: str, question_id: str, language: Optional[str] = None
    ) -> None:
        if not self.cache:
            return
        try:
            await self.cache.set(
                self._last_visited_key(user_id),
                {
                    "question_id": question_id,
                    "language": language,
                    "visited_at": _now_iso(),
                },
                ttl=self.ttl_workspace,
            )
        except Exception as e:  # pragma: no cover
            logger.debug("set_last_visited failed: %s", e)

    async def get_chat(self, user_id: str, question_id: str) -> List[Dict[str, Any]]:
        if not self.cache:
            return []
        try:
            data = await self.cache.get(self._chat_key(user_id, question_id))
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "messages" in data:
                return data["messages"]
            return []
        except Exception as e:  # pragma: no cover
            logger.debug("get_chat failed: %s", e)
            return []

    async def append_chat(
        self,
        user_id: str,
        question_id: str,
        messages: List[Dict[str, Any]],
    ) -> None:
        if not self.cache:
            return
        if not messages:
            return
        try:
            existing = await self.get_chat(user_id, question_id)
            incoming: List[Dict[str, Any]] = []
            for m in messages:
                role = m.get("role", "user")
                if role not in ("user", "assistant"):
                    continue
                content = str(m.get("content", ""))[: self.max_chat_chars]
                entry: Dict[str, Any] = {
                    "role": role,
                    "content": content,
                    "timestamp": m.get("timestamp") or _now_iso(),
                }
                if m.get("structured") is not None:
                    entry["structured"] = m["structured"]
                incoming.append(entry)
            combined = existing + incoming
            if len(combined) > self.max_chat_messages:
                combined = combined[-self.max_chat_messages :]
            await self.cache.set(
                self._chat_key(user_id, question_id), combined, ttl=self.ttl_chat
            )
        except Exception as e:  # pragma: no cover
            logger.debug("append_chat failed: %s", e)

    async def set_chat(
        self, user_id: str, question_id: str, messages: List[Dict[str, Any]]
    ) -> None:
        if not self.cache:
            return
        try:
            trimmed = (
                messages[-self.max_chat_messages :]
                if len(messages) > self.max_chat_messages
                else messages
            )
            normalized: List[Dict[str, Any]] = []
            for m in trimmed:
                role = m.get("role", "user")
                if role not in ("user", "assistant"):
                    continue
                normalized.append(
                    {
                        "role": role,
                        "content": str(m.get("content", ""))[: self.max_chat_chars],
                        "structured": m.get("structured"),
                        "timestamp": m.get("timestamp") or _now_iso(),
                    }
                )
            await self.cache.set(
                self._chat_key(user_id, question_id), normalized, ttl=self.ttl_chat
            )
        except Exception as e:  # pragma: no cover
            logger.debug("set_chat failed: %s", e)

    async def clear_chat(self, user_id: str, question_id: str) -> None:
        if not self.cache:
            return
        try:
            await self.cache.delete(self._chat_key(user_id, question_id))
        except Exception as e:  # pragma: no cover
            logger.debug("clear_chat failed: %s", e)

    async def set_last_exec(
        self, user_id: str, question_id: str, language: str, result: Dict[str, Any]
    ) -> None:
        if not self.cache:
            return
        try:
            await self.cache.set(
                self._last_exec_key(user_id, question_id, language),
                result,
                ttl=self.ttl_last_exec,
            )
        except Exception as e:  # pragma: no cover
            logger.debug("set_last_exec failed: %s", e)

    async def get_last_exec(
        self, user_id: str, question_id: str, language: str
    ) -> Optional[Dict[str, Any]]:
        if not self.cache:
            return None
        try:
            return await self.cache.get(
                self._last_exec_key(user_id, question_id, language)
            )
        except Exception as e:  # pragma: no cover
            logger.debug("get_last_exec failed: %s", e)
            return None

    async def set_last_submit(
        self, user_id: str, question_id: str, result: Dict[str, Any]
    ) -> None:
        if not self.cache:
            return
        try:
            await self.cache.set(
                self._last_submit_key(user_id, question_id),
                result,
                ttl=self.ttl_last_exec,
            )
        except Exception as e:  # pragma: no cover
            logger.debug("set_last_submit failed: %s", e)

    async def get_last_submit(
        self, user_id: str, question_id: str
    ) -> Optional[Dict[str, Any]]:
        if not self.cache:
            return None
        try:
            return await self.cache.get(self._last_submit_key(user_id, question_id))
        except Exception as e:  # pragma: no cover
            logger.debug("get_last_submit failed: %s", e)
            return None
