from uuid import UUID

from hourtime.interfaces.repositories import ClientRepository
from hourtime.interfaces.services import UnitOfWork
from hourtime.use_cases.access import get_workspace_client


class DeleteClient:
    """Removes a client; its projects survive with no client attached."""

    def __init__(self, clients: ClientRepository, uow: UnitOfWork) -> None:
        self._clients = clients
        self._uow = uow

    async def execute(self, workspace_id: UUID, client_id: UUID) -> None:
        client = await get_workspace_client(self._clients, workspace_id, client_id)
        await self._clients.delete(client.id)
        await self._uow.commit()
