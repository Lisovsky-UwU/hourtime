from uuid import uuid4

from hourtime.domain.entities import Task
from hourtime.domain.errors import TaskNameTaken, ValidationError
from hourtime.interfaces.repositories import ProjectRepository, TaskRepository
from hourtime.interfaces.services import Clock, UnitOfWork
from hourtime.use_cases.access import get_workspace_project
from hourtime.use_cases.dto import CreateTaskInput


class CreateTask:
    def __init__(
        self,
        tasks: TaskRepository,
        projects: ProjectRepository,
        clock: Clock,
        uow: UnitOfWork,
    ) -> None:
        self._tasks = tasks
        self._projects = projects
        self._clock = clock
        self._uow = uow

    async def execute(self, data: CreateTaskInput) -> Task:
        project = await get_workspace_project(self._projects, data.workspace_id, data.project_id)
        if project.is_archived:
            raise ValidationError("Tasks of an archived project are read-only")
        name = data.name.strip()
        if await self._tasks.find_by_name(project.id, name) is not None:
            raise TaskNameTaken

        now = self._clock.now()
        task = Task(
            id=uuid4(),
            project_id=project.id,
            name=name,
            estimated_seconds=data.estimated_seconds,
            created_at=now,
            updated_at=now,
        )
        stored = await self._tasks.add(task)
        await self._uow.commit()
        return stored
