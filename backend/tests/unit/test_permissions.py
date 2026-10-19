"""Roles: members create projects, clients and tags; changing or removing them is for admins."""

from collections.abc import Awaitable, Callable

import pytest

from hourtime.domain.entities import MemberRole
from hourtime.domain.errors import PermissionDenied
from hourtime.use_cases.clients import CreateClient, DeleteClient, UpdateClient
from hourtime.use_cases.dto import (
    CreateClientInput,
    CreateProjectInput,
    CreateTagInput,
    UpdateClientInput,
    UpdateProjectInput,
    UpdateTagInput,
    UpdateWorkspaceInput,
)
from hourtime.use_cases.projects import CreateProject, DeleteProject, UpdateProject
from hourtime.use_cases.tags import CreateTag, DeleteTag, UpdateTag
from hourtime.use_cases.workspaces import UpdateWorkspace
from tests.factories import make_client, make_project, make_tag, make_user, make_workspace
from tests.fakes import (
    FakeClock,
    FakeUnitOfWork,
    InMemoryClientRepository,
    InMemoryProjectRepository,
    InMemoryTagRepository,
    InMemoryWorkspaceRepository,
)


class World:
    def __init__(self) -> None:
        self.clock = FakeClock()
        self.uow = FakeUnitOfWork()
        owner = make_user()
        self.workspace_id = owner.default_workspace_id
        self.workspaces = InMemoryWorkspaceRepository([make_workspace(owner)])
        self.clients = InMemoryClientRepository()
        self.projects = InMemoryProjectRepository()
        self.tags = InMemoryTagRepository()

    async def update_client(self, role: MemberRole) -> None:
        client = await self.clients.add(make_client(self.workspace_id))
        await UpdateClient(self.clients, self.clock, self.uow).execute(
            UpdateClientInput(
                workspace_id=self.workspace_id, role=role, client_id=client.id, archived=True
            )
        )

    async def delete_client(self, role: MemberRole) -> None:
        client = await self.clients.add(make_client(self.workspace_id))
        await DeleteClient(self.clients, self.uow).execute(self.workspace_id, client.id, role=role)

    async def update_project(self, role: MemberRole) -> None:
        project = await self.projects.add(make_project(self.workspace_id))
        await UpdateProject(self.projects, self.clients, self.clock, self.uow).execute(
            UpdateProjectInput(
                workspace_id=self.workspace_id, role=role, project_id=project.id, name="Renamed"
            )
        )

    async def delete_project(self, role: MemberRole) -> None:
        project = await self.projects.add(make_project(self.workspace_id))
        await DeleteProject(self.projects, self.uow).execute(
            self.workspace_id, project.id, role=role
        )

    async def update_tag(self, role: MemberRole) -> None:
        tag = await self.tags.add(make_tag(self.workspace_id))
        await UpdateTag(self.tags, self.clock, self.uow).execute(
            UpdateTagInput(workspace_id=self.workspace_id, role=role, tag_id=tag.id, name="new")
        )

    async def delete_tag(self, role: MemberRole) -> None:
        tag = await self.tags.add(make_tag(self.workspace_id))
        await DeleteTag(self.tags, self.uow).execute(self.workspace_id, tag.id, role=role)

    async def update_workspace(self, role: MemberRole) -> None:
        await UpdateWorkspace(self.workspaces, self.clock, self.uow).execute(
            UpdateWorkspaceInput(workspace_id=self.workspace_id, role=role, currency="EUR")
        )


ADMIN_ONLY = [
    World.update_client,
    World.delete_client,
    World.update_project,
    World.delete_project,
    World.update_tag,
    World.delete_tag,
    World.update_workspace,
]

Operation = Callable[[World, MemberRole], Awaitable[None]]


@pytest.mark.parametrize("operation", ADMIN_ONLY, ids=lambda op: op.__name__)
async def test_admin_may(operation: Operation) -> None:
    world = World()
    await operation(world, "admin")
    assert world.uow.commits == 1


@pytest.mark.parametrize("operation", ADMIN_ONLY, ids=lambda op: op.__name__)
async def test_member_may_not(operation: Operation) -> None:
    world = World()
    with pytest.raises(PermissionDenied):
        await operation(world, "member")
    assert world.uow.commits == 0


async def test_member_creates_projects_clients_and_tags() -> None:
    world = World()
    await CreateClient(world.clients, world.clock, world.uow).execute(
        CreateClientInput(workspace_id=world.workspace_id, name="Acme")
    )
    await CreateProject(world.projects, world.clients, world.clock, world.uow).execute(
        CreateProjectInput(workspace_id=world.workspace_id, name="Website")
    )
    await CreateTag(world.tags, world.clock, world.uow).execute(
        CreateTagInput(workspace_id=world.workspace_id, name="urgent")
    )
    assert world.uow.commits == 3
