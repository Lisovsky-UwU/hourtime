from uuid import UUID

from hourtime.domain.entities import Task
from hourtime.interfaces.repositories import ProjectRepository, TaskRepository
from hourtime.use_cases.access import get_workspace_project


class ListTasks:
    def __init__(self, tasks: TaskRepository, projects: ProjectRepository) -> None:
        self._tasks = tasks
        self._projects = projects

    async def execute(
        self,
        workspace_id: UUID,
        *,
        project_id: UUID | None = None,
        include_completed: bool = False,
    ) -> list[Task]:
        if project_id is not None:
            await get_workspace_project(self._projects, workspace_id, project_id)
        return await self._tasks.list_for_workspace(
            workspace_id, project_id=project_id, include_completed=include_completed
        )
