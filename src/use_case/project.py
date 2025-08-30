import abc

from src.dto.project import CreateProjectPayload
from src.models.project import ProjectModel


class ProjectUseCase(abc.ABC):

    @abc.abstractmethod
    async def create_project(self, payload: CreateProjectPayload) -> ProjectModel:
        ...

