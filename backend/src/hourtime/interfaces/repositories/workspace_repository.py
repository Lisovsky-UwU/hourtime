from abc import ABC, abstractmethod

from hourtime.domain.entities import Workspace


class WorkspaceRepository(ABC):
    @abstractmethod
    async def add(self, workspace: Workspace) -> Workspace: ...
