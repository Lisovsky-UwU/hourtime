from hourtime.domain.errors import ValidationError
from hourtime.domain.reports import GroupKey, Totals
from hourtime.interfaces.repositories import ReportRepository, WorkspaceRepository
from hourtime.use_cases.dto import WeeklyReport, WeeklyReportInput, WeeklyRow
from hourtime.use_cases.reports.rules import (
    longest_first,
    period_days,
    report_criteria,
    workspace_currency,
)

MAX_DAYS = 7


class GetWeeklyReport:
    """Projects or clients against the days of one week.

    The frontend picks the week, aligned to the user's `week_start`; any range
    of up to seven days is accepted.

    Every entry has one project (or none) and one start day, so rows and days
    split the entries without overlap and simply add up to the totals.
    """

    def __init__(self, reports: ReportRepository, workspaces: WorkspaceRepository) -> None:
        self._reports = reports
        self._workspaces = workspaces

    async def execute(self, data: WeeklyReportInput) -> WeeklyReport:
        if data.filters.start_date is None and data.filters.end_date is None:
            raise ValidationError("start_date and end_date are required")
        criteria = report_criteria(data.filters)
        days = period_days(data.filters) or []
        if len(days) > MAX_DAYS:
            raise ValidationError(f"The period cannot be longer than {MAX_DAYS} days")
        currency = await workspace_currency(self._workspaces, criteria.workspace_id)

        column = {day: index for index, day in enumerate(days)}
        row_totals: dict[GroupKey, Totals] = {}
        row_days: dict[GroupKey, list[int]] = {}
        for cell in await self._reports.totals_by_group_and_day(criteria, data.group_by):
            row_totals[cell.group] = row_totals.get(cell.group, Totals()).plus(cell.totals())
            cells = row_days.setdefault(cell.group, [0] * len(days))
            # Python's tzdata and Postgres' may disagree on a zone that just
            # changed its rules; a day outside the week still counts in the row.
            if cell.day in column:
                cells[column[cell.day]] += cell.duration

        rows = sorted(
            (
                WeeklyRow(key=key, totals=totals, days=row_days[key])
                for key, totals in row_totals.items()
            ),
            key=lambda row: longest_first(row.key, row.totals),
        )
        totals = Totals()
        for row in rows:
            totals = totals.plus(row.totals)
        day_totals = [sum(row.days[index] for row in rows) for index in range(len(days))]
        return WeeklyReport(
            currency=currency, days=days, totals=totals, day_totals=day_totals, rows=rows
        )
