from sqlalchemy.ext.asyncio import AsyncSession

from hourtime.infrastructure.cache.invalidation import DeferredInvalidation
from hourtime.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork


class CacheAwareUnitOfWork(SqlAlchemyUnitOfWork):
    """Commits, then lets every cache drop what the transaction changed.

    Use cases keep calling plain `commit()`; the coupling between the caches and
    the transaction boundary stays here in the infrastructure layer.
    """

    def __init__(self, session: AsyncSession, *caches: DeferredInvalidation) -> None:
        super().__init__(session)
        self._caches = caches

    async def commit(self) -> None:
        await super().commit()
        for cache in self._caches:
            await cache.invalidate_pending()
