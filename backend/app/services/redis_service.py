"""Redis caching service with graceful degradation.

All cache keys follow: codecoach:{namespace}:{rest}
Uses connection pooling and is safe for concurrent use.
"""

import hashlib
import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis
import redis.exceptions as redis_exc
from redis.asyncio.connection import ConnectionPool

logger = logging.getLogger(__name__)

#: Errors that mean the Redis server is unreachable (outage). Only these
#: trip the circuit breaker. Data errors (bad JSON, wrong types) are
#: per-key problems and must never disable the whole cache.
_CONNECTION_ERRORS = (
    redis_exc.ConnectionError,
    redis_exc.TimeoutError,
    TimeoutError,
    OSError,
)


def _is_connection_error(exc: BaseException) -> bool:
    """True when exc signals an unreachable Redis (vs. a bad value)."""
    return isinstance(exc, _CONNECTION_ERRORS)


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

    def _note_error(self, exc: Exception, op: str, key: str) -> None:
        """Log a cache failure; trip the breaker only on outages.

        Connection errors are operational events (warning + disable).
        Anything else is a per-key data problem (debug, stay enabled).
        """
        if _is_connection_error(exc):
            logger.warning("Redis %s failed for %s: %s", op, key, exc)
            self.disable()
        else:
            logger.debug("Redis %s failed for %s: %s", op, key, exc)

    async def get(self, key: str) -> Optional[Any]:
        """Return deserialized value or None on miss/error."""
        client = await self._client()
        if not client:
            return None
        try:
            raw = await client.get(key)
            if raw is None:
                return None
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                # Poison value, not an outage: drop the key, stay enabled.
                logger.warning("Redis dropping undecodable key %s: %s", key, e)
                try:
                    await client.delete(key)
                except Exception as del_e:
                    self._note_error(del_e, "delete-poison", key)
                return None
        except Exception as e:
            self._note_error(e, "get", key)
            return None
        finally:
            try:
                await client.aclose()
            except Exception:
                pass

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Serialize and store value with TTL (seconds). Silently skip on error."""
        client = await self._client()
        if not client:
            return
        try:
            raw = json.dumps(value, default=str)
            await client.setex(key, ttl, raw)
        except Exception as e:
            self._note_error(e, "set", key)
        finally:
            try:
                await client.aclose()
            except Exception:
                pass

    async def set_if_absent(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Atomically set key only if absent (SET NX EX). True if acquired."""
        client = await self._client()
        if not client:
            return False
        try:
            raw = json.dumps(value, default=str)
            acquired = await client.set(key, raw, ex=ttl, nx=True)
            return bool(acquired)
        except Exception as e:
            self._note_error(e, "set_if_absent", key)
            return False
        finally:
            try:
                await client.aclose()
            except Exception:
                pass

    _INCR_SCRIPT = (
        "local v = redis.call('INCR', KEYS[1]);"
        " if v == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]); end;"
        " return v;"
    )

    async def incr(self, key: str, ttl: int = 60) -> Optional[int]:
        """Atomically increment a counter, setting TTL on first increment.

        The INCR+EXPIRE runs as one Lua script so a crash between the two
        can never leak a TTL-less key. Returns the new value, or None on
        any error (caller must degrade gracefully). Used for per-user
        rate limiting.
        """
        client = await self._client()
        if not client:
            return None
        try:
            value = await client.eval(self._INCR_SCRIPT, 1, key, ttl)
            return int(value)
        except Exception as e:
            self._note_error(e, "incr", key)
            return None
        finally:
            try:
                await client.aclose()
            except Exception:
                pass

    async def delete(self, pattern: str) -> int:
        """Delete all keys matching glob pattern. Returns number deleted.

        Uses non-blocking SCAN (never KEYS) batched in 500-key deletes so
        catalog invalidation stays safe as the dataset grows.
        """
        client = await self._client()
        if not client:
            return 0
        try:
            removed = 0
            batch: list = []
            async for key in client.scan_iter(match=pattern, count=500):
                batch.append(key)
                if len(batch) >= 500:
                    removed += await client.delete(*batch)
                    batch = []
            if batch:
                removed += await client.delete(*batch)
            return removed
        except Exception as e:
            self._note_error(e, "delete", pattern)
            return 0
        finally:
            try:
                await client.aclose()
            except Exception:
                pass

    async def decr(self, key: str) -> Optional[int]:
        """Atomically decrement a counter, returning the new value.

        Returns None on any error (caller must degrade gracefully). Used to
        refund a slot when a rate-limit INCR pushes a counter past its cap.
        """
        client = await self._client()
        if not client:
            return None
        try:
            value = await client.decr(key)
            return int(value)
        except Exception as e:
            self._note_error(e, "decr", key)
            return None
        finally:
            try:
                await client.aclose()
            except Exception:
                pass

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        client = await self._client()
        if not client:
            return False
        try:
            return await client.exists(key) > 0
        except Exception as e:
            self._note_error(e, "exists", key)
            return False
        finally:
            try:
                await client.aclose()
            except Exception:
                pass

    async def ttl(self, key: str) -> int:
        """Return remaining TTL in seconds. -1 if no TTL, -2 if key missing."""
        client = await self._client()
        if not client:
            return -2
        try:
            return await client.ttl(key)
        except Exception as e:
            self._note_error(e, "ttl", key)
            return -2
        finally:
            try:
                await client.aclose()
            except Exception:
                pass

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
