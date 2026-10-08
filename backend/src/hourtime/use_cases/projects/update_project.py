from typing import Any

from hourtime.domain.entities import Project
from hourtime.domain.errors import ProjectNameTaken, ValidationError
from hourtime.interfaces.repositories import ClientRepository, ProjectRepository
from hourtime.interfaces.services import Clock, UnitOfWork
from hourtime.use_cases.access import get_workspace_project
from hourtime.use_cases.dto import UpdateProjectInput
from hourtime.use_cases.projects.rules import resolve_client


class UpdateProject:
    """Renames, recolours, archives and (re)assigns the client - everything
    PATCH /projects/{id} can do. `client_id: null` detaches the client."""

    def __init__(
        self,
        projects: ProjectRepository,
        clients: ClientRepository,
        clock: Clock,
        uow: UnitOfWork,
    ) -> None:
        self._projects = projects
        self._clients = clients
        self._clock = clock
        self._uow = uow

    async def execute(self, data: UpdateProjectInput) -> Project:
        project = await get_workspace_project(self._projects, data.workspace_id, data.project_id)
        now = self._clock.now()
        changes: dict[str, Any] = {}

        if data.provided("name"):
            if data.name is None:
                raise ValidationError("The name is required")
            name = data.name.strip()
            clash = await self._projects.find_by_name(data.workspace_id, name)
            if clash is not None and clash.id != project.id:
                raise ProjectNameTaken
            changes["name"] = name

        if data.provided("color"):
            if data.color is None:
                raise ValidationError("The color is required")
            changes["color"] = data.color

        if data.provided("archived"):
            if data.archived is None:
                raise ValidationError("The archived flag is required")
            changes["archived_at"] = now if data.archived else None

        if data.provided("client_id"):
            changes["client_id"] = await resolve_client(
                self._clients, data.workspace_id, data.client_id
            )

        if not changes:
            return project

        changes["updated_at"] = now
        updated = await self._projects.update(project.evolve(**changes))
        await self._uow.commit()
        return updated
