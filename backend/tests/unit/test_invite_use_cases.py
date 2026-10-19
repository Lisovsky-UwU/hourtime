from datetime import timedelta

import pytest

from hourtime.domain.entities import INVITE_TTL, WorkspaceMember
from hourtime.domain.errors import NotFound, PermissionDenied
from hourtime.use_cases.auth import RegisterUser
from hourtime.use_cases.dto import RegisterUserInput
from hourtime.use_cases.workspaces import (
    AcceptInvite,
    CreateInvite,
    ListMembers,
    PreviewInvite,
    RemoveMember,
    RevokeInvite,
    UpdateMember,
)
from tests.factories import NOW, make_user, make_workspace
from tests.fakes import (
    FakeClock,
    FakePasswordHasher,
    FakeTokenGenerator,
    FakeUnitOfWork,
    InMemoryUserRepository,
    InMemoryWorkspaceInviteRepository,
    InMemoryWorkspaceMemberRepository,
    InMemoryWorkspaceRepository,
)


class World:
    def __init__(self) -> None:
        self.clock = FakeClock(NOW)
        self.uow = FakeUnitOfWork()
        self.tokens = FakeTokenGenerator()
        self.owner = make_user()
        self.guest = make_user(email="guest@example.com")
        self.workspace = make_workspace(self.owner, name="Team")
        self.users = InMemoryUserRepository([self.owner, self.guest])
        self.workspaces = InMemoryWorkspaceRepository(
            [self.workspace, make_workspace(self.guest, name="Personal")]
        )
        self.members = InMemoryWorkspaceMemberRepository(self.workspaces, self.users)
        self.invites = InMemoryWorkspaceInviteRepository()
        for user in (self.owner, self.guest):
            self.members.items[(user.default_workspace_id, user.id)] = WorkspaceMember(
                workspace_id=user.default_workspace_id,
                user_id=user.id,
                role="admin",
                created_at=NOW,
            )

        self.create = CreateInvite(self.invites, self.tokens, self.clock, self.uow)
        self.revoke = RevokeInvite(self.invites, self.uow)
        self.preview = PreviewInvite(
            self.invites, self.workspaces, self.users, self.tokens, self.clock
        )
        self.accept = AcceptInvite(
            self.invites,
            self.members,
            self.workspaces,
            self.users,
            self.tokens,
            self.clock,
            self.uow,
        )
        self.listing = ListMembers(self.members, self.workspaces)
        self.update = UpdateMember(self.members, self.workspaces, self.uow)
        self.remove = RemoveMember(self.members, self.workspaces, self.users, self.clock, self.uow)

    async def invite(self) -> str:
        issued = await self.create.execute(
            self.workspace.id, self.owner.id, role="admin", invited_role="member"
        )
        return issued.token

    def register(self, *, allow_registration: bool) -> RegisterUser:
        return RegisterUser(
            self.users,
            self.workspaces,
            self.members,
            self.invites,
            self.tokens,
            FakePasswordHasher(),
            self.clock,
            self.uow,
            allow_registration=allow_registration,
            password_min_length=10,
        )


@pytest.fixture
def world() -> World:
    return World()


class TestInviteLink:
    async def test_member_may_not_invite(self, world: World) -> None:
        with pytest.raises(PermissionDenied):
            await world.create.execute(
                world.workspace.id, world.owner.id, role="member", invited_role="member"
            )

    async def test_accepting_joins_and_opens_the_workspace(self, world: World) -> None:
        token = await world.invite()
        preview = await world.preview.execute(token)
        assert (preview.workspace_name, preview.invited_by) == ("Team", world.owner.email)

        joined = await world.accept.execute(world.guest, token)

        assert (joined.workspace.id, joined.role) == (world.workspace.id, "member")
        assert world.users.items[world.guest.id].default_workspace_id == world.workspace.id

    async def test_a_link_works_once(self, world: World) -> None:
        token = await world.invite()
        await world.accept.execute(world.guest, token)
        stranger = await world.users.add(make_user(email="third@example.com"))
        with pytest.raises(NotFound):
            await world.accept.execute(stranger, token)

    async def test_an_expired_link_is_refused(self, world: World) -> None:
        token = await world.invite()
        world.clock.advance(INVITE_TTL + timedelta(seconds=1))
        with pytest.raises(NotFound):
            await world.preview.execute(token)

    async def test_a_revoked_link_is_refused(self, world: World) -> None:
        token = await world.invite()
        invite = next(iter(world.invites.items.values()))
        await world.revoke.execute(world.workspace.id, invite.id, role="admin")
        with pytest.raises(NotFound):
            await world.accept.execute(world.guest, token)

    async def test_registers_with_registration_closed(self, world: World) -> None:
        token = await world.invite()
        user = await world.register(allow_registration=False).execute(
            RegisterUserInput(email="new@example.com", password="correct-horse", invite_token=token)
        )
        assert user.default_workspace_id == world.workspace.id
        member = await world.members.get(world.workspace.id, user.id)
        assert member is not None and member.role == "member"
        personal = await world.workspaces.first_owned(user.id)
        assert personal is not None and personal.id != world.workspace.id


class TestMembers:
    async def joined(self, world: World) -> None:
        await world.accept.execute(world.guest, await world.invite())

    async def test_lists_with_the_owner_marked(self, world: World) -> None:
        await self.joined(world)
        found = await world.listing.execute(world.workspace.id)
        assert [(a.user.email, a.member.role, a.is_owner) for a in found] == [
            (world.owner.email, "admin", True),
            (world.guest.email, "member", False),
        ]

    async def test_owner_stays_an_admin(self, world: World) -> None:
        with pytest.raises(PermissionDenied):
            await world.update.execute(world.workspace.id, world.owner.id, "member", role="admin")
        owner = await world.members.get(world.workspace.id, world.owner.id)
        assert owner is not None
        with pytest.raises(PermissionDenied):
            await world.remove.execute(world.workspace.id, world.owner.id, caller=owner)

    async def test_member_leaves_and_falls_back_to_their_own_workspace(self, world: World) -> None:
        await self.joined(world)
        guest = await world.members.get(world.workspace.id, world.guest.id)
        assert guest is not None
        await world.remove.execute(world.workspace.id, world.guest.id, caller=guest)
        assert await world.members.get(world.workspace.id, world.guest.id) is None
        assert world.users.items[world.guest.id].default_workspace_id == (
            world.guest.default_workspace_id
        )

    async def test_member_may_not_remove_others(self, world: World) -> None:
        await self.joined(world)
        third = await world.users.add(make_user(email="third@example.com"))
        await world.accept.execute(third, await world.invite())
        guest = await world.members.get(world.workspace.id, world.guest.id)
        assert guest is not None
        with pytest.raises(PermissionDenied):
            await world.remove.execute(world.workspace.id, third.id, caller=guest)
