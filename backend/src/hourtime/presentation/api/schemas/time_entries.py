from datetime import datetime
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from hourtime.domain.entities import TimeEntry, TimeEntrySuggestion
from hourtime.domain.entities.time_entry import DESCRIPTION_MAX_LENGTH
from hourtime.use_cases.dto import TimeEntryPage


class TimeEntryResponse(BaseModel):
    id: UUID
    project_id: UUID | None
    # Sorted by id, never null; an untagged entry has [].
    tag_ids: list[UUID]
    description: str
    billable: bool
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
            tag_ids=entry.tag_ids,
            description=entry.description,
            billable=entry.billable,
            started_at=entry.started_at,
            stopped_at=entry.stopped_at,
            duration_seconds=duration,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )


class TimeEntryPageResponse(BaseModel):
    items: list[TimeEntryResponse]
    # True when another page exists. There is no total on purpose — see
    # `ListTimeEntries`.
    has_more: bool
    limit: int
    offset: int

    @classmethod
    def of(cls, page: TimeEntryPage) -> "TimeEntryPageResponse":
        return cls(
            items=[TimeEntryResponse.of(entry) for entry in page.items],
            has_more=page.has_more,
            limit=page.limit,
            offset=page.offset,
        )


class TimeEntrySuggestionResponse(BaseModel):
    description: str
    project_id: UUID | None
    last_used_at: datetime

    @classmethod
    def of(cls, suggestion: TimeEntrySuggestion) -> "TimeEntrySuggestionResponse":
        return cls(
            description=suggestion.description,
            project_id=suggestion.project_id,
            last_used_at=suggestion.last_used_at,
        )


class StartTimerRequest(BaseModel):
    project_id: UUID | None = None
    tag_ids: list[UUID] = Field(default_factory=list)
    description: str = Field(default="", max_length=DESCRIPTION_MAX_LENGTH)
    # Omitted: the project's default, or false without a project.
    billable: bool | None = None
    # Defaults to the server's "now" when omitted.
    started_at: AwareDatetime | None = None


class StopTimerRequest(BaseModel):
    stopped_at: AwareDatetime | None = None


class CreateTimeEntryRequest(BaseModel):
    project_id: UUID | None = None
    tag_ids: list[UUID] = Field(default_factory=list)
    description: str = Field(default="", max_length=DESCRIPTION_MAX_LENGTH)
    # Omitted: the project's default, or false without a project.
    billable: bool | None = None
    started_at: AwareDatetime
    stopped_at: AwareDatetime


class UpdateTimeEntryRequest(BaseModel):
    """Omitted fields are left untouched; `project_id: null` clears the project,
    `tag_ids: []` clears the tags (`tag_ids: null` is rejected). A new project
    brings its billable default unless `billable` is sent too."""

    model_config = ConfigDict(extra="forbid")

    project_id: UUID | None = None
    tag_ids: list[UUID] | None = None
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    billable: bool | None = None
    started_at: AwareDatetime | None = None
    stopped_at: AwareDatetime | None = None
