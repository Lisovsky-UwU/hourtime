from uuid import uuid4

import pytest

from hourtime.domain.errors import ClientNameTaken, NotFound, ValidationError
from hourtime.use_cases.clients import CreateClient, DeleteClient, ListClients, UpdateClient
from hourtime.use_cases.dto import CreateClientInput, UpdateClientInput
from tests.factories import make_client, make_user
from tests.fakes import FakeClock, FakeUnitOfWork, InMemoryClientRepository


class ClientWorld:
    def __init__(self) -> None:
        self.clock = FakeClock()
        self.clients = InMemoryClientRepository()
        self.uow = FakeUnitOfWork()
        self.workspace_id = make_user().default_workspace_id
        self.other_workspace_id = make_user(email="someone@example.com").default_workspace_id

        self.create = CreateClient(self.clients, self.clock, self.uow)
        self.listing = ListClients(self.clients)
        self.update = UpdateClient(self.clients, self.clock, self.uow)
        self.delete = DeleteClient(self.clients, self.uow)


@pytest.fixture
def world() -> ClientWorld:
    return ClientWorld()


class TestCreate:
    async def test_strips_the_name(self, world: ClientWorld) -> None:
        client = await world.create.execute(
            CreateClientInput(workspace_id=world.workspace_id, name="  Acme  ")
        )
        assert client.name == "Acme"
        assert not client.is_archived
        assert world.uow.commits == 1

    async def test_rejects_a_blank_name(self, world: ClientWorld) -> None:
        with pytest.raises(ValidationError):
            await world.create.execute(
                CreateClientInput(workspace_id=world.workspace_id, name="  ")
            )

    async def test_rejects_a_duplicate_name_ignoring_case(self, world: ClientWorld) -> None:
        await world.create.execute(CreateClientInput(workspace_id=world.workspace_id, name="Acme"))
        with pytest.raises(ClientNameTaken):
            await world.create.execute(
                CreateClientInput(workspace_id=world.workspace_id, name=" ACME ")
            )

    async def test_an_archived_client_does_not_hold_its_name(self, world: ClientWorld) -> None:
        old = await world.clients.add(
            make_client(world.workspace_id, name="Acme", archived_at=world.clock.now())
        )
        fresh = await world.create.execute(
            CreateClientInput(workspace_id=world.workspace_id, name="Acme")
        )
        assert fresh.id != old.id

    async def test_the_same_name_is_free_in_another_workspace(self, world: ClientWorld) -> None:
        await world.create.execute(CreateClientInput(workspace_id=world.workspace_id, name="Acme"))
        theirs = await world.create.execute(
            CreateClientInput(workspace_id=world.other_workspace_id, name="Acme")
        )
        assert theirs.workspace_id == world.other_workspace_id


class TestUpdate:
    async def test_renames(self, world: ClientWorld) -> None:
        client = await world.clients.add(make_client(world.workspace_id))
        updated = await world.update.execute(
            UpdateClientInput(workspace_id=world.workspace_id, client_id=client.id, name="Globex")
        )
        assert updated.name == "Globex"

    async def test_archives_and_restores(self, world: ClientWorld) -> None:
        client = await world.clients.add(make_client(world.workspace_id))
        archived = await world.update.execute(
            UpdateClientInput(workspace_id=world.workspace_id, client_id=client.id, archived=True)
        )
        assert archived.archived_at == world.clock.now()

        restored = await world.update.execute(
            UpdateClientInput(workspace_id=world.workspace_id, client_id=client.id, archived=False)
        )
        assert not restored.is_archived

    async def test_rejects_a_name_another_client_holds(self, world: ClientWorld) -> None:
        await world.clients.add(make_client(world.workspace_id, name="Acme"))
        other = await world.clients.add(make_client(world.workspace_id, name="Globex"))
        with pytest.raises(ClientNameTaken):
            await world.update.execute(
                UpdateClientInput(workspace_id=world.workspace_id, client_id=other.id, name="acme")
            )

    async def test_keeping_its_own_name_is_not_a_clash(self, world: ClientWorld) -> None:
        client = await world.clients.add(make_client(world.workspace_id, name="Acme"))
        updated = await world.update.execute(
            UpdateClientInput(workspace_id=world.workspace_id, client_id=client.id, name="ACME")
        )
        assert updated.name == "ACME"

    async def test_rejects_a_null_name(self, world: ClientWorld) -> None:
        client = await world.clients.add(make_client(world.workspace_id))
        with pytest.raises(ValidationError):
            await world.update.execute(
                UpdateClientInput(workspace_id=world.workspace_id, client_id=client.id, name=None)
            )

    async def test_rejects_a_client_from_another_workspace(self, world: ClientWorld) -> None:
        theirs = await world.clients.add(make_client(world.other_workspace_id))
        with pytest.raises(NotFound):
            await world.update.execute(
                UpdateClientInput(workspace_id=world.workspace_id, client_id=theirs.id, name="Mine")
            )


class TestListing:
    async def test_sorts_by_name_and_hides_archived(self, world: ClientWorld) -> None:
        await world.clients.add(make_client(world.workspace_id, name="globex"))
        await world.clients.add(make_client(world.workspace_id, name="Acme"))
        await world.clients.add(
            make_client(world.workspace_id, name="Old", archived_at=world.clock.now())
        )
        await world.clients.add(make_client(world.other_workspace_id, name="Theirs"))

        live = await world.listing.execute(world.workspace_id)
        assert [client.name for client in live] == ["Acme", "globex"]

        everything = await world.listing.execute(world.workspace_id, include_archived=True)
        assert [client.name for client in everything] == ["Acme", "globex", "Old"]


class TestDelete:
    async def test_removes_the_client(self, world: ClientWorld) -> None:
        client = await world.clients.add(make_client(world.workspace_id))
        await world.delete.execute(world.workspace_id, client.id)
        assert await world.clients.get_by_id(client.id) is None

    async def test_rejects_a_client_from_another_workspace(self, world: ClientWorld) -> None:
        theirs = await world.clients.add(make_client(world.other_workspace_id))
        with pytest.raises(NotFound):
            await world.delete.execute(world.workspace_id, theirs.id)
        assert await world.clients.get_by_id(theirs.id) is not None

    async def test_reports_a_missing_client_as_not_found(self, world: ClientWorld) -> None:
        with pytest.raises(NotFound):
            await world.delete.execute(world.workspace_id, uuid4())
