from typing import cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from hourtime.domain.entities import MemberRole, User, Workspace, WorkspaceMember
from hourtime.domain.errors import NotFound
from hourtime.infrastructure.db.models import UserModel, WorkspaceMemberModel, WorkspaceModel
from hourtime.infrastructure.db.repositories.user_repository import to_domain as user_to_domain
from hourtime.infrastructure.db.repositories.workspace_repository import (
    to_domain as workspace_to_domain,
)
from hourtime.interfaces.repositories import WorkspaceMemberRepository


def to_domain(model: WorkspaceMemberModel) -> WorkspaceMember:
    return WorkspaceMember(
        workspace_id=model.workspace_id,
        user_id=model.user_id,
        role=cast(MemberRole, model.role),
        created_at=model.created_at,
    )


class SqlWorkspaceMemberRepository(WorkspaceMemberRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, workspace_id: UUID, user_id: UUID) -> WorkspaceMember | None:
        model = await self._session.get(WorkspaceMemberModel, (workspace_id, user_id))
        return to_domain(model) if model else None

    async def list_for_user(self, user_id: UUID) -> list[tuple[Workspace, MemberRole]]:
        statement = (
            sa.select(WorkspaceModel, WorkspaceMemberModel.role)
            .join(WorkspaceMemberModel, WorkspaceMemberModel.workspace_id == WorkspaceModel.id)
            .where(WorkspaceMemberModel.user_id == user_id)
            .order_by(sa.func.lower(WorkspaceModel.name), WorkspaceModel.created_at)
        )
        rows = (await self._session.execute(statement)).all()
        return [
            (workspace_to_domain(workspace), cast(MemberRole, role)) for workspace, role in rows
        ]

    async def list_for_workspace(self, workspace_id: UUID) -> list[tuple[WorkspaceMember, User]]:
        statement = (
            sa.select(WorkspaceMemberModel, UserModel)
            .join(UserModel, UserModel.id == WorkspaceMemberModel.user_id)
            .where(WorkspaceMemberModel.workspace_id == workspace_id)
            .order_by(WorkspaceMemberModel.created_at, UserModel.email)
        )
        rows = (await self._session.execute(statement)).all()
        return [(to_domain(member), user_to_domain(user)) for member, user in rows]

    async def add(self, member: WorkspaceMember) -> WorkspaceMember:
        model = WorkspaceMemberModel(**member.model_dump())
        self._session.add(model)
        await self._session.flush()
        return to_domain(model)

    async def update(self, member: WorkspaceMember) -> WorkspaceMember:
        model = await self._session.get(WorkspaceMemberModel, (member.workspace_id, member.user_id))
        if model is None:
            raise NotFound("Member not found")
        model.role = member.role
        await self._session.flush()
        return to_domain(model)

    async def remove(self, workspace_id: UUID, user_id: UUID) -> None:
        await self._session.execute(
            sa.delete(WorkspaceMemberModel).where(
                WorkspaceMemberModel.workspace_id == workspace_id,
                WorkspaceMemberModel.user_id == user_id,
            )
        )
