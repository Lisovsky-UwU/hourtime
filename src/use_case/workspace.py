import abc

from src.dto.workspace import CreateWorkspacePayload, UpdateWorkspacePayload
from src.models.common import UserAccess
from src.models.workspace import WorkspaceModel


class WorkspaceUseCase(abc.ABC):

    @abc.abstractmethod
    async def create_workspace(self, payload: CreateWorkspacePayload) -> WorkspaceModel:
        ...

    @abc.abstractmethod
    async def get_by_organization(self, organization_id: int) -> list[WorkspaceModel]:
        ...

    @abc.abstractmethod
    async def get_workspace_by_id(
        self,
        workspace_id: int,
        return_deleted: bool = False,
    ) -> WorkspaceModel:
        ...

    @abc.abstractmethod
    async def get_user_access(self, user_id: int, workspace_id: int) -> UserAccess | None:
        ...

    @abc.abstractmethod
    async def update_workspace(self, payload: UpdateWorkspacePayload) -> WorkspaceModel:
        ...

    @abc.abstractmethod
    async def delete_workspace(self, workspace_id: int) -> None:
        ...

