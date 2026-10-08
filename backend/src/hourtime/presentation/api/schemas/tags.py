from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from hourtime.domain.entities import Tag
from hourtime.domain.entities.tag import NAME_MAX_LENGTH


class TagResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, tag: Tag) -> "TagResponse":
        return cls(id=tag.id, name=tag.name, created_at=tag.created_at, updated_at=tag.updated_at)


class CreateTagRequest(BaseModel):
    name: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)


class UpdateTagRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)
