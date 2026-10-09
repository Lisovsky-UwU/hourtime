import datetime as dt
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from hourtime.domain.reports import (
    ClientRef,
    GroupKey,
    ProjectRef,
    ReportEntry,
    TagRef,
    Totals,
)
from hourtime.use_cases.dto import (
    DetailedReport,
    ReportDay,
    SummaryGroup,
    SummaryReport,
    WeeklyReport,
    WeeklyRow,
)

# Durations are whole seconds. Amounts are decimal strings such as "1503.33" in
# the workspace currency, summed from per-entry amounts rounded to the cent.


class ReportTotalsResponse(BaseModel):
    duration: int
    billable_duration: int
    amount: Decimal
    entries: int

    @classmethod
    def of(cls, totals: Totals) -> "ReportTotalsResponse":
        return cls(
            duration=totals.duration,
            billable_duration=totals.billable_duration,
            amount=totals.amount,
            entries=totals.entries,
        )


class ReportDayResponse(BaseModel):
    date: dt.date
    duration: int
    billable_duration: int
    amount: Decimal

    @classmethod
    def of(cls, day: ReportDay) -> "ReportDayResponse":
        return cls(
            date=day.day,
            duration=day.totals.duration,
            billable_duration=day.totals.billable_duration,
            amount=day.totals.amount,
        )


class SummarySubgroupResponse(BaseModel):
    # Null for the "no project / client / tags" group and for description groups.
    id: UUID | None
    # Null for the group of entries without a project, client, tags or description.
    name: str | None
    # Only projects have a color and a client.
    color: str | None
    client_name: str | None
    duration: int
    billable_duration: int
    amount: Decimal
    entries: int

    @classmethod
    def fields_of(cls, key: GroupKey, totals: Totals) -> dict[str, object]:
        return {
            "id": key.id,
            "name": key.name,
            "color": key.color,
            "client_name": key.client_name,
            "duration": totals.duration,
            "billable_duration": totals.billable_duration,
            "amount": totals.amount,
            "entries": totals.entries,
        }

    @classmethod
    def of(cls, group: SummaryGroup) -> "SummarySubgroupResponse":
        return cls.model_validate(cls.fields_of(group.key, group.totals))


class SummaryGroupResponse(SummarySubgroupResponse):
    # Empty when no `subgroup_by` was asked for.
    subgroups: list[SummarySubgroupResponse]

    @classmethod
    def of(cls, group: SummaryGroup) -> "SummaryGroupResponse":
        return cls.model_validate(
            {
                **cls.fields_of(group.key, group.totals),
                "subgroups": [SummarySubgroupResponse.of(item) for item in group.subgroups],
            }
        )


class SummaryReportResponse(BaseModel):
    currency: str
    totals: ReportTotalsResponse
    # Every day of the period, empty days as zeros; null without dates.
    by_day: list[ReportDayResponse] | None
    # Longest first. Grouped by tag, an entry counts under each of its tags,
    # so the groups may add up to more than `totals`.
    groups: list[SummaryGroupResponse]

    @classmethod
    def of(cls, report: SummaryReport) -> "SummaryReportResponse":
        return cls(
            currency=report.currency,
            totals=ReportTotalsResponse.of(report.totals),
            by_day=(
                None if report.by_day is None else [ReportDayResponse.of(d) for d in report.by_day]
            ),
            groups=[SummaryGroupResponse.of(group) for group in report.groups],
        )


class ReportProjectResponse(BaseModel):
    id: UUID
    name: str
    color: str

    @classmethod
    def of(cls, project: ProjectRef) -> "ReportProjectResponse":
        return cls(id=project.id, name=project.name, color=project.color)


class ReportClientResponse(BaseModel):
    id: UUID
    name: str

    @classmethod
    def of(cls, client: ClientRef) -> "ReportClientResponse":
        return cls(id=client.id, name=client.name)


class ReportTagResponse(BaseModel):
    id: UUID
    name: str

    @classmethod
    def of(cls, tag: TagRef) -> "ReportTagResponse":
        return cls(id=tag.id, name=tag.name)


class ReportEntryResponse(BaseModel):
    id: UUID
    description: str
    project: ReportProjectResponse | None
    client: ReportClientResponse | None
    # By name.
    tags: list[ReportTagResponse]
    billable: bool
    started_at: dt.datetime
    stopped_at: dt.datetime
    duration: int
    # Null unless the entry is billable and a rate applies.
    amount: Decimal | None

    @classmethod
    def of(cls, entry: ReportEntry) -> "ReportEntryResponse":
        return cls(
            id=entry.id,
            description=entry.description,
            project=ReportProjectResponse.of(entry.project) if entry.project else None,
            client=ReportClientResponse.of(entry.client) if entry.client else None,
            tags=[ReportTagResponse.of(tag) for tag in entry.tags],
            billable=entry.billable,
            started_at=entry.started_at,
            stopped_at=entry.stopped_at,
            duration=entry.duration,
            amount=entry.amount,
        )


class DetailedReportResponse(BaseModel):
    currency: str
    # Over every entry the filters let through; `entries` is what to page by.
    totals: ReportTotalsResponse
    items: list[ReportEntryResponse]
    has_more: bool
    limit: int
    offset: int

    @classmethod
    def of(cls, report: DetailedReport) -> "DetailedReportResponse":
        return cls(
            currency=report.currency,
            totals=ReportTotalsResponse.of(report.totals),
            items=[ReportEntryResponse.of(entry) for entry in report.items],
            has_more=report.has_more,
            limit=report.limit,
            offset=report.offset,
        )


class WeeklyTotalsResponse(ReportTotalsResponse):
    # Seconds per day, aligned with `WeeklyReportResponse.days`.
    days: list[int]


class WeeklyRowResponse(BaseModel):
    id: UUID | None
    name: str | None
    color: str | None
    client_name: str | None
    # Seconds per day, aligned with `WeeklyReportResponse.days`.
    days: list[int]
    duration: int
    billable_duration: int
    amount: Decimal
    entries: int

    @classmethod
    def of(cls, row: WeeklyRow) -> "WeeklyRowResponse":
        return cls(
            id=row.key.id,
            name=row.key.name,
            color=row.key.color,
            client_name=row.key.client_name,
            days=row.days,
            duration=row.totals.duration,
            billable_duration=row.totals.billable_duration,
            amount=row.totals.amount,
            entries=row.totals.entries,
        )


class WeeklyReportResponse(BaseModel):
    currency: str
    days: list[dt.date]
    totals: WeeklyTotalsResponse
    # Longest first.
    rows: list[WeeklyRowResponse]

    @classmethod
    def of(cls, report: WeeklyReport) -> "WeeklyReportResponse":
        totals = report.totals
        return cls(
            currency=report.currency,
            days=report.days,
            totals=WeeklyTotalsResponse(
                duration=totals.duration,
                billable_duration=totals.billable_duration,
                amount=totals.amount,
                entries=totals.entries,
                days=report.day_totals,
            ),
            rows=[WeeklyRowResponse.of(row) for row in report.rows],
        )
