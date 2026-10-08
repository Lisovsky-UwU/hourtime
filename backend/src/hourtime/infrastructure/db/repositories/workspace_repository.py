from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from hourtime.domain.entities import Workspace
from hourtime.domain.errors import NotFound
from hourtime.infrastructure.db.models import WorkspaceModel
from hourtime.interfaces.repositories import WorkspaceRepository


def to_domain(model: WorkspaceModel) -> Workspace:
    return Workspace(
        id=model.id,
        name=model.name,
        owner_id=model.owner_id,
        default_hourly_rate=model.default_hourly_rate,
        currency=model.currency,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlWorkspaceRepository(WorkspaceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, workspace_id: UUID) -> Workspace | None:
        model = await self._session.get(WorkspaceModel, workspace_id)
        return to_domain(model) if model else None

    async def add(self, workspace: Workspace) -> Workspace:
        model = WorkspaceModel(**workspace.model_dump())
        self._session.add(model)
        await self._session.flush()
        return to_domain(model)

    async def update(self, workspace: Workspace) -> Workspace:
        model = await self._session.get(WorkspaceModel, workspace.id)
        if model is None:
            raise NotFound("Workspace not found")
        for field, value in workspace.model_dump().items():
            setattr(model, field, value)
        await self._session.flush()
        return to_domain(model)
