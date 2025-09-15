from aiocache import BaseCache
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache import AppCacher
from src.cache_constants import CacheConst
from src.database import DataBaseSession


class DatabaseRepositoryMixin:

    def __init__(
        self,
        session: AsyncSession = Depends(DataBaseSession.session_depends),
        cacher: BaseCache = Depends(AppCacher.cache_depends),
    ) -> None:
        self.session = session
        self.cacher = cacher

    async def _clear_cache_for_organization(self, organization_id: int) -> None:
        await self.cacher.clear(
            namespace=CacheConst.Organization.NamespaceOrganization.format(organization_id),
        )

