from abc import ABC, abstractmethod
from uuid import UUID

from hourtime.domain.entities import Workspace


class WorkspaceRepository(ABC):
    @abstractmethod
    async def get_by_id(self, workspace_id: UUID) -> Workspace | None: ...

    @abstractmethod
    async def add(self, workspace: Workspace) -> Workspace: ...

    @abstractmethod
    async def update(self, workspace: Workspace) -> Workspace: ...
