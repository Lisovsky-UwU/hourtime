from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from hourtime.domain.entities import Client
from hourtime.domain.errors import NotFound
from hourtime.infrastructure.db.models import ClientModel
from hourtime.infrastructure.db.repositories.integrity import translating_integrity_errors
from hourtime.interfaces.repositories import ClientRepository


def to_domain(model: ClientModel) -> Client:
    return Client(
        id=model.id,
        workspace_id=model.workspace_id,
        name=model.name,
        archived_at=model.archived_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlClientRepository(ClientRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, client_id: UUID) -> Client | None:
        model = await self._session.get(ClientModel, client_id)
        return to_domain(model) if model else None

    async def list_for_workspace(
        self, workspace_id: UUID, *, include_archived: bool = False
    ) -> list[Client]:
        statement = sa.select(ClientModel).where(ClientModel.workspace_id == workspace_id)
        if not include_archived:
            statement = statement.where(ClientModel.archived_at.is_(None))
        statement = statement.order_by(sa.func.lower(ClientModel.name))
        models = (await self._session.execute(statement)).scalars().all()
        return [to_domain(model) for model in models]

    async def find_by_name(self, workspace_id: UUID, name: str) -> Client | None:
        statement = sa.select(ClientModel).where(
            ClientModel.workspace_id == workspace_id,
            sa.func.lower(ClientModel.name) == name.strip().lower(),
            ClientModel.archived_at.is_(None),
        )
        model = (await self._session.execute(statement)).scalar_one_or_none()
        return to_domain(model) if model else None

    async def add(self, client: Client) -> Client:
        model = ClientModel(**client.model_dump())
        self._session.add(model)
        await translating_integrity_errors(self._session.flush)
        return to_domain(model)

    async def update(self, client: Client) -> Client:
        model = await self._session.get(ClientModel, client.id)
        if model is None:
            raise NotFound("Client not found")
        for field, value in client.model_dump().items():
            setattr(model, field, value)
        await translating_integrity_errors(self._session.flush)
        return to_domain(model)

    async def delete(self, client_id: UUID) -> None:
        model = await self._session.get(ClientModel, client_id)
        if model is None:
            raise NotFound("Client not found")
        # `projects.client_id` is ON DELETE SET NULL, so the projects survive.
        await self._session.delete(model)
        await self._session.flush()
