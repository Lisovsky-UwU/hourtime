from fastapi import APIRouter, Depends

from src.api.depends import check_user_token, service_project_depends
from src.api.handlers import LoggingRoute
from src.dto.api.common import ResultResponse
from src.dto.api.project import CreateProjectRequest, UpdateProjectRequest
from src.dto.project import CreateProjectPayload, UpdateProjectPayload
from src.models.project import ProjectModel
from src.models.user import UserModel
from src.service.project import ProjectService

project_router = APIRouter(prefix="/project", route_class=LoggingRoute)


@project_router.post("/create")
async def create_project(
    request_model: CreateProjectRequest,
    user_model: UserModel = Depends(check_user_token),
    project_service: ProjectService = Depends(service_project_depends),
) -> ProjectModel:
    return await project_service.create_by_user(
        user_model.id,
        CreateProjectPayload(
            workspace_id=request_model.workspace_id,
            name=request_model.name,
            description=request_model.description,
        ),
    )

@project_router.get("/for_workspace")
async def get_projects_for_workspace(
    workspace_id: int,
    user_model: UserModel = Depends(check_user_token),
    project_service: ProjectService = Depends(service_project_depends),
) -> list[ProjectModel]:
    return await project_service.get_by_user_for_workspace(user_model.id, workspace_id)

@project_router.put("/update")
async def update_project(
    request_model: UpdateProjectRequest,
    user_model: UserModel = Depends(check_user_token),
    project_service: ProjectService = Depends(service_project_depends),
) -> ProjectModel:
    return await project_service.update_by_user(
        user_model.id,
        UpdateProjectPayload(
            project_id=request_model.project_id,
            name=request_model.name,
            description=request_model.description,
        ),
    )

@project_router.delete("/delete")
async def delete_project(
    project_id: int,
    user_model: UserModel = Depends(check_user_token),
    project_service: ProjectService = Depends(service_project_depends),
) -> ResultResponse:
    await project_service.delete_by_user(user_model.id, project_id)
    return ResultResponse()

