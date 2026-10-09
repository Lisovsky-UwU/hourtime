from hourtime.domain.errors import ValidationError
from hourtime.interfaces.repositories import ReportRepository, WorkspaceRepository
from hourtime.use_cases.dto import DetailedReport, DetailedReportInput
from hourtime.use_cases.reports.rules import report_criteria, workspace_currency

MAX_LIMIT = 200


class GetDetailedReport:
    """A page of entries plus totals over everything the filters let through.

    Unlike the time entry list this one does count: the totals query has to run
    anyway, and its entry count is what the frontend pages by.
    """

    def __init__(self, reports: ReportRepository, workspaces: WorkspaceRepository) -> None:
        self._reports = reports
        self._workspaces = workspaces

    async def execute(self, data: DetailedReportInput) -> DetailedReport:
        if data.limit < 1 or data.limit > MAX_LIMIT:
            raise ValidationError(f"limit must be between 1 and {MAX_LIMIT}")
        if data.offset < 0:
            raise ValidationError("offset cannot be negative")
        criteria = report_criteria(data.filters)
        currency = await workspace_currency(self._workspaces, criteria.workspace_id)

        totals = await self._reports.totals(criteria)
        found = await self._reports.list_entries(
            criteria, sort=data.sort, order=data.order, limit=data.limit + 1, offset=data.offset
        )
        return DetailedReport(
            currency=currency,
            totals=totals,
            items=found[: data.limit],
            has_more=len(found) > data.limit,
            limit=data.limit,
            offset=data.offset,
        )
