from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from hourtime.domain.entities import Project
from hourtime.domain.entities.project import NAME_MAX_LENGTH


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    color: str
    client_id: UUID | None
    archived: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, project: Project) -> "ProjectResponse":
        return cls(
            id=project.id,
            name=project.name,
            color=project.color,
            client_id=project.client_id,
            archived=project.is_archived,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )


class CreateProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)
    color: str | None = None
    client_id: UUID | None = None


class UpdateProjectRequest(BaseModel):
    """Omitted fields are left untouched; `client_id: null` detaches the client."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=NAME_MAX_LENGTH)
    color: str | None = None
    archived: bool | None = None
    client_id: UUID | None = None
