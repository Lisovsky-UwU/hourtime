"""Test wiring.

The environment is pointed at a throwaway database and the in-process cache
*before* anything imports the app, so no test can reach the development data.
"""

import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent

TEST_DATABASE_URL = os.environ.get(
    "HOURTIME_TEST_DATABASE_URL",
    "postgresql+psycopg://hourtime:hourtime@localhost:5432/hourtime_test",
)

os.environ["HOURTIME_DATABASE_URL"] = TEST_DATABASE_URL
os.environ["HOURTIME_CACHE_BACKEND"] = "memory"
os.environ["HOURTIME_ALLOW_REGISTRATION"] = "true"
os.environ["HOURTIME_PASSWORD_MIN_LENGTH"] = "10"

import httpx  # noqa: E402
import pytest  # noqa: E402
import sqlalchemy as sa  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi import FastAPI  # noqa: E402

from hourtime.infrastructure.asyncio_compat import use_selector_event_loop  # noqa: E402
from hourtime.presentation.api.app import API_PREFIX, create_app  # noqa: E402

# psycopg's async driver refuses to run on the default Windows event loop.
use_selector_event_loop()

TABLES = ("sessions", "time_entries", "projects", "workspaces", "users")


@pytest.fixture(scope="session")
def database() -> Iterator[None]:
    """Recreate the test database once per run and migrate it to head.

    Going through alembic rather than `metadata.create_all` means every test
    run also proves the migrations still apply.
    """
    url = sa.engine.make_url(TEST_DATABASE_URL)
    admin_engine = sa.create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        connection.execute(sa.text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))
        connection.execute(sa.text(f'CREATE DATABASE "{url.database}"'))
    admin_engine.dispose()

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    command.upgrade(config, "head")

    yield


@pytest.fixture
async def app(database: None) -> AsyncIterator[FastAPI]:
    application = create_app()
    # ASGITransport does not run lifespan events, so drive them by hand.
    async with application.router.lifespan_context(application):
        async with application.state.sessionmaker() as session:
            await session.execute(
                sa.text(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE")
            )
            await session.commit()
        yield application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url=f"http://testserver{API_PREFIX}"
    ) as http_client:
        yield http_client
