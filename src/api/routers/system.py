from fastapi import APIRouter

from version import APP_VERSION

system_route = APIRouter()


@system_route.get("/ping")
def ping() -> dict:
    return {
        "status": True,
        "version": APP_VERSION,
    }
