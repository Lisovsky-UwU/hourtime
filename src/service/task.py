from aiocache.lock import uuid

from src.dto.task import CreateTaskPayload, TaskInWorkspace, UpdateTaskPayload
from src.exceptions.defined import ORGANIZATION_ACCESS_ERROR
from src.exceptions.types import NotFoundError
from src.models.common import UserAccess
from src.models.task import TaskModel
from src.use_case.task import TaskUseCase
from src.use_case.workspace import WorkspaceUseCase


class TaskService:

    def __init__(
        self,
        task_repository: TaskUseCase,
        workspace_repository: WorkspaceUseCase,
    ) -> None:
        self.task_repository = task_repository
        self.workspace_repository = workspace_repository

    async def _get_user_access(self, user_id: int, workspace_id: int) -> UserAccess:
        user_access = await self.workspace_repository.get_user_access(
            user_id,
            workspace_id,
        )
        if user_access is None:
            raise ORGANIZATION_ACCESS_ERROR

        return user_access

    async def create_task_by_user(self, user_id: int, payload: CreateTaskPayload) -> TaskModel:
        user_access = await self._get_user_access(user_id, payload.workspace_id)
        if user_access is UserAccess.PARTIAL:
            raise ORGANIZATION_ACCESS_ERROR

        return await self.task_repository.create_task(payload)

    async def get_for_workspace_by_user(
        self,
        user_id: int,
        workspace_id: int,
    ) -> list[TaskInWorkspace]:
        await self._get_user_access(user_id, workspace_id)
        return await self.task_repository.get_by_workspace(workspace_id)

    async def update_by_user(self, user_id: int, payload: UpdateTaskPayload) -> TaskModel:
        task_model = await self.task_repository.get_by_id(payload.id)
        user_access = await self._get_user_access(user_id, task_model.workspace_id)
        if user_access is UserAccess.PARTIAL:
            raise ORGANIZATION_ACCESS_ERROR

        return await self.task_repository.update_task(payload)

    async def delete_by_user(self, user_id: int, task_id: uuid.UUID) -> None:
        task_model = await self.task_repository.get_by_id(task_id)
        user_access = await self._get_user_access(user_id, task_model.workspace_id)
        if user_access is UserAccess.PARTIAL:
            raise ORGANIZATION_ACCESS_ERROR

        try:
            await self.task_repository.delete_task(task_id)
        except NotFoundError as exc:
            raise ORGANIZATION_ACCESS_ERROR from exc

