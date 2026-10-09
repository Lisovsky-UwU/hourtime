from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest

from hourtime.domain.errors import NotFound, ValidationError
from hourtime.domain.reports import (
    DayTotals,
    GroupDayTotals,
    GroupKey,
    GroupTotals,
    ReportEntry,
    Totals,
)
from hourtime.use_cases.dto import (
    DetailedReportInput,
    ReportFiltersInput,
    SummaryReportInput,
    WeeklyReportInput,
)
from hourtime.use_cases.reports import GetDetailedReport, GetSummaryReport, GetWeeklyReport
from hourtime.use_cases.reports.rules import report_criteria
from tests.factories import make_user, make_workspace
from tests.fakes import CannedReportRepository, InMemoryWorkspaceRepository

USER = make_user()
WORKSPACE = make_workspace(USER, currency="RUB")


def filters(**overrides: Any) -> ReportFiltersInput:
    values: dict[str, Any] = {"user_id": USER.id, "workspace_id": WORKSPACE.id}
    values.update(overrides)
    return ReportFiltersInput(**values)


def week(**overrides: Any) -> ReportFiltersInput:
    return filters(start_date=date(2025, 2, 3), end_date=date(2025, 2, 9), **overrides)


def figures(seconds: int, *, amount: str = "0.00", entries: int = 1) -> dict[str, Any]:
    return {
        "duration": seconds,
        "billable_duration": 0,
        "amount": Decimal(amount),
        "entries": entries,
    }


PROJECT_A = GroupKey(id=uuid4(), name="alpha", color="#111111")
PROJECT_B = GroupKey(id=uuid4(), name="Beta", color="#222222")
NO_PROJECT = GroupKey()


class ReportWorld:
    def __init__(self) -> None:
        self.reports = CannedReportRepository()
        self.workspaces = InMemoryWorkspaceRepository([WORKSPACE])
        self.summary = GetSummaryReport(self.reports, self.workspaces)
        self.detailed = GetDetailedReport(self.reports, self.workspaces)
        self.weekly = GetWeeklyReport(self.reports, self.workspaces)


@pytest.fixture
def world() -> ReportWorld:
    return ReportWorld()


class TestCriteria:
    def test_dates_become_local_midnights_in_utc(self) -> None:
        criteria = report_criteria(week(timezone="Asia/Novosibirsk"))
        assert criteria.timezone == "Asia/Novosibirsk"
        assert criteria.started_from == datetime(2025, 2, 2, 17, 0, tzinfo=UTC)
        # Exclusive end: midnight after the last day.
        assert criteria.started_before == datetime(2025, 2, 9, 17, 0, tzinfo=UTC)

    def test_no_zone_means_utc(self) -> None:
        criteria = report_criteria(week())
        assert criteria.timezone == "UTC"
        assert criteria.started_from == datetime(2025, 2, 3, tzinfo=UTC)
        assert criteria.started_before == datetime(2025, 2, 10, tzinfo=UTC)

    def test_daylight_saving_day_is_23_hours_long(self) -> None:
        criteria = report_criteria(
            filters(
                timezone="America/Los_Angeles",
                start_date=date(2025, 3, 9),
                end_date=date(2025, 3, 9),
            )
        )
        assert criteria.started_from == datetime(2025, 3, 9, 8, 0, tzinfo=UTC)
        assert criteria.started_before == datetime(2025, 3, 10, 7, 0, tzinfo=UTC)

    def test_without_dates_the_period_is_open(self) -> None:
        criteria = report_criteria(filters())
        assert (criteria.started_from, criteria.started_before) == (None, None)

    @pytest.mark.parametrize(
        "dates",
        [
            {"start_date": date(2025, 2, 3)},
            {"end_date": date(2025, 2, 3)},
            {"start_date": date(2025, 2, 4), "end_date": date(2025, 2, 3)},
        ],
    )
    def test_rejects_half_or_reversed_periods(self, dates: dict[str, date]) -> None:
        with pytest.raises(ValidationError):
            report_criteria(filters(**dates))

    def test_rejects_an_unknown_zone(self) -> None:
        with pytest.raises(ValidationError):
            report_criteria(filters(timezone="Nowhere/Town"))

    def test_passes_the_filters_through(self) -> None:
        project, tag = uuid4(), uuid4()
        criteria = report_criteria(
            filters(
                project_ids=[project],
                without_project=True,
                without_client=True,
                tag_ids=[tag],
                billable=False,
                description="100%",
            )
        )
        assert criteria.project_ids == [project]
        assert criteria.without_project is True
        assert criteria.client_ids == []
        assert criteria.without_client is True
        assert criteria.tag_ids == [tag]
        assert criteria.without_tags is False
        assert criteria.billable is False
        assert criteria.description == "100%"


