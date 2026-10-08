from uuid import uuid4

import pytest

from hourtime.domain.errors import NotFound, ProjectNameTaken, ValidationError
from hourtime.use_cases.dto import CreateProjectInput, UpdateProjectInput
from hourtime.use_cases.projects import CreateProject, DeleteProject, ListProjects, UpdateProject
from tests.factories import make_client, make_project, make_user
from tests.fakes import (
    FakeClock,
    FakeUnitOfWork,
    InMemoryClientRepository,
    InMemoryProjectRepository,
)


class ProjectWorld:
    def __init__(self) -> None:
        self.clock = FakeClock()
        self.projects = InMemoryProjectRepository()
        self.clients = InMemoryClientRepository()
        self.uow = FakeUnitOfWork()
        self.user = make_user()
        self.other_user = make_user(email="someone@example.com")

        self.create = CreateProject(self.projects, self.clients, self.clock, self.uow)
        self.listing = ListProjects(self.projects)
        self.update = UpdateProject(self.projects, self.clients, self.clock, self.uow)
        self.delete = DeleteProject(self.projects, self.uow)


@pytest.fixture
def world() -> ProjectWorld:
    return ProjectWorld()


class TestCreate:
    async def test_uses_the_default_colour_when_none_is_given(self, world: ProjectWorld) -> None:
        project = await world.create.execute(
            CreateProjectInput(workspace_id=world.user.default_workspace_id, name="Website")
        )
        assert project.color == "#4285f4"

    async def test_normalises_a_custom_colour(self, world: ProjectWorld) -> None:
        project = await world.create.execute(
            CreateProjectInput(
                workspace_id=world.user.default_workspace_id, name="Website", color="#A1B2C3"
            )
        )
        assert project.color == "#a1b2c3"

    async def test_rejects_a_duplicate_name(self, world: ProjectWorld) -> None:
        await world.create.execute(
            CreateProjectInput(workspace_id=world.user.default_workspace_id, name="Website")
        )
        with pytest.raises(ProjectNameTaken):
            await world.create.execute(
                CreateProjectInput(workspace_id=world.user.default_workspace_id, name="  website ")
            )

    async def test_the_same_name_is_free_for_another_user(self, world: ProjectWorld) -> None:
        await world.create.execute(
            CreateProjectInput(workspace_id=world.user.default_workspace_id, name="Website")
        )
        theirs = await world.create.execute(
            CreateProjectInput(workspace_id=world.other_user.default_workspace_id, name="Website")
        )
        assert theirs.name == "Website"


class TestUpdate:
    async def test_renames_and_recolours(self, world: ProjectWorld) -> None:
        project = await world.projects.add(make_project(world.user.default_workspace_id))
        updated = await world.update.execute(
            UpdateProjectInput(
                workspace_id=world.user.default_workspace_id,
                project_id=project.id,
                name="Landing",
                color="#ff0000",
            )
        )
        assert (updated.name, updated.color) == ("Landing", "#ff0000")

    async def test_archiving_frees_the_name(self, world: ProjectWorld) -> None:
        project = await world.projects.add(
            make_project(world.user.default_workspace_id, name="Website")
        )
        await world.update.execute(
            UpdateProjectInput(
                workspace_id=world.user.default_workspace_id, project_id=project.id, archived=True
            )
        )
        reused = await world.create.execute(
            CreateProjectInput(workspace_id=world.user.default_workspace_id, name="Website")
        )
        assert reused.id != project.id

    async def test_unarchiving_clears_the_timestamp(self, world: ProjectWorld) -> None:
        project = await world.projects.add(
            make_project(world.user.default_workspace_id, archived_at=world.clock.now())
        )
        updated = await world.update.execute(
            UpdateProjectInput(
                workspace_id=world.user.default_workspace_id, project_id=project.id, archived=False
            )
        )
        assert not updated.is_archived

    async def test_rejects_a_name_another_project_already_holds(self, world: ProjectWorld) -> None:
        await world.projects.add(make_project(world.user.default_workspace_id, name="Website"))
        other = await world.projects.add(
            make_project(world.user.default_workspace_id, name="Landing")
        )
        with pytest.raises(ProjectNameTaken):
            await world.update.execute(
                UpdateProjectInput(
                    workspace_id=world.user.default_workspace_id,
                    project_id=other.id,
                    name="Website",
                )
            )

    async def test_keeping_its_own_name_is_not_a_clash(self, world: ProjectWorld) -> None:
        project = await world.projects.add(
            make_project(world.user.default_workspace_id, name="Website")
        )
        updated = await world.update.execute(
            UpdateProjectInput(
                workspace_id=world.user.default_workspace_id,
                project_id=project.id,
                name="Website",
                color="#000000",
            )
        )
        assert updated.color == "#000000"

    async def test_rejects_someone_elses_project(self, world: ProjectWorld) -> None:
        theirs = await world.projects.add(make_project(world.other_user.default_workspace_id))
        with pytest.raises(NotFound):
            await world.update.execute(
                UpdateProjectInput(
                    workspace_id=world.user.default_workspace_id, project_id=theirs.id, name="Mine"
                )
            )

    async def test_rejects_a_bad_colour(self, world: ProjectWorld) -> None:
        project = await world.projects.add(make_project(world.user.default_workspace_id))
        with pytest.raises(ValidationError):
            await world.update.execute(
                UpdateProjectInput(
                    workspace_id=world.user.default_workspace_id,
                    project_id=project.id,
                    color="chartreuse",
                )
            )


