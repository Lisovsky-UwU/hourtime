from decimal import Decimal
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from hourtime.domain.billing import CENT, SECONDS_PER_HOUR
from hourtime.domain.reports import (
    ClientRef,
    DayTotals,
    DetailedSort,
    GroupDayTotals,
    GroupKey,
    GroupTotals,
    ProjectRef,
    ReportCriteria,
    ReportEntry,
    ReportGrouping,
    SortOrder,
    TagRef,
    Totals,
    WeeklyGrouping,
)
from hourtime.infrastructure.db.models import (
    ClientModel,
    ProjectModel,
    TagModel,
    TimeEntryModel,
    TimeEntryTagModel,
    WorkspaceModel,
)
from hourtime.infrastructure.db.repositories.time_entry_repository import escape_like
from hourtime.interfaces.repositories import ReportRepository

KEY_FIELDS = ("id", "name", "color", "client_name")


def _matching_any(*options: tuple[bool, ColumnElement[bool]]) -> ColumnElement[bool] | None:
    """OR of the options that are switched on, or None when none is."""
    chosen = [condition for enabled, condition in options if enabled]
    return sa.or_(*chosen) if chosen else None


def _filters(criteria: ReportCriteria) -> list[ColumnElement[bool]]:
    entry = TimeEntryModel
    conditions: list[ColumnElement[bool]] = [
        entry.user_id == criteria.user_id,
        entry.workspace_id == criteria.workspace_id,
        entry.stopped_at.is_not(None),
    ]
    if criteria.started_from is not None:
        conditions.append(entry.started_at >= criteria.started_from)
    if criteria.started_before is not None:
        conditions.append(entry.started_at < criteria.started_before)

    has_tags = sa.exists().where(TimeEntryTagModel.time_entry_id == entry.id)
    # EXISTS rather than a join: an entry with two matching tags stays one row.
    has_wanted_tag = has_tags.where(TimeEntryTagModel.tag_id.in_(criteria.tag_ids))
    alternatives = (
        _matching_any(
            (bool(criteria.project_ids), entry.project_id.in_(criteria.project_ids)),
            (criteria.without_project, entry.project_id.is_(None)),
        ),
        _matching_any(
            (bool(criteria.client_ids), ProjectModel.client_id.in_(criteria.client_ids)),
            # Outer-joined, so this is also null for an entry without a project.
            (criteria.without_client, ProjectModel.client_id.is_(None)),
        ),
        _matching_any(
            (bool(criteria.tag_ids), has_wanted_tag),
            (criteria.without_tags, ~has_tags),
        ),
    )
    conditions.extend(condition for condition in alternatives if condition is not None)

    if criteria.billable is not None:
        conditions.append(entry.billable == criteria.billable)
    if criteria.description:
        conditions.append(
            entry.description.ilike(f"%{escape_like(criteria.description)}%", escape="\\")
        )
    return conditions


def _entries(criteria: ReportCriteria) -> sa.Subquery:
    """Every entry the report covers, one row each, with its duration, amount and day."""
    entry = TimeEntryModel
    # Whole seconds, truncated like `int(timedelta.total_seconds())` in `billing`.
    seconds = sa.cast(
        sa.func.floor(sa.extract("epoch", entry.stopped_at - entry.started_at)), sa.BigInteger
    )
    rate = sa.func.coalesce(ProjectModel.hourly_rate, WorkspaceModel.default_hourly_rate)
    # Same as `billing.billable_amount`: numeric `round` goes half away from zero,
    # which is half up for amounts that are never negative. Null without a rate.
    amount = sa.case(
        (entry.billable, sa.func.round(seconds * rate / SECONDS_PER_HOUR, 2)), else_=sa.null()
    )
    day = sa.cast(sa.func.timezone(criteria.timezone, entry.started_at), sa.Date)
    return (
        sa.select(
            entry.id,
            entry.description,
            entry.billable,
            entry.started_at,
            entry.stopped_at,
            entry.project_id,
            ProjectModel.name.label("project_name"),
            ProjectModel.color.label("project_color"),
            ClientModel.id.label("client_id"),
            ClientModel.name.label("client_name"),
            seconds.label("duration"),
            amount.label("amount"),
            day.label("day"),
        )
        .select_from(entry)
        .join(WorkspaceModel, WorkspaceModel.id == entry.workspace_id)
        .outerjoin(ProjectModel, ProjectModel.id == entry.project_id)
        .outerjoin(ClientModel, ClientModel.id == ProjectModel.client_id)
        .where(*_filters(criteria))
        .subquery("entries")
    )


