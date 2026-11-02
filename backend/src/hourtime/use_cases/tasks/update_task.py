from typing import Any

from hourtime.domain.entities import Task
from hourtime.domain.errors import TaskNameTaken, ValidationError
from hourtime.interfaces.repositories import ProjectRepository, TaskRepository
from hourtime.interfaces.services import Clock, UnitOfWork
from hourtime.use_cases.access import get_workspace_task, require_admin
from hourtime.use_cases.dto import UpdateTaskInput


class UpdateTask:
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

    async def execute(self, data: UpdateTaskInput) -> Task:
        require_admin(data.role)
        task, project = await get_workspace_task(
            self._tasks, self._projects, data.workspace_id, data.task_id
        )
        if project.is_archived:
            raise ValidationError("Tasks of an archived project are read-only")
        changes: dict[str, Any] = {}

        if data.provided("completed") and data.completed is None:
            raise ValidationError("The completed flag is required")

        if data.provided("name"):
            if data.name is None:
                raise ValidationError("The name is required")
            name = data.name.strip()
            clash = await self._tasks.find_by_name(project.id, name)
            if clash is not None and clash.id != task.id:
                raise TaskNameTaken
            changes["name"] = name

        if data.provided("estimated_seconds"):
            changes["estimated_seconds"] = data.estimated_seconds

        if not changes:
            return task

        changes["updated_at"] = self._clock.now()
        updated = await self._tasks.update(task.evolve(**changes))
        await self._uow.commit()
        return updated
