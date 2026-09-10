from uuid import UUID

from pydantic import EmailStr, field_validator

from hourtime.domain.entities.base import Entity, UtcDatetime


class User(Entity):
    id: UUID
    email: EmailStr
    password_hash: str
    is_active: bool = True
    created_at: UtcDatetime
    updated_at: UtcDatetime

    @field_validator("email", mode="before")
    @classmethod
    def _normalise_email(cls, value: object) -> object:
        """Emails are matched case-insensitively, so store them folded."""
        if isinstance(value, str):
            return value.strip().lower()
        return value
