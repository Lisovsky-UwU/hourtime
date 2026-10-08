from functools import lru_cache
from typing import Literal
from uuid import UUID
from zoneinfo import available_timezones

from pydantic import EmailStr, Field, field_validator

from hourtime.domain.entities.base import Entity, UtcDatetime

DISPLAY_NAME_MAX_LENGTH = 100
TIMEZONE_MAX_LENGTH = 64

# How durations are written: `classic` - 1:05, `decimal` - 1.08, `improved` - 1:05:00.
DurationFormat = Literal["classic", "decimal", "improved"]
HourCycle = Literal[12, 24]


@lru_cache(maxsize=1)
def _known_timezones() -> frozenset[str]:
    # Reads the zone database from disk, and users are rebuilt on every request.
    return frozenset(available_timezones())


class User(Entity):
    id: UUID
    email: EmailStr
    password_hash: str
    is_active: bool = True
    # Where the API puts projects and entries until workspaces can be picked.
    default_workspace_id: UUID
    display_name: str | None = Field(default=None, max_length=DISPLAY_NAME_MAX_LENGTH)
    # IANA name. None until the first client reports its zone: a default of UTC
    # could not be told apart from a deliberate choice of UTC.
    timezone: str | None = None
    # 0 = Sunday ... 6 = Saturday, same numbering as JavaScript's getDay().
    week_start: int = Field(default=1, ge=0, le=6)
    duration_format: DurationFormat = "classic"
    hour_cycle: HourCycle = 24
    created_at: UtcDatetime
    updated_at: UtcDatetime

    @field_validator("email", mode="before")
    @classmethod
    def _normalise_email(cls, value: object) -> object:
        """Emails are matched case-insensitively, so store them folded."""
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("display_name", mode="before")
    @classmethod
    def _blank_name_is_none(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip() or None
        return value

    @field_validator("timezone")
    @classmethod
    def _known_timezone(cls, value: str | None) -> str | None:
        if value is not None and value not in _known_timezones():
            raise ValueError("must be an IANA time zone such as Europe/Moscow")
        return value