def _entry_tags() -> sa.Subquery:
    return (
        sa.select(
            TimeEntryTagModel.time_entry_id,
            TagModel.id.label("tag_id"),
            TagModel.name.label("tag_name"),
        )
        .join(TagModel, TagModel.id == TimeEntryTagModel.tag_id)
        .subquery("entry_tags")
    )


def _key_columns(
    grouping: ReportGrouping, entries: sa.Subquery, tags: sa.Subquery
) -> dict[str, ColumnElement[Any] | None]:
    """What identifies a group and what it is shown as; None stays null in the report."""
    match grouping:
        case "project":
            return {
                "id": entries.c.project_id,
                "name": entries.c.project_name,
                "color": entries.c.project_color,
                "client_name": entries.c.client_name,
            }
        case "client":
            return {"id": entries.c.client_id, "name": entries.c.client_name}
        case "tag":
            return {"id": tags.c.tag_id, "name": tags.c.tag_name}
        case "description":
            # A literal, not a bound parameter: the expression appears in both
            # SELECT and GROUP BY, and two different parameters would not match.
            return {"name": sa.func.nullif(entries.c.description, sa.literal_column("''"))}


def _figures(entries: sa.Subquery) -> list[ColumnElement[Any]]:
    return [
        sa.func.coalesce(sa.func.sum(entries.c.duration), 0).label("duration"),
        sa.func.coalesce(sa.func.sum(entries.c.duration).filter(entries.c.billable), 0).label(
            "billable_duration"
        ),
        sa.func.coalesce(sa.func.sum(entries.c.amount), 0).label("amount"),
        sa.func.count().label("entries"),
    ]


def _grouped(
    criteria: ReportCriteria, groupings: dict[str, ReportGrouping], *, by_day: bool = False
) -> sa.Select[Any]:
    """Totals per combination of `groupings`, columns prefixed by the dict keys."""
    entries = _entries(criteria)
    tags = _entry_tags()
    source: sa.FromClause = entries
    if "tag" in groupings.values():
        # Outer: untagged entries form the "no tags" group.
        source = entries.outerjoin(tags, tags.c.time_entry_id == entries.c.id)

    columns: list[ColumnElement[Any]] = []
    group_by: list[ColumnElement[Any]] = []
    for prefix, grouping in groupings.items():
        found = _key_columns(grouping, entries, tags)
        for field in KEY_FIELDS:
            expression = found.get(field)
            if expression is None:
                columns.append(sa.null().label(f"{prefix}_{field}"))
            else:
                columns.append(expression.label(f"{prefix}_{field}"))
                group_by.append(expression)
    if by_day:
        columns.append(entries.c.day)
        group_by.append(entries.c.day)
    return sa.select(*columns, *_figures(entries)).select_from(source).group_by(*group_by)


def _figures_of(row: sa.Row[Any]) -> dict[str, Any]:
    return {
        "duration": int(row.duration),
        "billable_duration": int(row.billable_duration),
        "amount": Decimal(row.amount).quantize(CENT),
        "entries": int(row.entries),
    }


def _key_of(row: sa.Row[Any], prefix: str) -> GroupKey:
    mapping = row._mapping
    return GroupKey(**{field: mapping[f"{prefix}_{field}"] for field in KEY_FIELDS})


