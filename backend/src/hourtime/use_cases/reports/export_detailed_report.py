from collections.abc import AsyncIterator

from hourtime.domain.reports import ReportCriteria, ReportEntry
from hourtime.interfaces.repositories import ReportRepository, WorkspaceRepository
from hourtime.use_cases.dto import DetailedExport, DetailedExportInput
from hourtime.use_cases.reports.rules import report_criteria, workspace_currency

PAGE_SIZE = 1000


class ExportDetailedReport:
    """Every entry the filters let through, for a file rather than a screen.

    The filters are checked up front, so a bad request fails before the first
    byte is sent; the entries are then read in pages as the file is written.
    """

    def __init__(self, reports: ReportRepository, workspaces: WorkspaceRepository) -> None:
        self._reports = reports
        self._workspaces = workspaces

    async def execute(self, data: DetailedExportInput) -> DetailedExport:
        criteria = report_criteria(data.filters)
        currency = await workspace_currency(self._workspaces, criteria.workspace_id)
        return DetailedExport(
            currency=currency,
            timezone=criteria.timezone,
            pages=self._pages(criteria, data),
        )

    async def _pages(
        self, criteria: ReportCriteria, data: DetailedExportInput
    ) -> AsyncIterator[list[ReportEntry]]:
        # shortcut: offset paging, so an entry added or deleted mid-export can
        # shift a row between pages; move to keyset paging if exports get big.
        offset = 0
        while True:
            page = await self._reports.list_entries(
                criteria, sort=data.sort, order=data.order, limit=PAGE_SIZE, offset=offset
            )
            if page:
                yield page
            if len(page) < PAGE_SIZE:
                return
            offset += PAGE_SIZE
