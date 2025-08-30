import uuid

from pydantic import BaseModel


class TaskModel(BaseModel):
    id: uuid.UUID
    number: int
    name: str
    description: str | None
    project_id: int

