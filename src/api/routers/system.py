from fastapi import APIRouter

from src.api.handlers import LoggingRoute
from version import APP_VERSION

system_route = APIRouter(prefix="/system", route_class=LoggingRoute)


@system_route.get("/ping")
def ping() -> dict:
    return {
        "status": True,
        "version": APP_VERSION,
    }

