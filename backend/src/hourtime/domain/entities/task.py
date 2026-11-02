from uuid import UUID

from pydantic import Field, field_validator

from hourtime.domain.entities.base import Entity, UtcDatetime

NAME_MAX_LENGTH = 100


class Task(Entity):
    id: UUID
    project_id: UUID
    name: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)
    estimated_seconds: int | None = Field(default=None, gt=0)
    completed_at: UtcDatetime | None = None
    created_at: UtcDatetime
    updated_at: UtcDatetime

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @property
    def is_completed(self) -> bool:
        return self.completed_at is not None
