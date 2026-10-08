from abc import ABC, abstractmethod
from uuid import UUID

from hourtime.domain.entities import Project


class ProjectRepository(ABC):
    @abstractmethod
    async def get_by_id(self, project_id: UUID) -> Project | None: ...

    @abstractmethod
    async def list_for_workspace(
        self, workspace_id: UUID, *, include_archived: bool = False
    ) -> list[Project]: ...

    @abstractmethod
    async def find_by_name(self, workspace_id: UUID, name: str) -> Project | None:
        """Look up an active project by name, case-insensitively."""

    @abstractmethod
    async def add(self, project: Project) -> Project: ...

    @abstractmethod
    async def update(self, project: Project) -> Project: ...

    @abstractmethod
    async def delete(self, project_id: UUID) -> None: ...
