from sqlalchemy.ext.asyncio import AsyncSession

from hourtime.infrastructure.db.repositories.cached_session_repository import (
    CachedSessionRepository,
)
from hourtime.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork


class CacheAwareUnitOfWork(SqlAlchemyUnitOfWork):
    """Commits, then lets the session cache drop what the transaction changed.

    Use cases keep calling plain `commit()`; the coupling between the cache and
    the transaction boundary stays here in the infrastructure layer.
    """

    def __init__(self, session: AsyncSession, sessions: CachedSessionRepository) -> None:
        super().__init__(session)
        self._sessions = sessions

    async def commit(self) -> None:
        await super().commit()
        await self._sessions.invalidate_pending()
