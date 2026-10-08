from uuid import UUID

from pydantic import Field, field_validator

from hourtime.domain.entities.base import Entity, UtcDatetime

NAME_MAX_LENGTH = 100


class Tag(Entity):
    """A free-form label on time entries. Unlike projects and clients, tags are never archived."""

    id: UUID
    workspace_id: UUID
    name: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)
    created_at: UtcDatetime
    updated_at: UtcDatetime

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value
