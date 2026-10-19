from uuid import UUID

from pydantic import Field, field_validator

from hourtime.domain.billing import DEFAULT_CURRENCY, HourlyRate, normalise_currency
from hourtime.domain.entities.base import Entity, UtcDatetime

NAME_MAX_LENGTH = 100


def personal_workspace_name(email: str) -> str:
    """Every account gets a workspace at registration, named after its owner so
    that members of several personal workspaces can tell them apart."""
    return email[:NAME_MAX_LENGTH]


class Workspace(Entity):
    """Owns projects and time entries; for now each user has exactly one."""

    id: UUID
    name: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)
    owner_id: UUID
    # Applies to billable entries whose project has no rate of its own.
    default_hourly_rate: HourlyRate | None = None
    # One currency for every rate and amount in the workspace.
    currency: str = DEFAULT_CURRENCY
    created_at: UtcDatetime
    updated_at: UtcDatetime

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("currency", mode="before")
    @classmethod
    def _normalise_currency(cls, value: object) -> object:
        return normalise_currency(value) if isinstance(value, str) else value
