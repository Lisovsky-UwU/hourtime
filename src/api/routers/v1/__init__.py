from fastapi import APIRouter

api_v1_route = APIRouter(prefix="/v1")


from .auth import auth_route

api_v1_route.include_router(auth_route)

