"""Who is in a workspace. The owner is always an admin and can be neither demoted nor removed."""

from uuid import UUID

from hourtime.domain.entities import MemberRole, Workspace, WorkspaceMember
from hourtime.domain.errors import NotFound, PermissionDenied
from hourtime.interfaces.repositories import (
    UserRepository,
    WorkspaceMemberRepository,
    WorkspaceRepository,
)
from hourtime.interfaces.services import Clock, UnitOfWork
from hourtime.use_cases.access import require_admin
from hourtime.use_cases.dto import MemberAccount


async def _workspace(workspaces: WorkspaceRepository, workspace_id: UUID) -> Workspace:
    workspace = await workspaces.get_by_id(workspace_id)
    if workspace is None:
        raise NotFound("Workspace not found")
    return workspace


async def _other_member(
    members: WorkspaceMemberRepository, workspace: Workspace, user_id: UUID
) -> WorkspaceMember:
    if user_id == workspace.owner_id:
        raise PermissionDenied("The owner always stays an admin of the workspace")
    member = await members.get(workspace.id, user_id)
    if member is None:
        raise NotFound("Member not found")
    return member


class ListMembers:
    def __init__(self, members: WorkspaceMemberRepository, workspaces: WorkspaceRepository) -> None:
        self._members = members
        self._workspaces = workspaces

    async def execute(self, workspace_id: UUID) -> list[MemberAccount]:
        workspace = await _workspace(self._workspaces, workspace_id)
        found = await self._members.list_for_workspace(workspace_id)
        return [
            MemberAccount(member=member, user=user, is_owner=user.id == workspace.owner_id)
            for member, user in found
        ]


class UpdateMember:
    def __init__(
        self,
        members: WorkspaceMemberRepository,
        workspaces: WorkspaceRepository,
        uow: UnitOfWork,
    ) -> None:
        self._members = members
        self._workspaces = workspaces
        self._uow = uow

    async def execute(
        self, workspace_id: UUID, user_id: UUID, new_role: MemberRole, *, role: MemberRole
    ) -> WorkspaceMember:
        require_admin(role)
        workspace = await _workspace(self._workspaces, workspace_id)
        member = await _other_member(self._members, workspace, user_id)
        updated = await self._members.update(member.evolve(role=new_role))
        await self._uow.commit()
        return updated


class RemoveMember:
    """An admin removes anyone but the owner; anyone but the owner may leave."""

    def __init__(
        self,
        members: WorkspaceMemberRepository,
        workspaces: WorkspaceRepository,
        users: UserRepository,
        clock: Clock,
        uow: UnitOfWork,
    ) -> None:
        self._members = members
        self._workspaces = workspaces
        self._users = users
        self._clock = clock
        self._uow = uow

    async def execute(self, workspace_id: UUID, user_id: UUID, *, caller: WorkspaceMember) -> None:
        if caller.user_id != user_id:
            require_admin(caller.role)
        workspace = await _workspace(self._workspaces, workspace_id)
        await _other_member(self._members, workspace, user_id)
        await self._members.remove(workspace_id, user_id)

        # Their entries stay in the workspace; they just open their own one next time.
        user = await self._users.get_by_id(user_id)
        if user is not None and user.default_workspace_id == workspace_id:
            personal = await self._workspaces.first_owned(user_id)
            if personal is not None:
                await self._users.update(
                    user.evolve(default_workspace_id=personal.id, updated_at=self._clock.now())
                )
        await self._uow.commit()
