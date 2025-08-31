from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import DataBaseSession


class DatabaseRepositoryMixin:

    def __init__(
        self,
        session: AsyncSession = Depends(DataBaseSession.session_generator_for_depends),
    ) -> None:
        self.session = session

