from uuid import UUID

from hourtime.domain.entities import MemberRole, Task
from hourtime.domain.errors import ValidationError
from hourtime.interfaces.repositories import ProjectRepository, TaskRepository
from hourtime.interfaces.services import Clock, UnitOfWork
from hourtime.use_cases.access import get_workspace_task, require_admin


class CompleteTask:
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
        if task.is_completed:
            return task
        now = self._clock.now()
        completed = await self._tasks.update(task.evolve(completed_at=now, updated_at=now))
        await self._uow.commit()
        return completed
