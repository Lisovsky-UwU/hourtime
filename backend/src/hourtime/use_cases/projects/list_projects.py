from uuid import UUID

from hourtime.domain.entities import Project
from hourtime.interfaces.repositories import ProjectRepository


class ListProjects:
    def __init__(self, projects: ProjectRepository) -> None:
        self._projects = projects

    async def execute(self, user_id: UUID, *, include_archived: bool = False) -> list[Project]:
        return await self._projects.list_for_user(user_id, include_archived=include_archived)
