from uuid import UUID, uuid4

from hourtime.domain.entities import Workspace, WorkspaceMember
from hourtime.interfaces.repositories import WorkspaceMemberRepository, WorkspaceRepository
from hourtime.interfaces.services import Clock, UnitOfWork
from hourtime.use_cases.dto import MemberWorkspace


class CreateWorkspace:
    """Anyone may start a workspace; they own it and are its first admin."""

    def __init__(
        self,
        workspaces: WorkspaceRepository,
        members: WorkspaceMemberRepository,
        clock: Clock,
        uow: UnitOfWork,
    ) -> None:
        self._workspaces = workspaces
        self._members = members
        self._clock = clock
        self._uow = uow

    async def execute(self, user_id: UUID, name: str) -> MemberWorkspace:
        now = self._clock.now()
        workspace = await self._workspaces.add(
            Workspace(id=uuid4(), name=name, owner_id=user_id, created_at=now, updated_at=now)
        )
        await self._members.add(
            WorkspaceMember(
                workspace_id=workspace.id, user_id=user_id, role="admin", created_at=now
            )
        )
        await self._uow.commit()
        return MemberWorkspace(workspace=workspace, role="admin")
