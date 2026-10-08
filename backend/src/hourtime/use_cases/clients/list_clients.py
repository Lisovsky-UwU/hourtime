from uuid import UUID

from hourtime.domain.entities import Client
from hourtime.interfaces.repositories import ClientRepository


class ListClients:
    def __init__(self, clients: ClientRepository) -> None:
        self._clients = clients

    async def execute(self, workspace_id: UUID, *, include_archived: bool = False) -> list[Client]:
        return await self._clients.list_for_workspace(
            workspace_id, include_archived=include_archived
        )
