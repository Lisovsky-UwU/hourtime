from aiocache import BaseCache
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache import AppCacher
from src.database import DataBaseSession


class DatabaseRepositoryMixin:

    def __init__(
        self,
        session: AsyncSession = Depends(DataBaseSession.session_depends),
        cacher: BaseCache = Depends(AppCacher.cache_depends),
    ) -> None:
        self.session = session
        self.cacher = cacher

