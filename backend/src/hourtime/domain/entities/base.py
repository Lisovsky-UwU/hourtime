"""Shared plumbing for domain entities.

Entities are pydantic models on purpose: the invariants live next to the fields
and are enforced on every construction. Pydantic's own error type never leaves
the domain — it is translated into `domain.errors.ValidationError` so upper
layers only ever deal with domain vocabulary.
"""

from datetime import UTC, datetime
from typing import Annotated, Any, Self

from pydantic import AfterValidator, BaseModel, ConfigDict
from pydantic import ValidationError as PydanticValidationError

from hourtime.domain.errors import ValidationError


def _require_utc(value: datetime) -> datetime:
    """Reject naive datetimes and normalise everything else to UTC."""
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return value.astimezone(UTC)


UtcDatetime = Annotated[datetime, AfterValidator(_require_utc)]


def _describe(exc: PydanticValidationError) -> str:
    parts = []
    for error in exc.errors():
        location = ".".join(str(item) for item in error["loc"]) or "value"
        parts.append(f"{location}: {error['msg']}")
    return "; ".join(parts)


class Entity(BaseModel):
    """Immutable, self-validating domain object."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    def __init__(self, **data: Any) -> None:
        try:
            super().__init__(**data)
        except PydanticValidationError as exc:
            raise ValidationError(_describe(exc)) from exc

    @classmethod
    def model_validate(cls, obj: Any, **kwargs: Any) -> Self:
        try:
            return super().model_validate(obj, **kwargs)
        except PydanticValidationError as exc:
            raise ValidationError(_describe(exc)) from exc

    def evolve(self, **changes: Any) -> Self:
        """Return a copy with `changes` applied, re-checking every invariant.

        `model_copy(update=...)` skips validation, which would let callers build
        entities that violate their own rules — always go through this instead.
        """
        return self.model_validate({**self.model_dump(), **changes})
