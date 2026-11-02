from datetime import timedelta
from uuid import uuid4

import pytest

from hourtime.domain.errors import (
    NotFound,
    PermissionDenied,
    TaskNameTaken,
    ValidationError,
)
from hourtime.use_cases.dto import CreateTaskInput, UpdateTaskInput
from hourtime.use_cases.tasks import (
    CompleteTask,
    CreateTask,
    DeleteTask,
    ListTasks,
    ReopenTask,
    UpdateTask,
)
from tests.factories import make_project, make_task, make_user
from tests.fakes import (
    FakeClock,
    FakeUnitOfWork,
    InMemoryProjectRepository,
    InMemoryTaskRepository,
)


class TaskWorld:
    def __init__(self) -> None:
        self.clock = FakeClock()
        self.uow = FakeUnitOfWork()
        self.user = make_user()
        self.other_user = make_user(email="other@example.com")
        self.workspace_id = self.user.default_workspace_id
        self.other_workspace_id = self.other_user.default_workspace_id
        self.project = make_project(self.workspace_id)
        self.other_project = make_project(self.other_workspace_id)
        self.projects = InMemoryProjectRepository([self.project, self.other_project])
        self.tasks = InMemoryTaskRepository(projects=self.projects)
        self.create = CreateTask(self.tasks, self.projects, self.clock, self.uow)
        self.listing = ListTasks(self.tasks, self.projects)
        self.update = UpdateTask(self.tasks, self.projects, self.clock, self.uow)
        self.complete = CompleteTask(self.tasks, self.projects, self.clock, self.uow)
        self.reopen = ReopenTask(self.tasks, self.projects, self.clock, self.uow)
        self.delete = DeleteTask(self.tasks, self.projects, self.uow)

    def create_input(self, name: str = "Design", **overrides: object) -> CreateTaskInput:
        values: dict[str, object] = {
            "workspace_id": self.workspace_id,
            "project_id": self.project.id,
            "name": name,
        }
        values.update(overrides)
        return CreateTaskInput.model_validate(values)

    def update_input(self, task_id: object, **changes: object) -> UpdateTaskInput:
        return UpdateTaskInput.model_validate(
            {
                "workspace_id": self.workspace_id,
                "role": "admin",
                "task_id": task_id,
                **changes,
            }
        )


@pytest.fixture
def world() -> TaskWorld:
    return TaskWorld()


class TestTaskEntity:
    def test_trims_name_and_reports_completion(self, world: TaskWorld) -> None:
        task = make_task(world.project.id, name="  Design  ")
        assert task.name == "Design"
        assert not task.is_completed
        assert task.evolve(completed_at=world.clock.now()).is_completed

    @pytest.mark.parametrize(
        "overrides", [{"name": "  "}, {"estimated_seconds": 0}, {"estimated_seconds": -1}]
    )
    def test_rejects_invalid_fields(self, world: TaskWorld, overrides: dict[str, object]) -> None:
        with pytest.raises(ValidationError):
            make_task(world.project.id).model_validate(
                {**make_task(world.project.id).model_dump(), **overrides}
            )


class TestCreateTask:
    async def test_creates_with_estimate(self, world: TaskWorld) -> None:
        task = await world.create.execute(
            world.create_input(name="  Design ", estimated_seconds=3600)
        )
        assert (task.name, task.estimated_seconds) == ("Design", 3600)
        assert task.completed_at is None
        assert world.uow.commits == 1

    async def test_rejects_duplicate_active_name_only_in_same_project(
        self, world: TaskWorld
    ) -> None:
        await world.create.execute(world.create_input())
        with pytest.raises(TaskNameTaken):
            await world.create.execute(world.create_input(name=" design "))
        other = make_project(world.workspace_id, name="Other")
        await world.projects.add(other)
        assert await world.create.execute(world.create_input(project_id=other.id))

    async def test_completed_task_frees_name(self, world: TaskWorld) -> None:
        task = await world.create.execute(world.create_input())
        await world.complete.execute(world.workspace_id, task.id, role="admin")
        reused = await world.create.execute(world.create_input())
        assert reused.id != task.id

    async def test_rejects_other_workspace_and_archived_project(self, world: TaskWorld) -> None:
        with pytest.raises(NotFound):
            await world.create.execute(world.create_input(project_id=world.other_project.id))
        archived = make_project(world.workspace_id, name="Archived", archived_at=world.clock.now())
        await world.projects.add(archived)
        with pytest.raises(ValidationError):
            await world.create.execute(world.create_input(project_id=archived.id))


