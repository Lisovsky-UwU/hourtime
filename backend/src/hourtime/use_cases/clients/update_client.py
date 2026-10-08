from typing import Any

from hourtime.domain.entities import Client
from hourtime.domain.errors import ClientNameTaken, ValidationError
from hourtime.interfaces.repositories import ClientRepository
from hourtime.interfaces.services import Clock, UnitOfWork
from hourtime.use_cases.access import get_workspace_client
from hourtime.use_cases.dto import UpdateClientInput


class UpdateClient:
    """Renames and archives - everything PATCH /clients/{id} can do."""

    def __init__(self, clients: ClientRepository, clock: Clock, uow: UnitOfWork) -> None:
        self._clients = clients
        self._clock = clock
        self._uow = uow

    async def execute(self, data: UpdateClientInput) -> Client:
        client = await get_workspace_client(self._clients, data.workspace_id, data.client_id)
        now = self._clock.now()
        changes: dict[str, Any] = {}

        if data.provided("name"):
            if data.name is None:
                raise ValidationError("The name is required")
            name = data.name.strip()
            clash = await self._clients.find_by_name(data.workspace_id, name)
            if clash is not None and clash.id != client.id:
                raise ClientNameTaken
            changes["name"] = name

        if data.provided("archived"):
            if data.archived is None:
                raise ValidationError("The archived flag is required")
            changes["archived_at"] = now if data.archived else None

        if not changes:
            return client

        changes["updated_at"] = now
        updated = await self._clients.update(client.evolve(**changes))
        await self._uow.commit()
        return updated
