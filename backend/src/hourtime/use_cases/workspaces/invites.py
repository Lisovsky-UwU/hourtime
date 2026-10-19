"""Invite links: issued by admins, redeemed once by whoever opens them."""

from datetime import datetime
from uuid import UUID, uuid4

from hourtime.domain.entities import (
    INVITE_TTL,
    MemberRole,
    User,
    Workspace,
    WorkspaceInvite,
    WorkspaceMember,
)
from hourtime.domain.errors import NotFound
from hourtime.interfaces.repositories import (
    UserRepository,
    WorkspaceInviteRepository,
    WorkspaceMemberRepository,
    WorkspaceRepository,
)
from hourtime.interfaces.services import Clock, TokenGenerator, UnitOfWork
from hourtime.use_cases.access import require_admin
from hourtime.use_cases.dto import InvitePreview, IssuedInvite, MemberWorkspace


async def find_open_invite(
    invites: WorkspaceInviteRepository, tokens: TokenGenerator, token: str, now: datetime
) -> WorkspaceInvite:
    invite = await invites.get_by_token_hash(tokens.hash(token))
    if invite is None or not invite.is_open(now):
        raise NotFound("This invite link is invalid, used or expired")
    return invite


async def join(
    members: WorkspaceMemberRepository,
    users: UserRepository,
    invites: WorkspaceInviteRepository,
    invite: WorkspaceInvite,
    user: User,
    now: datetime,
) -> tuple[User, MemberRole]:
    """Adds the user, spends the link and opens the workspace for them next time.

    Someone who is already in keeps their role and leaves the link for another person.
    """
    member = await members.get(invite.workspace_id, user.id)
    if member is None:
        member = await members.add(
            WorkspaceMember(
                workspace_id=invite.workspace_id,
                user_id=user.id,
                role=invite.role,
                created_at=now,
            )
        )
        await invites.update(invite.evolve(used_at=now))
    if user.default_workspace_id != invite.workspace_id:
        user = await users.update(
            user.evolve(default_workspace_id=invite.workspace_id, updated_at=now)
        )
    return user, member.role


class CreateInvite:
    def __init__(
        self,
        invites: WorkspaceInviteRepository,
        tokens: TokenGenerator,
        clock: Clock,
        uow: UnitOfWork,
    ) -> None:
        self._invites = invites
        self._tokens = tokens
        self._clock = clock
        self._uow = uow

    async def execute(
        self, workspace_id: UUID, user_id: UUID, *, role: MemberRole, invited_role: MemberRole
    ) -> IssuedInvite:
        require_admin(role)
        now = self._clock.now()
        token = self._tokens.generate()
        invite = await self._invites.add(
            WorkspaceInvite(
                id=uuid4(),
                workspace_id=workspace_id,
                token_hash=self._tokens.hash(token),
                role=invited_role,
                created_by=user_id,
                created_at=now,
                expires_at=now + INVITE_TTL,
            )
        )
        await self._uow.commit()
        return IssuedInvite(invite=invite, token=token)


class ListInvites:
    def __init__(self, invites: WorkspaceInviteRepository, clock: Clock) -> None:
        self._invites = invites
        self._clock = clock

    async def execute(self, workspace_id: UUID, *, role: MemberRole) -> list[WorkspaceInvite]:
        require_admin(role)
        return await self._invites.list_open(workspace_id, self._clock.now())


class RevokeInvite:
    def __init__(self, invites: WorkspaceInviteRepository, uow: UnitOfWork) -> None:
        self._invites = invites
        self._uow = uow

    async def execute(self, workspace_id: UUID, invite_id: UUID, *, role: MemberRole) -> None:
        require_admin(role)
        invite = await self._invites.get_by_id(invite_id)
        if invite is None or invite.workspace_id != workspace_id:
            raise NotFound("Invite not found")
        await self._invites.delete(invite.id)
        await self._uow.commit()


class PreviewInvite:
    def __init__(
        self,
        invites: WorkspaceInviteRepository,
        workspaces: WorkspaceRepository,
        users: UserRepository,
        tokens: TokenGenerator,
        clock: Clock,
    ) -> None:
        self._invites = invites
        self._workspaces = workspaces
        self._users = users
        self._tokens = tokens
        self._clock = clock

    async def execute(self, token: str) -> InvitePreview:
        invite = await find_open_invite(self._invites, self._tokens, token, self._clock.now())
        workspace = await self._workspaces.get_by_id(invite.workspace_id)
        inviter = await self._users.get_by_id(invite.created_by)
        if workspace is None or inviter is None:
            raise NotFound("This invite link is invalid, used or expired")
        return InvitePreview(
            workspace_name=workspace.name,
            invited_by=inviter.display_name or inviter.email,
            role=invite.role,
        )


class AcceptInvite:
    def __init__(
        self,
        invites: WorkspaceInviteRepository,
        members: WorkspaceMemberRepository,
        workspaces: WorkspaceRepository,
        users: UserRepository,
        tokens: TokenGenerator,
        clock: Clock,
        uow: UnitOfWork,
    ) -> None:
        self._invites = invites
        self._members = members
        self._workspaces = workspaces
        self._users = users
        self._tokens = tokens
        self._clock = clock
        self._uow = uow

    async def execute(self, user: User, token: str) -> MemberWorkspace:
        now = self._clock.now()
        invite = await find_open_invite(self._invites, self._tokens, token, now)
        workspace: Workspace | None = await self._workspaces.get_by_id(invite.workspace_id)
        if workspace is None:
            raise NotFound("This invite link is invalid, used or expired")
        _, role = await join(self._members, self._users, self._invites, invite, user, now)
        await self._uow.commit()
        return MemberWorkspace(workspace=workspace, role=role)
