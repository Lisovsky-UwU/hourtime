from fastapi import APIRouter, Depends

from src.api.depends import check_user_token, service_workspace_depends
from src.api.handlers import LoggingRoute
from src.dto.api.common import ResultResponse
from src.dto.api.workspace import CreateWorkspaceByUserRequest, UpdateWorkspaceByUserRequest
from src.dto.workspace import CreateWorkspacePayload, UpdateWorkspacePayload
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

@workspace_route.put("/update")
async def update_workspace_from_user(
    request_model: UpdateWorkspaceByUserRequest,
    user_model: UserModel = Depends(check_user_token),
    workspace_service: WorkspaceService = Depends(service_workspace_depends),
) -> WorkspaceModel:
    return await workspace_service.update_workspace_by_user(
        user_model.id,
        UpdateWorkspacePayload(
            workspace_id=request_model.workspace_id,
            name=request_model.name,
        ),
    )

@workspace_route.delete("/delete")
async def delete_workspace_from_user(
    workspace_id: int,
    user_model: UserModel = Depends(check_user_token),
    workspace_service: WorkspaceService = Depends(service_workspace_depends),
) -> ResultResponse:
    await workspace_service.delete_workspace_by_user(
        user_model.id,
        workspace_id,
    )
    return ResultResponse()

