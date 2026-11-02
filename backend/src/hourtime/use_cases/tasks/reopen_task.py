from uuid import UUID

from hourtime.domain.entities import MemberRole, Task
from hourtime.domain.errors import TaskNameTaken, ValidationError
from hourtime.interfaces.repositories import ProjectRepository, TaskRepository
from hourtime.interfaces.services import Clock, UnitOfWork
from hourtime.use_cases.access import get_workspace_task, require_admin


class ReopenTask:
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

    async def execute(self, workspace_id: UUID, task_id: UUID, *, role: MemberRole) -> Task:
        require_admin(role)
        task, project = await get_workspace_task(self._tasks, self._projects, workspace_id, task_id)
        if project.is_archived:
            raise ValidationError("Tasks of an archived project are read-only")
        if not task.is_completed:
            return task
        clash = await self._tasks.find_by_name(project.id, task.name)
        if clash is not None and clash.id != task.id:
            raise TaskNameTaken
        reopened = await self._tasks.update(
            task.evolve(completed_at=None, updated_at=self._clock.now())
        )
        await self._uow.commit()
        return reopened
