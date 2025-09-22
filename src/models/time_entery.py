import uuid
from datetime import date

from pydantic import BaseModel

from src.models.helpers import TimeNoMicroseconds


class TimeEntryModel(BaseModel):
    id: uuid.UUID
    user_id: int
    comment: str | None
    workspace_id: int
    project_id: int | None
    task_id: uuid.UUID | None
    start_date: date
    start_time: TimeNoMicroseconds
    end_date: date | None
    end_time: TimeNoMicroseconds | None

