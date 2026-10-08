from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from hourtime.domain.billing import HourlyRate
from hourtime.domain.entities import Workspace


class WorkspaceResponse(BaseModel):
    id: UUID
    name: str
    # A decimal string such as "150.00", or null when no default rate is set.
    default_hourly_rate: Decimal | None
    currency: str

    @classmethod
    def of(cls, workspace: Workspace) -> "WorkspaceResponse":
        return cls(
            id=workspace.id,
            name=workspace.name,
            default_hourly_rate=workspace.default_hourly_rate,
            currency=workspace.currency,
        )


class UpdateWorkspaceRequest(BaseModel):
    """Omitted fields are left untouched; `default_hourly_rate: null` removes the rate."""

    model_config = ConfigDict(extra="forbid")

    default_hourly_rate: HourlyRate | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
