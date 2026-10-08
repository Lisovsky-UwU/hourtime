from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from hourtime.domain.entities import Client
from hourtime.domain.entities.client import NAME_MAX_LENGTH


class ClientResponse(BaseModel):
    id: UUID
    name: str
    archived: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, client: Client) -> "ClientResponse":
        return cls(
            id=client.id,
            name=client.name,
            archived=client.is_archived,
            created_at=client.created_at,
            updated_at=client.updated_at,
        )


class CreateClientRequest(BaseModel):
    name: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)


class UpdateClientRequest(BaseModel):
    """Omitted fields are left untouched."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=NAME_MAX_LENGTH)
    archived: bool | None = None
