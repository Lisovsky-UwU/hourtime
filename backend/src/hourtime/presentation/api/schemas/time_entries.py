from datetime import datetime
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from hourtime.domain.entities import TimeEntry
from hourtime.domain.entities.time_entry import DESCRIPTION_MAX_LENGTH
from hourtime.use_cases.dto import TimeEntryPage


class TimeEntryResponse(BaseModel):
    id: UUID
    project_id: UUID | None
    description: str
    started_at: datetime
    stopped_at: datetime | None
    # Null while the timer runs: the client ticks that number itself, using
    # `started_at` and the server clock from the X-Server-Time header.
    duration_seconds: int | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, entry: TimeEntry) -> "TimeEntryResponse":
        duration = (
            None
            if entry.stopped_at is None
            else int((entry.stopped_at - entry.started_at).total_seconds())
        )
        return cls(
            id=entry.id,
            project_id=entry.project_id,
            description=entry.description,
            started_at=entry.started_at,
            stopped_at=entry.stopped_at,
            duration_seconds=duration,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )


class TimeEntryPageResponse(BaseModel):
    items: list[TimeEntryResponse]
    total: int
    limit: int
    offset: int

    @classmethod
    def of(cls, page: TimeEntryPage) -> "TimeEntryPageResponse":
        return cls(
            items=[TimeEntryResponse.of(entry) for entry in page.items],
            total=page.total,
            limit=page.limit,
            offset=page.offset,
        )


class StartTimerRequest(BaseModel):
    project_id: UUID | None = None
    description: str = Field(default="", max_length=DESCRIPTION_MAX_LENGTH)
    # Defaults to the server's "now" when omitted.
    started_at: AwareDatetime | None = None


class StopTimerRequest(BaseModel):
    stopped_at: AwareDatetime | None = None


class CreateTimeEntryRequest(BaseModel):
    project_id: UUID | None = None
    description: str = Field(default="", max_length=DESCRIPTION_MAX_LENGTH)
    started_at: AwareDatetime
    stopped_at: AwareDatetime


class UpdateTimeEntryRequest(BaseModel):
    """Omitted fields are left untouched; `project_id: null` clears the project."""

    model_config = ConfigDict(extra="forbid")

    project_id: UUID | None = None
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    started_at: AwareDatetime | None = None
    stopped_at: AwareDatetime | None = None
