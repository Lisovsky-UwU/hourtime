"""Cache contract.

This lives in `infrastructure`, not `interfaces`, on purpose: caching is a
storage detail and no use case is allowed to know it exists.
"""

from abc import ABC, abstractmethod


class CacheClient(ABC):
    @abstractmethod
    async def get(self, key: str) -> str | None: ...

    @abstractmethod
    async def set(self, key: str, value: str, ttl_seconds: int) -> None: ...

    @abstractmethod
    async def delete(self, *keys: str) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...
