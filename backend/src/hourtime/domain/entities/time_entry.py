from datetime import datetime, timedelta
from typing import Self
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from hourtime.domain.entities.base import Entity, UtcDatetime

DESCRIPTION_MAX_LENGTH = 1000


class TimeEntry(Entity):
    """A tracked interval. `stopped_at is None` means the timer is still running."""

    id: UUID
    # Who tracked it. Within a shared workspace this is what keeps one member's
    # entries apart from another's.
    user_id: UUID
    workspace_id: UUID
    project_id: UUID | None = None
    # Sorted by id and free of duplicates, so the same set of tags always reads
    # the same no matter how it was sent or stored.
    tag_ids: list[UUID] = Field(default_factory=list)
    description: str = Field(default="", max_length=DESCRIPTION_MAX_LENGTH)
    billable: bool = False
    started_at: UtcDatetime
    stopped_at: UtcDatetime | None = None
    created_at: UtcDatetime
    updated_at: UtcDatetime

    @field_validator("description", mode="before")
    @classmethod
    def _clean_description(cls, value: object) -> object:
        if value is None:
            return ""
        return value.strip() if isinstance(value, str) else value

    @field_validator("tag_ids", mode="after")
    @classmethod
    def _normalise_tag_ids(cls, value: list[UUID]) -> list[UUID]:
        return sorted(set(value))

    @model_validator(mode="after")
    def _check_interval(self) -> Self:
        if self.stopped_at is not None and self.stopped_at <= self.started_at:
            raise ValueError("stopped_at must be later than started_at")
        return self

    @property
    def is_running(self) -> bool:
        return self.stopped_at is None

    def duration(self, now: datetime) -> timedelta:
        """Elapsed time; a running entry is measured against `now`."""
        return (self.stopped_at or now) - self.started_at

    def stop(self, at: datetime) -> "TimeEntry":
        return self.evolve(stopped_at=at, updated_at=at)


class TimeEntrySuggestion(Entity):
    """A description and project pair tracked before, offered while typing a new one."""

    description: str
    project_id: UUID | None = None
    last_used_at: UtcDatetime
