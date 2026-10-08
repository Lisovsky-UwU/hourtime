from sqlalchemy.ext.asyncio import AsyncSession

from hourtime.domain.entities import Workspace
from hourtime.infrastructure.db.models import WorkspaceModel
from hourtime.interfaces.repositories import WorkspaceRepository


def to_domain(model: WorkspaceModel) -> Workspace:
    return Workspace(
        id=model.id,
        name=model.name,
        owner_id=model.owner_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlWorkspaceRepository(WorkspaceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, workspace: Workspace) -> Workspace:
        model = WorkspaceModel(**workspace.model_dump())
        self._session.add(model)
        await self._session.flush()
        return to_domain(model)
