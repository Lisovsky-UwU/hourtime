"""Read models for reports: which entries a report covers and what it adds up.

Nothing here is stored. Every figure is worked out from the entries and the
current rates when a report is asked for, the same way `billing` prices a
single entry.
"""

from datetime import date
from decimal import Decimal
from typing import Literal, Self
from uuid import UUID

from pydantic import Field

from hourtime.domain.billing import CENT
from hourtime.domain.entities.base import Entity, UtcDatetime

# What a summary can be grouped by; weekly rows only by the first two.
ReportGrouping = Literal["project", "client", "tag", "description"]
WeeklyGrouping = Literal["project", "client"]

DetailedSort = Literal["started_at", "duration", "description", "project"]
SortOrder = Literal["asc", "desc"]

ZERO_AMOUNT = Decimal("0.00")


class ReportCriteria(Entity):
    """Which finished entries of one user in one workspace a report covers.

    Each id list goes with a `without_*` flag and the two are alternatives: an
    entry passes when it matches the list OR the flag. Leaving both empty
    switches that filter off.
    """

    user_id: UUID
    workspace_id: UUID
    # IANA name; a day is cut at midnight in this zone.
    timezone: str
    started_from: UtcDatetime | None = None
    # Exclusive, so a whole local day is `[midnight, next midnight)`.
    started_before: UtcDatetime | None = None
    project_ids: list[UUID] = Field(default_factory=list)
    without_project: bool = False
    # "Without a client" also covers entries without a project.
    client_ids: list[UUID] = Field(default_factory=list)
    without_client: bool = False
    tag_ids: list[UUID] = Field(default_factory=list)
    without_tags: bool = False
    billable: bool | None = None
    # Case-insensitive substring; "" matches everything.
    description: str = ""


class Totals(Entity):
    """Durations in whole seconds; `amount` is the sum of per-entry amounts, each
    already rounded to the cent, so it always matches the entries it covers."""

    duration: int = 0
    billable_duration: int = 0
    amount: Decimal = ZERO_AMOUNT
    entries: int = 0

    def plus(self, other: "Totals") -> Self:
        return self.evolve(
            duration=self.duration + other.duration,
            billable_duration=self.billable_duration + other.billable_duration,
            amount=(self.amount + other.amount).quantize(CENT),
            entries=self.entries + other.entries,
        )

    def totals(self) -> "Totals":
        """Just the figures, without whatever the subclass groups them by."""
        return Totals(
            duration=self.duration,
            billable_duration=self.billable_duration,
            amount=self.amount,
            entries=self.entries,
        )


class GroupKey(Entity):
    """One group of a report and what it is shown as.

    `id` is null for the "no project / no client / no tags" group and for
    every description group, which are told apart by `name` instead.
    """

    id: UUID | None = None
    name: str | None = None
    color: str | None = None
    client_name: str | None = None


class GroupTotals(Totals):
    group: GroupKey
    # Set only when the totals were split by a second grouping.
    subgroup: GroupKey | None = None


class DayTotals(Totals):
    day: date


class GroupDayTotals(Totals):
    group: GroupKey
    day: date


class ProjectRef(Entity):
    id: UUID
    name: str
    color: str


class ClientRef(Entity):
    id: UUID
    name: str


class TagRef(Entity):
    id: UUID
    name: str


class ReportEntry(Entity):
    """One finished entry as the detailed report lists it."""

    id: UUID
    description: str
    project: ProjectRef | None = None
    client: ClientRef | None = None
    # Ordered by name.
    tags: list[TagRef] = Field(default_factory=list)
    billable: bool
    started_at: UtcDatetime
    stopped_at: UtcDatetime
    duration: int
    # None unless the entry is billable and some rate applies to it.
    amount: Decimal | None = None
