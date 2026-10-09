"""What every report does the same way: reading the filters and the workspace."""

from datetime import date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from hourtime.domain.errors import NotFound, ValidationError
from hourtime.domain.reports import GroupKey, ReportCriteria, Totals
from hourtime.interfaces.repositories import WorkspaceRepository
from hourtime.use_cases.dto import ReportFiltersInput

DEFAULT_TIMEZONE = "UTC"


def _zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValidationError(f"Unknown time zone {name!r}") from exc


def _local_midnight(day: date, zone: ZoneInfo) -> datetime:
    # On the rare day whose midnight is skipped by a DST jump, fold=0 lands on
    # the instant of the jump, which is exactly where that local day begins.
    return datetime.combine(day, time.min, tzinfo=zone)


def report_criteria(filters: ReportFiltersInput) -> ReportCriteria:
    """Check the filters and turn local dates into the UTC instants they span."""
    if (filters.start_date is None) != (filters.end_date is None):
        raise ValidationError("start_date and end_date go together")
    timezone = filters.timezone or DEFAULT_TIMEZONE
    zone = _zone(timezone)

    started_from = started_before = None
    if filters.start_date is not None and filters.end_date is not None:
        if filters.start_date > filters.end_date:
            raise ValidationError("start_date must not be later than end_date")
        started_from = _local_midnight(filters.start_date, zone)
        started_before = _local_midnight(filters.end_date + timedelta(days=1), zone)

    return ReportCriteria(
        user_id=filters.user_id,
        workspace_id=filters.workspace_id,
        timezone=timezone,
        started_from=started_from,
        started_before=started_before,
        project_ids=filters.project_ids,
        without_project=filters.without_project,
        client_ids=filters.client_ids,
        without_client=filters.without_client,
        tag_ids=filters.tag_ids,
        without_tags=filters.without_tags,
        billable=filters.billable,
        description=filters.description,
    )


def period_days(filters: ReportFiltersInput) -> list[date] | None:
    """Every day from start to end inclusive; None for an open-ended report."""
    if filters.start_date is None or filters.end_date is None:
        return None
    count = (filters.end_date - filters.start_date).days + 1
    return [filters.start_date + timedelta(days=offset) for offset in range(count)]


async def workspace_currency(workspaces: WorkspaceRepository, workspace_id: UUID) -> str:
    workspace = await workspaces.get_by_id(workspace_id)
    if workspace is None:
        raise NotFound("Workspace not found")
    return workspace.currency


def longest_first(key: GroupKey, totals: Totals) -> tuple[object, ...]:
    """Sort key for groups: longest first, then by name with the unnamed group last.

    The id only breaks ties between namesakes, such as an archived project and
    a live one, so the order never depends on how Postgres returned the rows.
    """
    name = key.name or ""
    return (-totals.duration, key.name is None, name.casefold(), name, str(key.id or ""))
