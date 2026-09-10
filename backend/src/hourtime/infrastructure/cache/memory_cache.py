import time

from hourtime.infrastructure.cache.base import CacheClient


class InMemoryCache(CacheClient):
    """Process-local cache for tests and single-worker development.

    Entries die with the process and are not shared between workers, which is
    exactly why Redis is the default in production.
    """

    def __init__(self) -> None:
        self._entries: dict[str, tuple[float, str]] = {}

    def _now(self) -> float:
        return time.monotonic()

    async def get(self, key: str) -> str | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if expires_at <= self._now():
            self._entries.pop(key, None)
            return None
        return value

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            return
        self._entries[key] = (self._now() + ttl_seconds, value)

    async def delete(self, *keys: str) -> None:
        for key in keys:
            self._entries.pop(key, None)

    async def close(self) -> None:
        self._entries.clear()