class SqlReportRepository(ReportRepository):
    """Everything is summed in Postgres; only finished rows come back to Python."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def totals(self, criteria: ReportCriteria) -> Totals:
        entries = _entries(criteria)
        row = (await self._session.execute(sa.select(*_figures(entries)))).one()
        return Totals(**_figures_of(row))

    async def totals_by_day(self, criteria: ReportCriteria) -> list[DayTotals]:
        entries = _entries(criteria)
        statement = (
            sa.select(entries.c.day, *_figures(entries))
            .group_by(entries.c.day)
            .order_by(entries.c.day)
        )
        rows = (await self._session.execute(statement)).all()
        return [DayTotals(day=row.day, **_figures_of(row)) for row in rows]

    async def totals_by_group(
        self,
        criteria: ReportCriteria,
        group_by: ReportGrouping,
        subgroup_by: ReportGrouping | None = None,
    ) -> list[GroupTotals]:
        groupings: dict[str, ReportGrouping] = {"group": group_by}
        if subgroup_by is not None:
            groupings["subgroup"] = subgroup_by
        rows = (await self._session.execute(_grouped(criteria, groupings))).all()
        return [
            GroupTotals(
                group=_key_of(row, "group"),
                subgroup=_key_of(row, "subgroup") if subgroup_by is not None else None,
                **_figures_of(row),
            )
            for row in rows
        ]

    async def totals_by_group_and_day(
        self, criteria: ReportCriteria, group_by: WeeklyGrouping
    ) -> list[GroupDayTotals]:
        statement = _grouped(criteria, {"group": group_by}, by_day=True)
        rows = (await self._session.execute(statement)).all()
        return [
            GroupDayTotals(group=_key_of(row, "group"), day=row.day, **_figures_of(row))
            for row in rows
        ]

    async def list_entries(
        self,
        criteria: ReportCriteria,
        *,
        sort: DetailedSort = "started_at",
        order: SortOrder = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[ReportEntry]:
        entries = _entries(criteria)
        sort_by = {
            "started_at": entries.c.started_at,
            "duration": entries.c.duration,
            "description": sa.func.lower(entries.c.description),
            "project": sa.func.lower(entries.c.project_name),
        }[sort]
        primary = sort_by.asc() if order == "asc" else sort_by.desc()
        statement = (
            sa.select(entries)
            .order_by(primary.nulls_last(), entries.c.started_at.desc(), entries.c.id.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(statement)).all()
        tags = await self._tags_of([row.id for row in rows])
        return [self._to_entry(row, tags[row.id]) for row in rows]

    async def _tags_of(self, entry_ids: list[UUID]) -> dict[UUID, list[TagRef]]:
        """Tags of a whole page in one query, by name."""
        found: dict[UUID, list[TagRef]] = {entry_id: [] for entry_id in entry_ids}
        if not entry_ids:
            return found
        statement = (
            sa.select(TimeEntryTagModel.time_entry_id, TagModel.id, TagModel.name)
            .join(TagModel, TagModel.id == TimeEntryTagModel.tag_id)
            .where(TimeEntryTagModel.time_entry_id.in_(entry_ids))
            .order_by(sa.func.lower(TagModel.name), TagModel.id)
        )
        for entry_id, tag_id, name in (await self._session.execute(statement)).all():
            found[entry_id].append(TagRef(id=tag_id, name=name))
        return found

    @staticmethod
    def _to_entry(row: sa.Row[Any], tags: list[TagRef]) -> ReportEntry:
        project = (
            ProjectRef(id=row.project_id, name=row.project_name, color=row.project_color)
            if row.project_id is not None
            else None
        )
        client = (
            ClientRef(id=row.client_id, name=row.client_name) if row.client_id is not None else None
        )
        return ReportEntry(
            id=row.id,
            description=row.description,
            project=project,
            client=client,
            tags=tags,
            billable=row.billable,
            started_at=row.started_at,
            stopped_at=row.stopped_at,
            duration=int(row.duration),
            amount=row.amount,
        )
