from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from hourtime.domain.entities import Task
from hourtime.domain.entities.task import NAME_MAX_LENGTH


class TaskResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    estimated_seconds: int | None
    completed: bool
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, task: Task) -> "TaskResponse":
        return cls(
            id=task.id,
            project_id=task.project_id,
            name=task.name,
            estimated_seconds=task.estimated_seconds,
            completed=task.is_completed,
            completed_at=task.completed_at,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )


class CreateTaskRequest(BaseModel):
    project_id: UUID
    name: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)
    estimated_seconds: int | None = Field(default=None, gt=0)


class UpdateTaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=NAME_MAX_LENGTH)
    estimated_seconds: int | None = Field(default=None, gt=0)
    completed: bool | None = None
