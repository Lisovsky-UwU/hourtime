from uuid import UUID

from hourtime.domain.entities import MemberRole
from hourtime.domain.errors import ValidationError
from hourtime.interfaces.repositories import ProjectRepository, TaskRepository
from hourtime.interfaces.services import UnitOfWork
from hourtime.use_cases.access import get_workspace_task, require_admin


class DeleteTask:
    def __init__(
        self, tasks: TaskRepository, projects: ProjectRepository, uow: UnitOfWork
    ) -> None:
        self._tasks = tasks
        self._projects = projects
        self._uow = uow

    async def execute(self, workspace_id: UUID, task_id: UUID, *, role: MemberRole) -> None:
        require_admin(role)
        task, project = await get_workspace_task(self._tasks, self._projects, workspace_id, task_id)
        if project.is_archived:
            raise ValidationError("Tasks of an archived project are read-only")
        await self._tasks.delete(task.id)
        await self._uow.commit()