class TestSummary:
    async def test_fills_every_day_of_the_period(self, world: ReportWorld) -> None:
        world.reports.days = [DayTotals(day=date(2025, 2, 5), **figures(3600, amount="10.50"))]

        report = await world.summary.execute(SummaryReportInput(filters=week()))

        assert report.currency == "RUB"
        assert report.by_day is not None
        assert [day.day for day in report.by_day] == [date(2025, 2, d) for d in range(3, 10)]
        assert [day.totals.duration for day in report.by_day] == [0, 0, 3600, 0, 0, 0, 0]
        assert report.by_day[0].totals.amount == Decimal("0.00")
        assert report.by_day[2].totals.amount == Decimal("10.50")

    async def test_no_days_without_a_period(self, world: ReportWorld) -> None:
        report = await world.summary.execute(SummaryReportInput(filters=filters()))
        assert report.by_day is None
        assert "totals_by_day" not in [name for name, _ in world.reports.calls]

    async def test_groups_longest_first_then_by_name_with_unnamed_last(
        self, world: ReportWorld
    ) -> None:
        world.reports.groups = [
            GroupTotals(group=NO_PROJECT, **figures(3600)),
            GroupTotals(group=PROJECT_B, **figures(3600)),
            GroupTotals(group=PROJECT_A, **figures(3600)),
            GroupTotals(group=GroupKey(id=uuid4(), name="zeta"), **figures(7200)),
        ]

        report = await world.summary.execute(SummaryReportInput(filters=filters()))

        assert [group.key.name for group in report.groups] == ["zeta", "alpha", "Beta", None]
        assert all(group.subgroups == [] for group in report.groups)

    async def test_subgroups_land_under_their_group(self, world: ReportWorld) -> None:
        red, blue = GroupKey(id=uuid4(), name="red"), GroupKey(id=uuid4(), name="blue")
        world.reports.groups = [
            GroupTotals(group=PROJECT_A, **figures(5400, entries=2)),
            GroupTotals(group=NO_PROJECT, **figures(600)),
        ]
        world.reports.pairs = [
            GroupTotals(group=PROJECT_A, subgroup=blue, **figures(3600)),
            GroupTotals(group=PROJECT_A, subgroup=red, **figures(5400, entries=2)),
            GroupTotals(group=NO_PROJECT, subgroup=GroupKey(), **figures(600)),
        ]

        report = await world.summary.execute(
            SummaryReportInput(filters=filters(), group_by="project", subgroup_by="tag")
        )

        first, second = report.groups
        assert first.key == PROJECT_A
        # The group keeps its own figures; tags overlap, so subgroups add up to more.
        assert first.totals.duration == 5400
        assert [(sub.key.name, sub.totals.duration) for sub in first.subgroups] == [
            ("red", 5400),
            ("blue", 3600),
        ]
        assert [sub.key for sub in second.subgroups] == [GroupKey()]

    async def test_subgroup_must_differ(self, world: ReportWorld) -> None:
        with pytest.raises(ValidationError):
            await world.summary.execute(
                SummaryReportInput(filters=filters(), group_by="tag", subgroup_by="tag")
            )

    async def test_missing_workspace(self, world: ReportWorld) -> None:
        with pytest.raises(NotFound):
            await world.summary.execute(SummaryReportInput(filters=filters(workspace_id=uuid4())))


class TestDetailed:
    @staticmethod
    def entry(hour: int) -> ReportEntry:
        return ReportEntry(
            id=uuid4(),
            description="",
            billable=False,
            started_at=datetime(2025, 2, 3, hour, tzinfo=UTC),
            stopped_at=datetime(2025, 2, 3, hour, 30, tzinfo=UTC),
            duration=1800,
        )

    async def test_pages_and_totals(self, world: ReportWorld) -> None:
        world.reports.entries = [self.entry(hour) for hour in range(9, 14)]
        world.reports.total = Totals(**figures(9000, entries=5))

        first = await world.detailed.execute(
            DetailedReportInput(filters=filters(), sort="duration", order="asc", limit=3)
        )
        assert (len(first.items), first.has_more, first.totals.entries) == (3, True, 5)
        # One extra row tells whether another page exists.
        assert world.reports.page_requests[0] == {
            "sort": "duration",
            "order": "asc",
            "limit": 4,
            "offset": 0,
        }

        last = await world.detailed.execute(
            DetailedReportInput(filters=filters(), limit=3, offset=3)
        )
        assert (len(last.items), last.has_more, last.totals.entries) == (2, False, 5)

    @pytest.mark.parametrize(("limit", "offset"), [(0, 0), (201, 0), (50, -1)])
    async def test_rejects_bad_paging(self, world: ReportWorld, limit: int, offset: int) -> None:
        with pytest.raises(ValidationError):
            await world.detailed.execute(
                DetailedReportInput(filters=filters(), limit=limit, offset=offset)
            )


class TestWeekly:
    async def test_rows_days_and_totals(self, world: ReportWorld) -> None:
        world.reports.cells = [
            GroupDayTotals(group=PROJECT_A, day=date(2025, 2, 3), **figures(3600, amount="1.25")),
            GroupDayTotals(group=NO_PROJECT, day=date(2025, 2, 9), **figures(7200)),
            GroupDayTotals(group=PROJECT_A, day=date(2025, 2, 5), **figures(1800, amount="2.50")),
        ]

        report = await world.weekly.execute(WeeklyReportInput(filters=week()))

        assert report.days == [date(2025, 2, d) for d in range(3, 10)]
        assert [(row.key, row.days) for row in report.rows] == [
            (NO_PROJECT, [0, 0, 0, 0, 0, 0, 7200]),
            (PROJECT_A, [3600, 0, 1800, 0, 0, 0, 0]),
        ]
        assert report.rows[1].totals == Totals(**figures(5400, amount="3.75", entries=2))
        assert report.totals == Totals(**figures(12600, amount="3.75", entries=3))
        assert report.day_totals == [3600, 0, 1800, 0, 0, 0, 7200]

    async def test_empty_week(self, world: ReportWorld) -> None:
        report = await world.weekly.execute(WeeklyReportInput(filters=week()))
        assert report.rows == []
        assert report.totals == Totals()
        assert report.day_totals == [0] * 7

    @pytest.mark.parametrize(
        "dates",
        [
            {},
            {"start_date": date(2025, 2, 3)},
            {"start_date": date(2025, 2, 3), "end_date": date(2025, 2, 10)},
        ],
    )
    async def test_needs_a_period_of_at_most_a_week(
        self, world: ReportWorld, dates: dict[str, date]
    ) -> None:
        with pytest.raises(ValidationError):
            await world.weekly.execute(WeeklyReportInput(filters=filters(**dates)))
        assert world.reports.calls == []
