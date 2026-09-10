import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError

from hourtime.infrastructure.cache.base import CacheClient

logger = logging.getLogger(__name__)


class RedisCache(CacheClient):
    """Redis-backed cache that degrades to "no cache" instead of failing requests.

    A cache outage should slow the API down, never take it offline — every
    reader falls through to the database on error.
    """

    def __init__(self, client: Redis) -> None:
        self._client = client

    @classmethod
    def from_url(cls, url: str) -> "RedisCache":
        return cls(Redis.from_url(url, decode_responses=True))

    async def get(self, key: str) -> str | None:
        try:
            value = await self._client.get(key)
        except RedisError:
            logger.warning("cache read failed for %s", key, exc_info=True)
            return None
        return str(value) if value is not None else None

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            return
        try:
            await self._client.set(key, value, ex=ttl_seconds)
        except RedisError:
            logger.warning("cache write failed for %s", key, exc_info=True)

    async def delete(self, *keys: str) -> None:
        if not keys:
            return
        try:
            await self._client.delete(*keys)
        except RedisError:
            # A stale entry that cannot be dropped is a security problem, so
            # this one is worth an error-level line.
            logger.error("cache invalidation failed for %s", keys, exc_info=True)

    async def close(self) -> None:
        await self._client.aclose()
