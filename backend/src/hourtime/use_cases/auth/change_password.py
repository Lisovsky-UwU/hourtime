from hourtime.domain.errors import InvalidCurrentPassword, NotFound, ValidationError
from hourtime.interfaces.repositories import SessionRepository, UserRepository
from hourtime.interfaces.services import Clock, PasswordHasher, UnitOfWork
from hourtime.use_cases.dto import ChangePasswordInput


class ChangePassword:
    """Replaces the password and signs out every other device.

    A password is usually changed because it may have leaked, so whoever is
    holding a session made with the old one loses it right away.
    """

    def __init__(
        self,
        users: UserRepository,
        sessions: SessionRepository,
        hasher: PasswordHasher,
        clock: Clock,
        uow: UnitOfWork,
        *,
        password_min_length: int,
    ) -> None:
        self._users = users
        self._sessions = sessions
        self._hasher = hasher
        self._clock = clock
        self._uow = uow
        self._password_min_length = password_min_length

    async def execute(self, data: ChangePasswordInput) -> None:
        user = await self._users.get_by_id(data.user_id)
        if user is None:
            raise NotFound("User not found")

        if not self._hasher.verify(data.current_password, user.password_hash):
            raise InvalidCurrentPassword

        if len(data.new_password) < self._password_min_length:
            raise ValidationError(
                f"The password must be at least {self._password_min_length} characters long"
            )

        now = self._clock.now()
        await self._users.update(
            user.evolve(password_hash=self._hasher.hash(data.new_password), updated_at=now)
        )
        await self._sessions.revoke_all_for_user(user.id, now, keep=data.session_id)
        await self._uow.commit()
