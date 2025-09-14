import abc

from src.dto.project import CreateProjectPayload, UpdateProjectPayload
from src.models.project import ProjectModel


class ProjectUseCase(abc.ABC):

    @abc.abstractmethod
    async def create_project(self, payload: CreateProjectPayload) -> ProjectModel:
        ...

    @abc.abstractmethod
    async def get_by_workspace(self, workspace_id: int) -> list[ProjectModel]:
        ...

    @abc.abstractmethod
    async def get_by_id(self, project_id: int) -> ProjectModel:
        ...

    @abc.abstractmethod
    async def update_project(self, payload: UpdateProjectPayload) -> ProjectModel:
        ...

    @abc.abstractmethod
    async def delete_project(self, project_id: int) -> None:
        ...

