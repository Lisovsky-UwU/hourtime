from sqlalchemy.ext.asyncio import AsyncSession

from hourtime.interfaces.services import UnitOfWork


class SqlAlchemyUnitOfWork(UnitOfWork):
    """Transaction control for the one session bound to the current request."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def flush(self) -> None:
        await self._session.flush()
