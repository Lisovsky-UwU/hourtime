from uuid import uuid4

from hourtime.domain.entities import DEFAULT_COLOR, Project
from hourtime.domain.errors import ProjectNameTaken
from hourtime.interfaces.repositories import ProjectRepository
from hourtime.interfaces.services import Clock, UnitOfWork
from hourtime.use_cases.dto import CreateProjectInput


class CreateProject:
    def __init__(self, projects: ProjectRepository, clock: Clock, uow: UnitOfWork) -> None:
        self._projects = projects
        self._clock = clock
        self._uow = uow

    async def execute(self, data: CreateProjectInput) -> Project:
        name = data.name.strip()
        if await self._projects.find_by_name(data.workspace_id, name) is not None:
            raise ProjectNameTaken

        now = self._clock.now()
        project = Project(
            id=uuid4(),
            workspace_id=data.workspace_id,
            name=name,
            color=data.color or DEFAULT_COLOR,
            created_at=now,
            updated_at=now,
        )
        stored = await self._projects.add(project)
        await self._uow.commit()
        return stored
