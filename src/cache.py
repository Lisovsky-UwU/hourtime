from contextlib import asynccontextmanager

import aiocache
from loguru import logger

from src.exceptions import ConfigurationError


class AppCacher:

    _cache_instance: aiocache.BaseCache | None = None

    @classmethod
    def setup_cache(cls):
        cls._cache_instance = aiocache.SimpleMemoryCache()

    @classmethod
    @asynccontextmanager
    async def cacher_factory(cls):
        if cls._cache_instance is None:
            logger.critical("Cache instance is not initialized")
            raise ConfigurationError(
                2,
                "Configuration cache error",
                "Cache instance is not initialized",
            )

        yield cls._cache_instance

    @classmethod
    async def cache_depends(cls):
        async with cls.cacher_factory() as cacher:
            yield cacher

    @classmethod
    async def close_cache(cls):
        if cls._cache_instance is not None:
            await cls._cache_instance.clear()
            await cls._cache_instance.close()

