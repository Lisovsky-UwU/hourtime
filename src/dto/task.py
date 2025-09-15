import uuid

from pydantic import BaseModel


class CreateTaskPayload(BaseModel):
    name: str
    description: str | None
    workspace_id: int
    project_id: int | None


class TaskInWorkspace(BaseModel):
    id: uuid.UUID
    number: int
    name: str
    description: str | None
    project_id: int | None


class UpdateTaskPayload(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None

