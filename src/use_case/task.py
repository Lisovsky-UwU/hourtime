import abc
import uuid

from src.dto.task import CreateTaskPayload, TaskInWorkspace, UpdateTaskPayload
from src.models.task import TaskModel


class TaskUseCase(abc.ABC):

    @abc.abstractmethod
    async def create_task(self, payload: CreateTaskPayload) -> TaskModel:
        ...

    @abc.abstractmethod
    async def get_by_id(self, task_id: uuid.UUID, return_deleted: bool = False) -> TaskModel:
        ...

    @abc.abstractmethod
    async def get_by_workspace(self, workspace_id: int) -> list[TaskInWorkspace]:
        ...

    @abc.abstractmethod
    async def update_task(self, payload: UpdateTaskPayload) -> TaskModel:
        ...

    @abc.abstractmethod
    async def delete_task(self, task_id: uuid.UUID) -> None:
        ...

