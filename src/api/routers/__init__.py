from fastapi import APIRouter

api_route = APIRouter(prefix="/api")


from .system import system_route
from .v1 import api_v1_route

api_route.include_router(system_route)
api_route.include_router(api_v1_route)

