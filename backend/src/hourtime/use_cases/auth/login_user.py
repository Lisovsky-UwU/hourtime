from hourtime.domain.errors import AccountDisabled, InvalidCredentials
from hourtime.interfaces.repositories import UserRepository
from hourtime.interfaces.services import Clock, PasswordHasher, UnitOfWork
from hourtime.use_cases.auth.session_issuer import SessionIssuer
from hourtime.use_cases.dto import LoginResult, LoginUserInput


class LoginUser:
    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        issuer: SessionIssuer,
        clock: Clock,
        uow: UnitOfWork,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._issuer = issuer
        self._clock = clock
        self._uow = uow

    async def execute(self, data: LoginUserInput) -> LoginResult:
        user = await self._users.get_by_email(data.email.strip().lower())
        if user is None:
            # Hash anyway so a missing account is not faster than a wrong password.
            self._hasher.hash(data.password)
            raise InvalidCredentials
        if not self._hasher.verify(data.password, user.password_hash):
            raise InvalidCredentials
        if not user.is_active:
            raise AccountDisabled

        if self._hasher.needs_rehash(user.password_hash):
            user = await self._users.update(
                user.evolve(
                    password_hash=self._hasher.hash(data.password),
                    updated_at=self._clock.now(),
                )
            )

        issued = await self._issuer.issue(user.id, user_agent=data.user_agent, ip=data.ip)
        await self._uow.commit()
        return LoginResult(user=user, tokens=issued.tokens)
