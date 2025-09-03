from fastapi import APIRouter, Depends

from src.api.depends import check_user_token, service_workspace_depends
from src.api.handlers import LoggingRoute
from src.dto.api.workspace import CreateWorkspaceByUserRequest
from src.dto.workspace import CreateWorkspacePayload
from src.models.user import UserModel
from src.models.workspace import WorkspaceModel
from src.service.workspace import WorkspaceService

workspace_route = APIRouter(prefix="/workspace", route_class=LoggingRoute)


@workspace_route.post("/create")
async def create_workspace_from_user(
    request_model: CreateWorkspaceByUserRequest,
    user_model: UserModel = Depends(check_user_token),
    workspace_service: WorkspaceService = Depends(service_workspace_depends),
) -> WorkspaceModel:
    return await workspace_service.create_workspace_by_user(
        user_model.id,
        CreateWorkspacePayload(
            name=request_model.name,
            organization_id=request_model.organization_id,
        ),
    )

