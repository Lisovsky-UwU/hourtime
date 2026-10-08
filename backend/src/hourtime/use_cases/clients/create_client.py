from uuid import uuid4

from hourtime.domain.entities import Client
from hourtime.domain.errors import ClientNameTaken
from hourtime.interfaces.repositories import ClientRepository
from hourtime.interfaces.services import Clock, UnitOfWork
from hourtime.use_cases.dto import CreateClientInput


class CreateClient:
    def __init__(self, clients: ClientRepository, clock: Clock, uow: UnitOfWork) -> None:
        self._clients = clients
        self._clock = clock
        self._uow = uow

    async def execute(self, data: CreateClientInput) -> Client:
        name = data.name.strip()
        if await self._clients.find_by_name(data.workspace_id, name) is not None:
            raise ClientNameTaken

        now = self._clock.now()
        client = Client(
            id=uuid4(),
            workspace_id=data.workspace_id,
            name=name,
            created_at=now,
            updated_at=now,
        )
        stored = await self._clients.add(client)
        await self._uow.commit()
        return stored
