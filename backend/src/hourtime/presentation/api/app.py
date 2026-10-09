import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager, suppress
from datetime import UTC, datetime
from importlib.metadata import version

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from hourtime.config import Settings, get_settings
from hourtime.infrastructure.cache import CacheClient, InMemoryCache, RedisCache
from hourtime.infrastructure.db.engine import build_engine, build_sessionmaker
from hourtime.infrastructure.security.argon2_hasher import Argon2PasswordHasher
from hourtime.presentation.api.deps import build_purge_expired_sessions
from hourtime.presentation.api.errors import register_error_handlers
from hourtime.presentation.api.routers import (
    auth,
    clients,
    projects,
    reports,
    tags,
    time_entries,
    workspaces,
)

logger = logging.getLogger(__name__)

API_PREFIX = "/api/v1"
SERVER_TIME_HEADER = "X-Server-Time"


def build_cache(settings: Settings) -> CacheClient:
    if settings.cache_backend == "redis":
        return RedisCache.from_url(settings.redis_url)
    return InMemoryCache()


async def purge_sessions_once(app: FastAPI) -> int:
    async with app.state.sessionmaker() as session:
        use_case = build_purge_expired_sessions(session, app.state.cache, app.state.settings)
        return await use_case.execute()


async def _retention_loop(app: FastAPI) -> None:
    interval = app.state.settings.session_purge_interval_hours * 3600
    while True:
        try:
            removed = await purge_sessions_once(app)
            if removed:
                logger.info("purged %s expired sessions", removed)
        except asyncio.CancelledError:
            raise
        except Exception:
            # Retention must never take the API down with it.
            logger.exception("session retention sweep failed")
        await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())

    engine = build_engine(settings)
    app.state.settings = settings
    app.state.engine = engine
    app.state.sessionmaker = build_sessionmaker(engine)
    app.state.cache = build_cache(settings)
    app.state.password_hasher = Argon2PasswordHasher()

    retention = asyncio.create_task(_retention_loop(app))
    try:
        yield
    finally:
        retention.cancel()
        with suppress(asyncio.CancelledError):
            await retention
        await app.state.cache.close()
        await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Hourtime API",
        version=version("hourtime"),
        lifespan=lifespan,
        docs_url=f"{API_PREFIX}/docs",
        openapi_url=f"{API_PREFIX}/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        # Auth rides on the Authorization header, not cookies.
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        # Without this the browser hides the header from the frontend.
        expose_headers=[SERVER_TIME_HEADER],
    )

    @app.middleware("http")
    async def stamp_server_time(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Lets the client correct for a skewed local clock when ticking timers."""
        response = await call_next(request)
        response.headers[SERVER_TIME_HEADER] = datetime.now(UTC).isoformat()
        return response

    register_error_handlers(app)

    @app.get(f"{API_PREFIX}/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "server_time": datetime.now(UTC).isoformat()}

    for router in (
        auth.router,
        clients.router,
        projects.router,
        reports.router,
        tags.router,
        time_entries.router,
        workspaces.router,
    ):
        app.include_router(router, prefix=API_PREFIX)

    return app


app = create_app()
