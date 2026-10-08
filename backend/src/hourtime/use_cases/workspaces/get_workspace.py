from uuid import UUID

from hourtime.domain.entities import Workspace
from hourtime.domain.errors import NotFound
from hourtime.interfaces.repositories import WorkspaceRepository


class GetWorkspace:
    def __init__(self, workspaces: WorkspaceRepository) -> None:
        self._workspaces = workspaces

    async def execute(self, workspace_id: UUID) -> Workspace:
        workspace = await self._workspaces.get_by_id(workspace_id)
        if workspace is None:
            raise NotFound("Workspace not found")
        return workspace
