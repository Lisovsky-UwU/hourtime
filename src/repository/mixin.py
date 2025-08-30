from sqlalchemy.ext.asyncio import AsyncSession


class DatabaseRepositoryMixin:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

