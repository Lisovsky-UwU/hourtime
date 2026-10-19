from uuid import uuid4

from hourtime.domain.entities import PERSONAL_WORKSPACE_NAME, User, Workspace, WorkspaceMember
from hourtime.domain.errors import EmailAlreadyUsed, RegistrationDisabled, ValidationError
from hourtime.interfaces.repositories import (
    UserRepository,
    WorkspaceInviteRepository,
    WorkspaceMemberRepository,
    WorkspaceRepository,
)
from hourtime.interfaces.services import Clock, PasswordHasher, TokenGenerator, UnitOfWork
from hourtime.use_cases.dto import RegisterUserInput
from hourtime.use_cases.workspaces.invites import find_open_invite, join


class RegisterUser:
    def __init__(
        self,
        users: UserRepository,
        workspaces: WorkspaceRepository,
        members: WorkspaceMemberRepository,
        invites: WorkspaceInviteRepository,
        tokens: TokenGenerator,
        hasher: PasswordHasher,
        clock: Clock,
        uow: UnitOfWork,
        *,
        allow_registration: bool,
        password_min_length: int,
    ) -> None:
        self._users = users
        self._workspaces = workspaces
        self._members = members
        self._invites = invites
        self._tokens = tokens
        self._hasher = hasher
        self._clock = clock
        self._uow = uow
        self._allow_registration = allow_registration
        self._password_min_length = password_min_length

    async def execute(self, data: RegisterUserInput) -> User:
        now = self._clock.now()
        invite = None
        if data.invite_token is not None:
            invite = await find_open_invite(self._invites, self._tokens, data.invite_token, now)
        elif not self._allow_registration:
            raise RegistrationDisabled

        if len(data.password) < self._password_min_length:
            raise ValidationError(
                f"The password must be at least {self._password_min_length} characters long"
            )

        email = data.email.strip().lower()
        if await self._users.get_by_email(email) is not None:
            raise EmailAlreadyUsed

        user = User(
            id=uuid4(),
            email=email,
            password_hash=self._hasher.hash(data.password),
            is_active=True,
            default_workspace_id=uuid4(),
            created_at=now,
            updated_at=now,
        )
        # The user goes in first: the repository turns a lost unique-index race
        # into EmailAlreadyUsed, and the workspace needs its owner to exist.
        stored = await self._users.add(user)
        await self._workspaces.add(
            Workspace(
                id=user.default_workspace_id,
                name=PERSONAL_WORKSPACE_NAME,
                owner_id=user.id,
                created_at=now,
                updated_at=now,
            )
        )
        await self._members.add(
            WorkspaceMember(
                workspace_id=user.default_workspace_id,
                user_id=user.id,
                role="admin",
                created_at=now,
            )
        )
        if invite is not None:
            stored, _ = await join(self._members, self._users, self._invites, invite, stored, now)
        await self._uow.commit()
        return stored
