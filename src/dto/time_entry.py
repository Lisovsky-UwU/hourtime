import uuid
from datetime import date, time

from pydantic import BaseModel, model_validator

from src.exceptions.defined import TIME_ENTRY_TIMES_ERROR
from src.models.helpers import TimeNoMicroseconds


class CreateTimeEntryPayload(BaseModel):
    user_id: int
    comment: str | None
    workspace_id: int
    project_id: int | None
    task_id: uuid.UUID | None
    start_date: date
    start_time: time
    end_date: date | None
    end_time: time | None

    @model_validator(mode="after")
    def validate_times_and_date(self) -> "CreateTimeEntryPayload":
        if self.end_date is not None and self.end_time is not None and \
            (self.end_date > self.start_date or self.end_time > self.start_time):
            raise TIME_ENTRY_TIMES_ERROR
        return self


class UpdateTimeEntryPayload(BaseModel):
    time_entry_id: uuid.UUID
    comment: str | None
    project_id: int | None
    task_id: uuid.UUID | None
    start_date: date | None
    start_time: time | None
    end_date: date | None
    end_time: time | None


class TimeEntryForUser(BaseModel):
    id: uuid.UUID
    comment: str | None
    workspace_id: int
    project_id: int | None
    task_id: uuid.UUID | None
    start_date: date
    start_time: TimeNoMicroseconds
    end_date: date | None
    end_time: TimeNoMicroseconds | None

