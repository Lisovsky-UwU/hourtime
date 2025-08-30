import asyncio
from contextlib import asynccontextmanager

from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)

from src.config import app_config
from src.exceptions import BaseHourtimeException, ConfigurationError


class DataBaseSession:
    _engine: AsyncEngine | None = None

    @classmethod
    def create_engine(cls, connection_string: str | None = None):
        if connection_string is None:
            connection_string = app_config.db_postgres.connection_string
        try:
            logger.trace("Creating database engine")
            cls._engine = create_async_engine(connection_string)
            logger.trace("Database engine created successfully")
        except Exception as exc:
            logger.exception("Failed to create database engine")
            raise ConfigurationError(
                2,
                "Database connection error",
                f"Failed to connect to the database: {exc}",
            ) from exc

    @classmethod
    async def close_engine(cls):
        if cls._engine is not None:
            await cls._engine.dispose()
            cls._engine = None
            logger.trace("Database engine disposed")

    @classmethod
    def session_factory(cls, autoflush: bool = False, expire_on_commit: bool = False):
        if cls._engine is None:
            logger.critical("Database engine is not initialized")
            raise ConfigurationError(
                1,
                "Configuration database error",
                "The connection string is not set for the database",
            )

        return async_scoped_session(
            async_sessionmaker(
                bind=cls._engine,
                autoflush=autoflush,
                expire_on_commit=expire_on_commit,
            ),
            scopefunc=asyncio.current_task,
        )

    @classmethod
    @asynccontextmanager
    async def get_session(cls, autoflush: bool = False, expire_on_commit: bool = False):
        session = cls.session_factory(autoflush=autoflush, expire_on_commit=expire_on_commit)
        try:
            yield session
            await session.commit()
        except Exception as exc:
            await session.rollback()
            if not isinstance(exc, BaseHourtimeException):
                logger.exception("Session transaction failed: {}", exc)
            raise
        finally:
            await session.close()

