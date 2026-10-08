from typing import Any

from hourtime.domain.entities import User
from hourtime.domain.errors import NotFound, ValidationError
from hourtime.interfaces.repositories import UserRepository
from hourtime.interfaces.services import Clock, UnitOfWork
from hourtime.use_cases.dto import UpdateProfileInput

# Only the display name may be cleared; the rest always has a value once set.
_REQUIRED = ("timezone", "week_start", "duration_format", "hour_cycle")


class UpdateProfile:
    """Everything PATCH /auth/me can change. Email and password have their own paths."""

    def __init__(self, users: UserRepository, clock: Clock, uow: UnitOfWork) -> None:
        self._users = users
        self._clock = clock
        self._uow = uow

    async def execute(self, data: UpdateProfileInput) -> User:
        user = await self._users.get_by_id(data.user_id)
        if user is None:
            raise NotFound("User not found")

        changes: dict[str, Any] = {}
        for field in ("display_name", *_REQUIRED):
            if not data.provided(field):
                continue
            value = getattr(data, field)
            if value is None and field in _REQUIRED:
                raise ValidationError(f"{field}: may not be null")
            changes[field] = value

        if not changes:
            return user

        changes["updated_at"] = self._clock.now()
        updated = await self._users.update(user.evolve(**changes))
        await self._uow.commit()
        return updated
