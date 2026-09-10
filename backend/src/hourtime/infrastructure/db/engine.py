import logging
import time
from typing import Any

from sqlalchemy import event, exc
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from hourtime.config import Settings

logger = logging.getLogger(__name__)

_LAST_USED = "_hourtime_returned_at"


def build_engine(settings: Settings) -> AsyncEngine:
    engine = create_async_engine(
        settings.database_url,
        echo=settings.sql_echo,
        # Not `pool_pre_ping`: that spends a full round trip validating a
        # connection on *every* checkout, which measured slower than the queries
        # it protects. `install_idle_ping` below buys the same safety, but only
        # for connections that have actually been sitting idle.
        pool_pre_ping=False,
        # A connection older than this is replaced silently on checkout, which
        # covers idle timeouts imposed by the database or a firewall.
        pool_recycle=settings.db_pool_recycle_seconds,
        pool_size=5,
        max_overflow=10,
    )
    install_idle_ping(engine, settings.db_ping_after_idle_seconds)
    return engine


def install_idle_ping(engine: AsyncEngine, idle_seconds: int) -> None:
    """Validate a pooled connection only once it has gone quiet.

    A connection handed back seconds ago is almost certainly still alive, so
    pinging it is pure latency. One that has been idle — across a database
    restart, say — is worth a `SELECT 1` before the request depends on it.

    Raising `DisconnectionError` from the checkout event is the retry: the pool
    discards that connection and hands out a fresh one, all before any of the
    request's own statements run.
    """
    if idle_seconds < 0:
        return

    @event.listens_for(engine.sync_engine, "checkin")
    def _stamp_return(dbapi_connection: Any, record: Any) -> None:
        setattr(record, _LAST_USED, time.monotonic())

    @event.listens_for(engine.sync_engine, "checkout")
    def _ping_if_idle(dbapi_connection: Any, record: Any, proxy: Any) -> None:
        returned_at = getattr(record, _LAST_USED, None)
        if returned_at is not None and time.monotonic() - returned_at < idle_seconds:
            return

        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("SELECT 1")
        except Exception:
            logger.warning("dropping a dead pooled connection", exc_info=True)
            # Tells the pool to discard this one and retry the checkout.
            raise exc.DisconnectionError() from None
        finally:
            cursor.close()


def build_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
