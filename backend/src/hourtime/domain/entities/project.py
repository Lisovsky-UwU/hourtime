import re
from uuid import UUID

from pydantic import Field, field_validator

from hourtime.domain.billing import HourlyRate
from hourtime.domain.entities.base import Entity, UtcDatetime

NAME_MAX_LENGTH = 100

_HEX_LONG = re.compile(r"^#[0-9a-fA-F]{6}$")
_HEX_SHORT = re.compile(r"^#[0-9a-fA-F]{3}$")

DEFAULT_COLOR = "#4285f4"


def normalise_color(value: str) -> str:
    """Accept `#rgb` / `#RRGGBB` (with or without `#`) and fold to `#rrggbb`."""
    candidate = value.strip()
    if not candidate.startswith("#"):
        candidate = f"#{candidate}"
    if _HEX_SHORT.match(candidate):
        r, g, b = candidate[1], candidate[2], candidate[3]
        candidate = f"#{r}{r}{g}{g}{b}{b}"
    if not _HEX_LONG.match(candidate):
        raise ValueError("must be a hex color such as #4285f4")
    return candidate.lower()


class Project(Entity):
    id: UUID
    workspace_id: UUID
    client_id: UUID | None = None
    name: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)
    color: str = DEFAULT_COLOR
    # What new entries on this project start as; each entry can still be switched.
    billable: bool = False
    # None falls back to the workspace's default rate.
    hourly_rate: HourlyRate | None = None
    archived_at: UtcDatetime | None = None
    created_at: UtcDatetime
    updated_at: UtcDatetime

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("color", mode="before")
    @classmethod
    def _normalise_color(cls, value: object) -> object:
        return normalise_color(value) if isinstance(value, str) else value

    @property
    def is_archived(self) -> bool:
        return self.archived_at is not None
