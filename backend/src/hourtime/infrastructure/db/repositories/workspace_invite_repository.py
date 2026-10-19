from datetime import datetime
from typing import cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from hourtime.domain.entities import MemberRole, WorkspaceInvite
from hourtime.domain.errors import NotFound
from hourtime.infrastructure.db.models import WorkspaceInviteModel
from hourtime.interfaces.repositories import WorkspaceInviteRepository


def to_domain(model: WorkspaceInviteModel) -> WorkspaceInvite:
    return WorkspaceInvite(
        id=model.id,
        workspace_id=model.workspace_id,
        token_hash=model.token_hash,
        role=cast(MemberRole, model.role),
        created_by=model.created_by,
        created_at=model.created_at,
        expires_at=model.expires_at,
        used_at=model.used_at,
    )


class SqlWorkspaceInviteRepository(WorkspaceInviteRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, invite_id: UUID) -> WorkspaceInvite | None:
        model = await self._session.get(WorkspaceInviteModel, invite_id)
        return to_domain(model) if model else None

    async def get_by_token_hash(self, token_hash: str) -> WorkspaceInvite | None:
        statement = sa.select(WorkspaceInviteModel).where(
            WorkspaceInviteModel.token_hash == token_hash
        )
        model = (await self._session.execute(statement)).scalar_one_or_none()
        return to_domain(model) if model else None

    async def list_open(self, workspace_id: UUID, now: datetime) -> list[WorkspaceInvite]:
        statement = (
            sa.select(WorkspaceInviteModel)
            .where(
                WorkspaceInviteModel.workspace_id == workspace_id,
                WorkspaceInviteModel.used_at.is_(None),
                WorkspaceInviteModel.expires_at > now,
            )
            .order_by(WorkspaceInviteModel.created_at.desc())
        )
        models = (await self._session.execute(statement)).scalars().all()
        return [to_domain(model) for model in models]

    async def add(self, invite: WorkspaceInvite) -> WorkspaceInvite:
        model = WorkspaceInviteModel(**invite.model_dump())
        self._session.add(model)
        await self._session.flush()
        return to_domain(model)

    async def update(self, invite: WorkspaceInvite) -> WorkspaceInvite:
        model = await self._session.get(WorkspaceInviteModel, invite.id)
        if model is None:
            raise NotFound("Invite not found")
        for field, value in invite.model_dump().items():
            setattr(model, field, value)
        await self._session.flush()
        return to_domain(model)

    async def delete(self, invite_id: UUID) -> None:
        await self._session.execute(
            sa.delete(WorkspaceInviteModel).where(WorkspaceInviteModel.id == invite_id)
        )
