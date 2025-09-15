import uuid

from pydantic import BaseModel


class CreateTaskRequest(BaseModel):
    name: str
    description: str | None = None
    workspace_id: int
    project_id: int | None = None


class UpdateTaskRequest(BaseModel):
    task_id: uuid.UUID
    name: str
    description: str | None = None

