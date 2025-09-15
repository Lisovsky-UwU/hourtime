import uuid

from fastapi import APIRouter, Depends

from src.api.depends import check_user_token, service_task_depends
from src.api.handlers import LoggingRoute
from src.dto.api.common import ResultResponse
from src.dto.api.task import CreateTaskRequest, UpdateTaskRequest
from src.dto.task import CreateTaskPayload, TaskInWorkspace, UpdateTaskPayload
from src.models.task import TaskModel
from src.models.user import UserModel
from src.service.task import TaskService

task_router = APIRouter(prefix="/task", route_class=LoggingRoute)


@task_router.post("/create")
async def create_task_by_user(
    request_body: CreateTaskRequest,
    user_model: UserModel = Depends(check_user_token),
    task_service: TaskService = Depends(service_task_depends),
) -> TaskModel:
    return await task_service.create_task_by_user(
        user_model.id,
        CreateTaskPayload(
            name=request_body.name,
            description=request_body.description,
            workspace_id=request_body.workspace_id,
            project_id=request_body.project_id,
        ),
    )

@task_router.get("/for_workspace")
async def get_tasks_for_workspace_by_user(
    workspace_id: int,
    user_model: UserModel = Depends(check_user_token),
    task_service: TaskService = Depends(service_task_depends),
) -> list[TaskInWorkspace]:
    return await task_service.get_for_workspace_by_user(
        user_model.id,
        workspace_id,
    )

@task_router.put("/update")
async def update_task_by_user(
    request_body: UpdateTaskRequest,
    user_model: UserModel = Depends(check_user_token),
    task_service: TaskService = Depends(service_task_depends),
) -> TaskModel:
    return await task_service.update_by_user(
        user_model.id,
        UpdateTaskPayload(
            id=request_body.task_id,
            name=request_body.name,
            description=request_body.description,
        ),
    )

@task_router.delete("/delete")
async def delete_task_by_user(
    task_id: uuid.UUID,
    user_model: UserModel = Depends(check_user_token),
    task_service: TaskService = Depends(service_task_depends),
) -> ResultResponse:
    await task_service.delete_by_user(user_model.id, task_id)
    return ResultResponse()