class TestUpdateTask:
    async def test_updates_name_and_estimate(self, world: TaskWorld) -> None:
        task = await world.create.execute(world.create_input(estimated_seconds=60))
        world.clock.advance(timedelta(minutes=1))
        updated = await world.update.execute(
            world.update_input(task.id, name="Research", estimated_seconds=None)
        )
        assert (updated.name, updated.estimated_seconds) == ("Research", None)
        assert updated.updated_at == world.clock.now()

    async def test_member_cannot_update_or_delete(self, world: TaskWorld) -> None:
        task = await world.create.execute(world.create_input())
        with pytest.raises(PermissionDenied):
            await world.update.execute(world.update_input(task.id, role="member", name="New"))
        with pytest.raises(PermissionDenied):
            await world.delete.execute(world.workspace_id, task.id, role="member")

    async def test_rejects_duplicate_name(self, world: TaskWorld) -> None:
        await world.create.execute(world.create_input())
        other = await world.create.execute(world.create_input(name="Research"))
        with pytest.raises(TaskNameTaken):
            await world.update.execute(world.update_input(other.id, name="DESIGN"))

    async def test_rejects_task_from_other_workspace(self, world: TaskWorld) -> None:
        task = await world.tasks.add(make_task(world.other_project.id))
        with pytest.raises(NotFound):
            await world.update.execute(world.update_input(task.id, name="Stolen"))
        with pytest.raises(NotFound):
            await world.delete.execute(world.workspace_id, task.id, role="admin")


class TestListTasks:
    async def test_filters_completion_project_and_workspace(self, world: TaskWorld) -> None:
        active = await world.create.execute(world.create_input(name="Active"))
        completed = await world.create.execute(world.create_input(name="Completed"))
        await world.complete.execute(world.workspace_id, completed.id, role="admin")
        second_project = make_project(world.workspace_id, name="Second")
        await world.projects.add(second_project)
        other = await world.create.execute(
            world.create_input(name="Other", project_id=second_project.id)
        )
        await world.tasks.add(make_task(world.other_project.id, name="Foreign"))

        listed = await world.listing.execute(world.workspace_id)
        assert {task.id for task in listed} == {active.id, other.id}
        everything = await world.listing.execute(world.workspace_id, include_completed=True)
        assert {task.id for task in everything} == {active.id, completed.id, other.id}
        filtered = await world.listing.execute(
            world.workspace_id, project_id=second_project.id, include_completed=True
        )
        assert [task.name for task in filtered] == ["Other"]

    async def test_other_workspaces_project_filter_is_not_found(self, world: TaskWorld) -> None:
        with pytest.raises(NotFound):
            await world.listing.execute(world.workspace_id, project_id=world.other_project.id)


class TestCompletion:
    async def test_complete_and_reopen_update_timestamps(self, world: TaskWorld) -> None:
        task = await world.create.execute(world.create_input())
        completed_at = world.clock.advance(timedelta(minutes=1))
        completed = await world.complete.execute(world.workspace_id, task.id, role="admin")
        assert completed.completed_at == completed_at
        assert completed.updated_at == completed_at
        reopened = await world.reopen.execute(world.workspace_id, task.id, role="admin")
        assert reopened.completed_at is None

    async def test_reopen_rejects_active_name_clash(self, world: TaskWorld) -> None:
        task = await world.create.execute(world.create_input())
        await world.complete.execute(world.workspace_id, task.id, role="admin")
        await world.create.execute(world.create_input(name="design"))
        with pytest.raises(TaskNameTaken):
            await world.reopen.execute(world.workspace_id, task.id, role="admin")

    async def test_archived_project_is_read_only_for_all_mutations(self, world: TaskWorld) -> None:
        task = await world.create.execute(world.create_input())
        await world.projects.update(world.project.evolve(archived_at=world.clock.now()))
        for operation in (
            world.update.execute(world.update_input(task.id, name="New")),
            world.complete.execute(world.workspace_id, task.id, role="admin"),
            world.reopen.execute(world.workspace_id, task.id, role="admin"),
            world.delete.execute(world.workspace_id, task.id, role="admin"),
        ):
            with pytest.raises(ValidationError):
                await operation

    async def test_missing_task_is_not_found(self, world: TaskWorld) -> None:
        with pytest.raises(NotFound):
            await world.complete.execute(world.workspace_id, uuid4(), role="admin")
