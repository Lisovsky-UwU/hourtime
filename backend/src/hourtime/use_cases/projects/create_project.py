from uuid import uuid4

from hourtime.domain.entities import DEFAULT_COLOR, Project
from hourtime.domain.errors import ProjectNameTaken
from hourtime.interfaces.repositories import ClientRepository, ProjectRepository
from hourtime.interfaces.services import Clock, UnitOfWork
from hourtime.use_cases.dto import CreateProjectInput
from hourtime.use_cases.projects.rules import resolve_client


class CreateProject:
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

    async def execute(self, data: CreateProjectInput) -> Project:
        name = data.name.strip()
        if await self._projects.find_by_name(data.workspace_id, name) is not None:
            raise ProjectNameTaken
        client_id = await resolve_client(self._clients, data.workspace_id, data.client_id)

        now = self._clock.now()
        project = Project(
            id=uuid4(),
            workspace_id=data.workspace_id,
            client_id=client_id,
            name=name,
            color=data.color or DEFAULT_COLOR,
            billable=data.billable,
            hourly_rate=data.hourly_rate,
            created_at=now,
            updated_at=now,
        )
        stored = await self._projects.add(project)
        await self._uow.commit()
        return stored
