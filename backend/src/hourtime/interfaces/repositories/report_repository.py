from abc import ABC, abstractmethod

from hourtime.domain.reports import (
    DayTotals,
    DetailedSort,
    GroupDayTotals,
    GroupTotals,
    ReportCriteria,
    ReportEntry,
    ReportGrouping,
    SortOrder,
    Totals,
    WeeklyGrouping,
)


class ReportRepository(ABC):
    """Aggregates over finished entries; a running timer is never counted.

    The day of an entry is the local date of its start in `criteria.timezone`,
    so an entry that runs past midnight belongs wholly to the day it began.
    Amounts follow `domain.billing`: the project's rate, else the workspace
    default, applied to whole seconds and rounded half up per entry.
    """

    @abstractmethod
    async def totals(self, criteria: ReportCriteria) -> Totals: ...

    @abstractmethod
    async def totals_by_day(self, criteria: ReportCriteria) -> list[DayTotals]:
        """Only days that have entries, in date order."""

    @abstractmethod
    async def totals_by_group(
        self,
        criteria: ReportCriteria,
        group_by: ReportGrouping,
        subgroup_by: ReportGrouping | None = None,
    ) -> list[GroupTotals]:
        """One row per group, or per (group, subgroup) pair when `subgroup_by` is set.

        Grouping by tag counts an entry once under each of its tags, and once
        under the "no tags" group when it has none. Rows come in no particular
        order.
        """

    @abstractmethod
    async def totals_by_group_and_day(
        self, criteria: ReportCriteria, group_by: WeeklyGrouping
    ) -> list[GroupDayTotals]:
        """One row per (group, day) that has entries, in no particular order."""

    @abstractmethod
    async def list_entries(
        self,
        criteria: ReportCriteria,
        *,
        sort: DetailedSort = "started_at",
        order: SortOrder = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[ReportEntry]:
        """A page of entries. Ties are broken by `started_at` descending, then by
        id, so pages stay stable; entries without a project sort last by project."""
