from abc import ABC, abstractmethod
from uuid import UUID

from hourtime.domain.entities import Client


class ClientRepository(ABC):
    @abstractmethod
    async def get_by_id(self, client_id: UUID) -> Client | None: ...

    @abstractmethod
    async def list_for_workspace(
        self, workspace_id: UUID, *, include_archived: bool = False
    ) -> list[Client]: ...

    @abstractmethod
    async def find_by_name(self, workspace_id: UUID, name: str) -> Client | None:
        """Look up an active client by name, case-insensitively."""

    @abstractmethod
    async def add(self, client: Client) -> Client: ...

    @abstractmethod
    async def update(self, client: Client) -> Client: ...

    @abstractmethod
    async def delete(self, client_id: UUID) -> None:
        """Remove the client; its projects stay, with no client attached."""
