"""Input and output data for use cases.

These are the only shapes the presentation layer is allowed to pass inwards —
HTTP schemas stay in `presentation`, ORM models stay in `infrastructure`.
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from hourtime.domain.entities import Session, TimeEntry, User
from hourtime.domain.entities.user import DurationFormat, HourCycle
from hourtime.domain.reports import (
    DetailedSort,
    GroupKey,
    ReportEntry,
    ReportGrouping,
    SortOrder,
    Totals,
    WeeklyGrouping,
)


class PatchInput(BaseModel):
    """Base for partial updates.

    Callers build these from `request_body.model_dump(exclude_unset=True)`, so
    `provided()` distinguishes "set this field to null" from "leave it alone".
    """

    model_config = ConfigDict(extra="forbid")

    def provided(self, field: str) -> bool:
        return field in self.model_fields_set


# --- auth -------------------------------------------------------------------


class RegisterUserInput(BaseModel):
    email: str
    password: str


class LoginUserInput(BaseModel):
    email: str
    password: str
    user_agent: str | None = None
    ip: str | None = None


class RefreshSessionInput(BaseModel):
    refresh_token: str
    user_agent: str | None = None
    ip: str | None = None


class SessionTokens(BaseModel):
    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime


class IssuedSession(BaseModel):
    session: Session
    tokens: SessionTokens


class LoginResult(BaseModel):
    user: User
    tokens: SessionTokens


class AuthenticatedUser(BaseModel):
    user: User
    session_id: UUID

    @property
    def workspace_id(self) -> UUID:
        """The workspace every request works in until the API lets one be picked."""
        return self.user.default_workspace_id


class UpdateProfileInput(PatchInput):
    user_id: UUID
    display_name: str | None = None
    timezone: str | None = None
    week_start: int | None = None
    duration_format: DurationFormat | None = None
    hour_cycle: HourCycle | None = None


class ChangePasswordInput(BaseModel):
    user_id: UUID
    # The session that asked for the change stays signed in; the rest are revoked.
    session_id: UUID
    current_password: str
    new_password: str


# --- workspaces -------------------------------------------------------------


class UpdateWorkspaceInput(PatchInput):
    workspace_id: UUID
    default_hourly_rate: Decimal | None = None
    currency: str | None = None


# --- clients ----------------------------------------------------------------


class CreateClientInput(BaseModel):
    workspace_id: UUID
    name: str


class UpdateClientInput(PatchInput):
    workspace_id: UUID
    client_id: UUID
    name: str | None = None
    archived: bool | None = None


# --- tags -------------------------------------------------------------------


class CreateTagInput(BaseModel):
    workspace_id: UUID
    name: str


class UpdateTagInput(BaseModel):
    workspace_id: UUID
    tag_id: UUID
    name: str


# --- projects ---------------------------------------------------------------


class CreateProjectInput(BaseModel):
    workspace_id: UUID
    name: str
    color: str | None = None
    client_id: UUID | None = None
    billable: bool = False
    hourly_rate: Decimal | None = None


class UpdateProjectInput(PatchInput):
    workspace_id: UUID
    project_id: UUID
    name: str | None = None
    color: str | None = None
    archived: bool | None = None
    client_id: UUID | None = None
    billable: bool | None = None
    hourly_rate: Decimal | None = None


# --- time entries -----------------------------------------------------------


class StartTimerInput(BaseModel):
    user_id: UUID
    workspace_id: UUID
    project_id: UUID | None = None
    tag_ids: list[UUID] = Field(default_factory=list)
    description: str = ""
    # None follows the project's default.
    billable: bool | None = None
    started_at: datetime | None = None


class StopTimerInput(BaseModel):
    user_id: UUID
    workspace_id: UUID
    entry_id: UUID | None = None
    stopped_at: datetime | None = None


class CreateTimeEntryInput(BaseModel):
    user_id: UUID
    workspace_id: UUID
    project_id: UUID | None = None
    tag_ids: list[UUID] = Field(default_factory=list)
    description: str = ""
    # None follows the project's default.
    billable: bool | None = None
    started_at: datetime
    stopped_at: datetime


class UpdateTimeEntryInput(PatchInput):
    user_id: UUID
    workspace_id: UUID
    entry_id: UUID
    project_id: UUID | None = None
    tag_ids: list[UUID] | None = None
    description: str | None = None
    billable: bool | None = None
    started_at: datetime | None = None
    stopped_at: datetime | None = None


class ListTimeEntriesInput(BaseModel):
    user_id: UUID
    workspace_id: UUID
    started_from: datetime | None = None
    started_to: datetime | None = None
    project_id: UUID | None = None
    client_id: UUID | None = None
    tag_ids: list[UUID] = Field(default_factory=list)
    without_project: bool = False
    limit: int = 50
    offset: int = 0


class SuggestTimeEntriesInput(BaseModel):
    user_id: UUID
    workspace_id: UUID
    query: str = ""
    limit: int = 10


class TimeEntryPage(BaseModel):
    items: list[TimeEntry]
    # No total: knowing it costs a second query on every page load, and the list
    # only needs to know whether a "load more" button belongs on screen.
    has_more: bool
    limit: int
    offset: int


# --- reports ----------------------------------------------------------------


class ReportFiltersInput(BaseModel):
    """Filters shared by every report.

    Dates are local to `timezone` and both inclusive; give both or neither.
    Each id list goes with a `without_*` flag, and an entry passes when it
    matches the list OR the flag.
    """

    user_id: UUID
    workspace_id: UUID
    # The user's IANA zone; None means UTC.
    timezone: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    project_ids: list[UUID] = Field(default_factory=list)
    without_project: bool = False
    client_ids: list[UUID] = Field(default_factory=list)
    without_client: bool = False
    tag_ids: list[UUID] = Field(default_factory=list)
    without_tags: bool = False
    billable: bool | None = None
    description: str = ""


class SummaryReportInput(BaseModel):
    filters: ReportFiltersInput
    group_by: ReportGrouping = "project"
    subgroup_by: ReportGrouping | None = None


class DetailedReportInput(BaseModel):
    filters: ReportFiltersInput
    sort: DetailedSort = "started_at"
    order: SortOrder = "desc"
    limit: int = 50
    offset: int = 0


class WeeklyReportInput(BaseModel):
    filters: ReportFiltersInput
    group_by: WeeklyGrouping = "project"


class ReportDay(BaseModel):
    day: date
    totals: Totals


class SummaryGroup(BaseModel):
    key: GroupKey
    totals: Totals
    subgroups: list["SummaryGroup"] = Field(default_factory=list)


class SummaryReport(BaseModel):
    currency: str
    totals: Totals
    # Every day of the period in order, empty ones included; None without dates.
    by_day: list[ReportDay] | None
    # Longest first; with grouping by tag their sum can exceed `totals`.
    groups: list[SummaryGroup]


class DetailedReport(BaseModel):
    currency: str
    # Over every entry that passes the filters, not just this page.
    totals: Totals
    items: list[ReportEntry]
    has_more: bool
    limit: int
    offset: int


class WeeklyRow(BaseModel):
    key: GroupKey
    totals: Totals
    # Seconds per day, aligned with `WeeklyReport.days`.
    days: list[int]


class WeeklyReport(BaseModel):
    currency: str
    days: list[date]
    totals: Totals
    day_totals: list[int]
    rows: list[WeeklyRow]
