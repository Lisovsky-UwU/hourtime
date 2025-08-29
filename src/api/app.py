import uvicorn
from fastapi import FastAPI
from loguru import logger
from sqlalchemy.exc import OperationalError

from src.api.handlers import handle_app_exception, handle_database_error, handle_uncatch_exception
from src.api.routers import api_v1_route, system_route
from src.exceptions import BaseHourtimeException
from version import APP_VERSION


def build_app() -> FastAPI:
    logger.trace("Build API app")
    app = FastAPI(version=APP_VERSION, description="Hourtime app API")

    logger.trace("Registring router api/v1")
    app.include_router(api_v1_route)
    logger.trace("Registring router system")
    app.include_router(system_route)

    logger.trace("Registring exception handlers")
    app.add_exception_handler(Exception, handle_uncatch_exception)
    app.add_exception_handler(OperationalError, handle_database_error) # type: ignore
    app.add_exception_handler(BaseHourtimeException, handle_app_exception) # type: ignore

    return app


def start_api(host: str, port: int, ssl_cert_path: str | None, ssl_key_path: str | None) -> None:
    app = build_app()
    logger.success(
        "Run api on {protocol}://{host}:{port}",
        protocol="https" if ssl_cert_path and ssl_key_path else "http",
        host=host,
        port=port,
    )
    uvicorn.run(app, host=host, port=port, ssl_certfile=ssl_cert_path, ssl_keyfile=ssl_key_path)