class TestListing:
    async def test_hides_archived_projects_by_default(self, world: ProjectWorld) -> None:
        await world.projects.add(make_project(world.user.default_workspace_id, name="Live"))
        await world.projects.add(
            make_project(world.user.default_workspace_id, name="Old", archived_at=world.clock.now())
        )

        assert [p.name for p in await world.listing.execute(world.user.default_workspace_id)] == [
            "Live"
        ]
        everything = await world.listing.execute(
            world.user.default_workspace_id, include_archived=True
        )
        assert [p.name for p in everything] == ["Live", "Old"]

    async def test_never_shows_another_users_projects(self, world: ProjectWorld) -> None:
        await world.projects.add(make_project(world.other_user.default_workspace_id))
        assert await world.listing.execute(world.user.default_workspace_id) == []


class TestDelete:
    async def test_removes_own_project(self, world: ProjectWorld) -> None:
        project = await world.projects.add(make_project(world.user.default_workspace_id))
        await world.delete.execute(world.user.default_workspace_id, project.id)
        assert await world.projects.get_by_id(project.id) is None

    async def test_rejects_someone_elses_project(self, world: ProjectWorld) -> None:
        theirs = await world.projects.add(make_project(world.other_user.default_workspace_id))
        with pytest.raises(NotFound):
            await world.delete.execute(world.user.default_workspace_id, theirs.id)

    async def test_reports_a_missing_project_as_not_found(self, world: ProjectWorld) -> None:
        with pytest.raises(NotFound):
            await world.delete.execute(world.user.default_workspace_id, uuid4())


class TestClientAssignment:
    async def test_creates_a_project_for_a_client(self, world: ProjectWorld) -> None:
        client = await world.clients.add(make_client(world.user.default_workspace_id))
        project = await world.create.execute(
            CreateProjectInput(
                workspace_id=world.user.default_workspace_id, name="Website", client_id=client.id
            )
        )
        assert project.client_id == client.id

    async def test_rejects_a_client_from_another_workspace(self, world: ProjectWorld) -> None:
        theirs = await world.clients.add(make_client(world.other_user.default_workspace_id))
        with pytest.raises(NotFound):
            await world.create.execute(
                CreateProjectInput(
                    workspace_id=world.user.default_workspace_id,
                    name="Website",
                    client_id=theirs.id,
                )
            )
        project = await world.projects.add(make_project(world.user.default_workspace_id))
        with pytest.raises(NotFound):
            await world.update.execute(
                UpdateProjectInput(
                    workspace_id=world.user.default_workspace_id,
                    project_id=project.id,
                    client_id=theirs.id,
                )
            )

    async def test_rejects_an_archived_client(self, world: ProjectWorld) -> None:
        archived = await world.clients.add(
            make_client(world.user.default_workspace_id, archived_at=world.clock.now())
        )
        with pytest.raises(ValidationError):
            await world.create.execute(
                CreateProjectInput(
                    workspace_id=world.user.default_workspace_id,
                    name="Website",
                    client_id=archived.id,
                )
            )
        project = await world.projects.add(make_project(world.user.default_workspace_id))
        with pytest.raises(ValidationError):
            await world.update.execute(
                UpdateProjectInput(
                    workspace_id=world.user.default_workspace_id,
                    project_id=project.id,
                    client_id=archived.id,
                )
            )

    async def test_patch_assigns_keeps_and_detaches_the_client(self, world: ProjectWorld) -> None:
        workspace_id = world.user.default_workspace_id
        client = await world.clients.add(make_client(workspace_id))
        project = await world.projects.add(make_project(workspace_id))

        assigned = await world.update.execute(
            UpdateProjectInput(
                workspace_id=workspace_id, project_id=project.id, client_id=client.id
            )
        )
        assert assigned.client_id == client.id

        renamed = await world.update.execute(
            UpdateProjectInput(workspace_id=workspace_id, project_id=project.id, name="Landing")
        )
        assert renamed.client_id == client.id

        detached = await world.update.execute(
            UpdateProjectInput(workspace_id=workspace_id, project_id=project.id, client_id=None)
        )
        assert detached.client_id is None
