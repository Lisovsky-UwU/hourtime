from abc import ABC, abstractmethod
from uuid import UUID

from hourtime.domain.entities import Task


class TaskRepository(ABC):
    @abstractmethod
    async def get_by_id(self, task_id: UUID) -> Task | None: ...

    @abstractmethod
    async def list_for_workspace(
        self,
        workspace_id: UUID,
        *,
        project_id: UUID | None = None,
        include_completed: bool = False,
    ) -> list[Task]: ...

    @abstractmethod
    async def find_by_name(self, project_id: UUID, name: str) -> Task | None:
        """Look up an active task by name, case-insensitively."""

    @abstractmethod
    async def add(self, task: Task) -> Task: ...

    @abstractmethod
    async def update(self, task: Task) -> Task: ...

    @abstractmethod
    async def delete(self, task_id: UUID) -> None: ...
