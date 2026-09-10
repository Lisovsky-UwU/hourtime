from uuid import uuid4

from hourtime.domain.entities import User
from hourtime.domain.errors import EmailAlreadyUsed, RegistrationDisabled, ValidationError
from hourtime.interfaces.repositories import UserRepository
from hourtime.interfaces.services import Clock, PasswordHasher, UnitOfWork
from hourtime.use_cases.dto import RegisterUserInput


class RegisterUser:
    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        clock: Clock,
        uow: UnitOfWork,
        *,
        allow_registration: bool,
        password_min_length: int,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._clock = clock
        self._uow = uow
        self._allow_registration = allow_registration
        self._password_min_length = password_min_length

    async def execute(self, data: RegisterUserInput) -> User:
        if not self._allow_registration:
            raise RegistrationDisabled

        if len(data.password) < self._password_min_length:
            raise ValidationError(
                f"The password must be at least {self._password_min_length} characters long"
            )

        email = data.email.strip().lower()
        if await self._users.get_by_email(email) is not None:
            raise EmailAlreadyUsed

        now = self._clock.now()
        user = User(
            id=uuid4(),
            email=email,
            password_hash=self._hasher.hash(data.password),
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        # The repository turns a lost unique-index race into EmailAlreadyUsed.
        stored = await self._users.add(user)
        await self._uow.commit()
        return stored
