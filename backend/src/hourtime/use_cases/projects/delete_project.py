from uuid import UUID

from hourtime.interfaces.repositories import ProjectRepository
from hourtime.interfaces.services import UnitOfWork
from hourtime.use_cases.access import get_owned_project


class DeleteProject:
    """Removes a project; its time entries survive with no project attached."""

    def __init__(self, projects: ProjectRepository, uow: UnitOfWork) -> None:
        self._projects = projects
        self._uow = uow

    async def execute(self, user_id: UUID, project_id: UUID) -> None:
        project = await get_owned_project(self._projects, user_id, project_id)
        await self._projects.delete(project.id)
        await self._uow.commit()
