import uuid
from datetime import date, time

from pydantic import BaseModel, Field

from src.models.helpers import (
    DATE_EXAMPLES,
    DATE_FORMAT_DESC,
    TIME_EXAMPLES,
    TIME_FORMAT_DESC,
    get_current_date,
    get_current_time,
)


class TimeEntryStartRequest(BaseModel):
    workspace_id: int
    comment: str | None = None
    project_id: int | None = None
    task_id: uuid.UUID | None = None
    start_date: date | None = Field(
        default_factory=get_current_date,
        description=DATE_FORMAT_DESC,
        examples=DATE_EXAMPLES,
    )
    start_time: time | None = Field(
        default_factory=get_current_time,
        description=TIME_FORMAT_DESC,
        examples=TIME_EXAMPLES,
    )


class TimeENtryCreateRequest(BaseModel):
    workspace_id: int
    comment: str | None = None
    project_id: int | None = None
    task_id: uuid.UUID | None = None
    start_date: date = Field(description=DATE_FORMAT_DESC, examples=DATE_EXAMPLES)
    start_time: time = Field(description=TIME_FORMAT_DESC, examples=TIME_EXAMPLES)
    end_date: date = Field(description=DATE_FORMAT_DESC, examples=DATE_EXAMPLES)
    end_time: time = Field(description=TIME_FORMAT_DESC, examples=TIME_EXAMPLES)



class TimeEntryUpdateRequest(BaseModel):
    time_entry_id: uuid.UUID
    comment: str | None = None
    project_id: int | None = None
    task_id: uuid.UUID | None = None
    start_date: date | None = Field(
        default=None,
        description=DATE_FORMAT_DESC,
        examples=DATE_EXAMPLES,
    )
    start_time: time | None = Field(
        default=None,
        description=TIME_FORMAT_DESC,
        examples=TIME_EXAMPLES,
    )
    end_date: date | None = Field(
        default=None,
        description=DATE_FORMAT_DESC,
        examples=DATE_EXAMPLES,
    )
    end_time: time | None = Field(
        default=None,
        description=TIME_FORMAT_DESC,
        examples=TIME_EXAMPLES,
    )

