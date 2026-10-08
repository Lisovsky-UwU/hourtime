from uuid import UUID

from pydantic import Field, field_validator

from hourtime.domain.entities.base import Entity, UtcDatetime

NAME_MAX_LENGTH = 100


class Client(Entity):
    """Who the work is for; groups projects."""

    id: UUID
    workspace_id: UUID
    name: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)
    archived_at: UtcDatetime | None = None
    created_at: UtcDatetime
    updated_at: UtcDatetime

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @property
    def is_archived(self) -> bool:
        return self.archived_at is not None
