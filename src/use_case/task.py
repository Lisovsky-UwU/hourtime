import abc

from src.dto.task import CreateTaskPayload
from src.models.task import TaskModel


class TaskUseCase(abc.ABC):

    @abc.abstractmethod
    async def create_task(self, payload: CreateTaskPayload) -> TaskModel:
        ...

