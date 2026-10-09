from collections import defaultdict

from hourtime.domain.errors import ValidationError
from hourtime.domain.reports import GroupKey, Totals
from hourtime.interfaces.repositories import ReportRepository, WorkspaceRepository
from hourtime.use_cases.dto import ReportDay, SummaryGroup, SummaryReport, SummaryReportInput
from hourtime.use_cases.reports.rules import (
    longest_first,
    period_days,
    report_criteria,
    workspace_currency,
)


def _sorted(groups: list[SummaryGroup]) -> list[SummaryGroup]:
    return sorted(groups, key=lambda group: longest_first(group.key, group.totals))


class GetSummaryReport:
    """Totals of a period, split by day for the chart and by up to two groupings.

    Groups and subgroups come from two separate aggregates rather than one: a
    group's own figures must count each entry once, even when its subgroups are
    tags and an entry sits under two of them.
    """

    def __init__(self, reports: ReportRepository, workspaces: WorkspaceRepository) -> None:
        self._reports = reports
        self._workspaces = workspaces

    async def execute(self, data: SummaryReportInput) -> SummaryReport:
        if data.subgroup_by is not None and data.subgroup_by == data.group_by:
            raise ValidationError("subgroup_by must differ from group_by")
        criteria = report_criteria(data.filters)
        currency = await workspace_currency(self._workspaces, criteria.workspace_id)

        totals = await self._reports.totals(criteria)

        by_day = None
        days = period_days(data.filters)
        if days is not None:
            found = {row.day: row.totals() for row in await self._reports.totals_by_day(criteria)}
            by_day = [ReportDay(day=day, totals=found.get(day, Totals())) for day in days]

        children: dict[GroupKey, list[SummaryGroup]] = defaultdict(list)
        if data.subgroup_by is not None:
            pairs = await self._reports.totals_by_group(criteria, data.group_by, data.subgroup_by)
            for pair in pairs:
                if pair.subgroup is not None:
                    children[pair.group].append(
                        SummaryGroup(key=pair.subgroup, totals=pair.totals())
                    )

        groups = [
            SummaryGroup(key=row.group, totals=row.totals(), subgroups=_sorted(children[row.group]))
            for row in await self._reports.totals_by_group(criteria, data.group_by)
        ]
        return SummaryReport(
            currency=currency, totals=totals, by_day=by_day, groups=_sorted(groups)
        )
