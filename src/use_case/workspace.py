import abc

from src.dto.workspace import CreateWorkspacePayload
from src.models.workspace import WorkspaceModel


class WorkspaceUseCase(abc.ABC):

    @abc.abstractmethod
    async def create_workspace(self, payload: CreateWorkspacePayload) -> WorkspaceModel:
        ...

    @abc.abstractmethod
    async def get_by_organization(self, organization_id: int) -> list[WorkspaceModel]:
        ...

