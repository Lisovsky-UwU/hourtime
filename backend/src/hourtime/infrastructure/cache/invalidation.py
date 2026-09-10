"""Cache invalidation tied to the transaction boundary."""

from hourtime.infrastructure.cache.base import CacheClient


class DeferredInvalidation:
    """Drops cache keys twice: when the row changes, and again after the commit.

    Dropping them only before the commit is not enough on its own — a concurrent
    reader can repopulate the key from the row as it still looks pre-commit.
    Repeating the delete once the transaction lands closes that window.

    `CacheAwareUnitOfWork` is what performs the second pass, so nothing above
    the infrastructure layer has to know this dance exists.
    """

    def __init__(self, cache: CacheClient) -> None:
        self._cache = cache
        self._pending: set[str] = set()

    async def invalidate(self, *keys: str) -> None:
        if not keys:
            return
        self._pending.update(keys)
        await self._cache.delete(*keys)

    async def invalidate_pending(self) -> None:
        if not self._pending:
            return
        keys, self._pending = self._pending, set()
        await self._cache.delete(*keys)
