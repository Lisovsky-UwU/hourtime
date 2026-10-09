from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from hourtime.domain.entities.time_entry import DESCRIPTION_MAX_LENGTH
from hourtime.domain.reports import DetailedSort, ReportGrouping, SortOrder, WeeklyGrouping
from hourtime.presentation.api.csv_export import csv_response, detailed_csv, summary_csv
from hourtime.presentation.api.deps import (
    CurrentUserDep,
    get_export_detailed_report,
    get_get_detailed_report,
    get_get_summary_report,
    get_get_weekly_report,
)
from hourtime.presentation.api.schemas.reports import (
    DetailedReportResponse,
    SummaryReportResponse,
    WeeklyReportResponse,
)
from hourtime.use_cases.dto import (
    DetailedExportInput,
    DetailedReportInput,
    ReportFiltersInput,
    SummaryReportInput,
    WeeklyReportInput,
)
from hourtime.use_cases.reports import (
    ExportDetailedReport,
    GetDetailedReport,
    GetSummaryReport,
    GetWeeklyReport,
)

router = APIRouter(prefix="/reports", tags=["reports"])


def report_filters(
    current: CurrentUserDep,
    # Local dates in the user's time zone, both inclusive; give both or neither.
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
    # Each list is repeated in the query string (`?project_ids=a&project_ids=b`)
    # and goes with a `without_*` flag: an entry passes when it matches either.
    project_ids: Annotated[list[UUID] | None, Query()] = None,
    without_project: Annotated[bool, Query()] = False,
    client_ids: Annotated[list[UUID] | None, Query()] = None,
    without_client: Annotated[bool, Query()] = False,
    tag_ids: Annotated[list[UUID] | None, Query()] = None,
    without_tags: Annotated[bool, Query()] = False,
    billable: Annotated[bool | None, Query()] = None,
    description: Annotated[str, Query(max_length=DESCRIPTION_MAX_LENGTH)] = "",
) -> ReportFiltersInput:
    return ReportFiltersInput(
        user_id=current.user.id,
        workspace_id=current.workspace_id,
        timezone=current.user.timezone,
        start_date=start_date,
        end_date=end_date,
        project_ids=project_ids or [],
        without_project=without_project,
        client_ids=client_ids or [],
        without_client=without_client,
        tag_ids=tag_ids or [],
        without_tags=without_tags,
        billable=billable,
        description=description,
    )


FiltersDep = Annotated[ReportFiltersInput, Depends(report_filters)]


@router.get("/summary", response_model=SummaryReportResponse)
async def summary_report(
    filters: FiltersDep,
    use_case: Annotated[GetSummaryReport, Depends(get_get_summary_report)],
    group_by: Annotated[ReportGrouping, Query()] = "project",
    subgroup_by: Annotated[ReportGrouping | None, Query()] = None,
) -> SummaryReportResponse:
    report = await use_case.execute(
        SummaryReportInput(filters=filters, group_by=group_by, subgroup_by=subgroup_by)
    )
    return SummaryReportResponse.of(report)


@router.get("/detailed", response_model=DetailedReportResponse)
async def detailed_report(
    filters: FiltersDep,
    use_case: Annotated[GetDetailedReport, Depends(get_get_detailed_report)],
    sort: Annotated[DetailedSort, Query()] = "started_at",
    order: Annotated[SortOrder, Query()] = "desc",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DetailedReportResponse:
    report = await use_case.execute(
        DetailedReportInput(filters=filters, sort=sort, order=order, limit=limit, offset=offset)
    )
    return DetailedReportResponse.of(report)


@router.get("/summary.csv", response_class=StreamingResponse)
async def summary_report_csv(
    filters: FiltersDep,
    use_case: Annotated[GetSummaryReport, Depends(get_get_summary_report)],
    group_by: Annotated[ReportGrouping, Query()] = "project",
    subgroup_by: Annotated[ReportGrouping | None, Query()] = None,
) -> StreamingResponse:
    report = await use_case.execute(
        SummaryReportInput(filters=filters, group_by=group_by, subgroup_by=subgroup_by)
    )
    content = summary_csv(report, group_by, subgroup_by)
    return csv_response(content, "summary", filters.start_date, filters.end_date)


@router.get("/detailed.csv", response_class=StreamingResponse)
async def detailed_report_csv(
    filters: FiltersDep,
    use_case: Annotated[ExportDetailedReport, Depends(get_export_detailed_report)],
    sort: Annotated[DetailedSort, Query()] = "started_at",
    order: Annotated[SortOrder, Query()] = "desc",
) -> StreamingResponse:
    # The session behind the use case stays open while the response streams:
    # FastAPI closes request-scoped dependencies only after the body is sent.
    export = await use_case.execute(DetailedExportInput(filters=filters, sort=sort, order=order))
    return csv_response(detailed_csv(export), "detailed", filters.start_date, filters.end_date)


@router.get("/weekly", response_model=WeeklyReportResponse)
async def weekly_report(
    filters: FiltersDep,
    use_case: Annotated[GetWeeklyReport, Depends(get_get_weekly_report)],
    group_by: Annotated[WeeklyGrouping, Query()] = "project",
) -> WeeklyReportResponse:
    report = await use_case.execute(WeeklyReportInput(filters=filters, group_by=group_by))
    return WeeklyReportResponse.of(report)
