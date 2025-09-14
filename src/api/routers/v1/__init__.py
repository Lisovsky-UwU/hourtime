from fastapi import APIRouter

api_v1_route = APIRouter(prefix="/v1")


from .auth import auth_route
from .organization import organization_router
from .project import project_router
from .user import user_route
from .workspace import workspace_route

api_v1_route.include_router(auth_route)
api_v1_route.include_router(organization_router)
api_v1_route.include_router(project_router)
api_v1_route.include_router(user_route)
api_v1_route.include_router(workspace_route)

