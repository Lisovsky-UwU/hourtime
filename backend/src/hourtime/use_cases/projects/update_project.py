from typing import Any

from hourtime.domain.entities import Project
from hourtime.domain.errors import ProjectNameTaken, ValidationError
from hourtime.interfaces.repositories import ClientRepository, ProjectRepository
from hourtime.interfaces.services import Clock, UnitOfWork
from hourtime.use_cases.access import get_workspace_project
from hourtime.use_cases.dto import UpdateProjectInput
from hourtime.use_cases.projects.rules import resolve_client


class UpdateProject:
    """Renames, recolours, archives, (re)assigns the client and sets billing -
    everything PATCH /projects/{id} can do. `client_id: null` detaches the
    client, `hourly_rate: null` falls back to the workspace rate."""

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

        if data.provided("billable"):
            if data.billable is None:
                raise ValidationError("The billable flag is required")
            changes["billable"] = data.billable

        if data.provided("hourly_rate"):
            changes["hourly_rate"] = data.hourly_rate

        if not changes:
            return project

        changes["updated_at"] = now
        updated = await self._projects.update(project.evolve(**changes))
        await self._uow.commit()
        return updated
