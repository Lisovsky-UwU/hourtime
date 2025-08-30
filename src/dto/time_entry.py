import uuid
from datetime import date, time

from pydantic import BaseModel


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


class UpdateTimeEntryPayload(BaseModel):
    time_entry_id: uuid.UUID
    comment: str | None
    project_id: int | None
    task_id: uuid.UUID | None
    start_date: date
    start_time: time
    end_date: date | None
    end_time: time | None

