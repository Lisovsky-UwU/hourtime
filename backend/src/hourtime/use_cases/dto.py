"""Input and output data for use cases.

These are the only shapes the presentation layer is allowed to pass inwards —
HTTP schemas stay in `presentation`, ORM models stay in `infrastructure`.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from hourtime.domain.entities import Session, TimeEntry, User


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


# --- projects ---------------------------------------------------------------


class CreateProjectInput(BaseModel):
    user_id: UUID
    name: str
    color: str | None = None


class UpdateProjectInput(PatchInput):
    user_id: UUID
    project_id: UUID
    name: str | None = None
    color: str | None = None
    archived: bool | None = None


# --- time entries -----------------------------------------------------------


class StartTimerInput(BaseModel):
    user_id: UUID
    project_id: UUID | None = None
    description: str = ""
    started_at: datetime | None = None


class StopTimerInput(BaseModel):
    user_id: UUID
    entry_id: UUID | None = None
    stopped_at: datetime | None = None


class CreateTimeEntryInput(BaseModel):
    user_id: UUID
    project_id: UUID | None = None
    description: str = ""
    started_at: datetime
    stopped_at: datetime


class UpdateTimeEntryInput(PatchInput):
    user_id: UUID
    entry_id: UUID
    project_id: UUID | None = None
    description: str | None = None
    started_at: datetime | None = None
    stopped_at: datetime | None = None


class ListTimeEntriesInput(BaseModel):
    user_id: UUID
    started_from: datetime | None = None
    started_to: datetime | None = None
    project_id: UUID | None = None
    limit: int = 50
    offset: int = 0


class SuggestTimeEntriesInput(BaseModel):
    user_id: UUID
    query: str = ""
    limit: int = 10


class TimeEntryPage(BaseModel):
    items: list[TimeEntry]
    # No total: knowing it costs a second query on every page load, and the list
    # only needs to know whether a "load more" button belongs on screen.
    has_more: bool
    limit: int
    offset: int
