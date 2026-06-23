"""Redis caching service with graceful degradation.

All cache keys follow: codecoach:{namespace}:{rest}
Uses connection pooling and is safe for concurrent use.
"""

import hashlib
import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis
from redis.asyncio.connection import ConnectionPool

logger = logging.getLogger(__name__)


def _content_hash(*parts: str) -> str:
    """SHA-256 of normalized parts, truncated to 16 hex chars."""
    normalized = ":".join(parts)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


class RedisCache:
    """Async Redis cache client with connection pooling and graceful degradation."""

    def __init__(self, redis_url: str, max_connections: int = 20):
        self._pool = ConnectionPool.from_url(redis_url, max_connections=max_connections)
        self._enabled = True

    async def _client(self) -> Optional[aioredis.Redis]:
        """Get a Redis client from the pool if enabled."""
        if not self._enabled:
            return None
        try:
            return aioredis.Redis(connection_pool=self._pool)
        except Exception as e:
            logger.warning("Redis client creation failed: %s", e)
            self._enabled = False
            return None

    def disable(self) -> None:
        """Graceful degradation — disable caching without raising."""
        self._enabled = False

    async def get(self, key: str) -> Optional[Any]:
        """Return deserialized value or None on miss/error."""
        client = await self._client()
        if not client:
            return None
        try:
            raw = await client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except aioredis.RedisError as e:
            logger.warning("Redis get failed for key %s: %s", key, e)
            self.disable()
            return None
        finally:
            await client.aclose()

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Serialize and store value with TTL (seconds). Silently skip on error."""
        client = await self._client()
        if not client:
            return
        try:
            raw = json.dumps(value, default=str)
            await client.setex(key, ttl, raw)
        except aioredis.RedisError as e:
            logger.warning("Redis set failed for key %s: %s", key, e)
            self.disable()
        finally:
            await client.aclose()

    async def delete(self, pattern: str) -> int:
        """Delete all keys matching glob pattern. Returns number deleted."""
        client = await self._client()
        if not client:
            return 0
        try:
            keys = await client.keys(pattern)
            if keys:
                count = await client.delete(*keys)
                return count
            return 0
        except aioredis.RedisError as e:
            logger.warning("Redis delete failed for pattern %s: %s", pattern, e)
            self.disable()
            return 0
        finally:
            await client.aclose()

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        client = await self._client()
        if not client:
            return False
        try:
            return await client.exists(key) > 0
        except aioredis.RedisError as e:
            logger.warning("Redis exists check failed for key %s: %s", key, e)
            return False
        finally:
            await client.aclose()

    async def ttl(self, key: str) -> int:
        """Return remaining TTL in seconds. -1 if no TTL, -2 if key missing."""
        client = await self._client()
        if not client:
            return -2
        try:
            return await client.ttl(key)
        except aioredis.RedisError as e:
            logger.warning("Redis ttl check failed for key %s: %s", key, e)
            return -2
        finally:
            await client.aclose()

    async def close(self) -> None:
        """Close the connection pool."""
        if not hasattr(self, "_pool") or self._pool is None:
            return
        try:
            await self._pool.disconnect()
        except Exception as e:
            logger.debug("Redis pool disconnect note: %s", e)

    @staticmethod
    def key(*parts: str) -> str:
        """Build namespaced cache key: codecoach:{parts[0]}:{parts[1]}:..."""
        return f"codecoach:{':'.join(parts)}"
