from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from hourtime.domain.billing import HourlyRate
from hourtime.domain.entities import MemberRole, Workspace, WorkspaceInvite
from hourtime.domain.entities.workspace import NAME_MAX_LENGTH
from hourtime.use_cases.dto import MemberAccount, MemberWorkspace


class WorkspaceResponse(BaseModel):
    id: UUID
    name: str
    # A decimal string such as "150.00", or null when no default rate is set.
    default_hourly_rate: Decimal | None
    currency: str

    @classmethod
    def of(cls, workspace: Workspace) -> "WorkspaceResponse":
        return cls(
            id=workspace.id,
            name=workspace.name,
            default_hourly_rate=workspace.default_hourly_rate,
            currency=workspace.currency,
        )


class MemberWorkspaceResponse(WorkspaceResponse):
    # The caller's role in this workspace.
    role: MemberRole

    @classmethod
    def of_member(cls, found: MemberWorkspace) -> "MemberWorkspaceResponse":
        return cls(**WorkspaceResponse.of(found.workspace).model_dump(), role=found.role)


class UpdateWorkspaceRequest(BaseModel):
    """Omitted fields are left untouched; `default_hourly_rate: null` removes the rate."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=NAME_MAX_LENGTH)
    default_hourly_rate: HourlyRate | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)


class CreateWorkspaceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)


class MemberResponse(BaseModel):
    user_id: UUID
    email: str
    display_name: str | None
    role: MemberRole
    is_owner: bool
    joined_at: datetime

    @classmethod
    def of(cls, account: MemberAccount) -> "MemberResponse":
        return cls(
            user_id=account.user.id,
            email=account.user.email,
            display_name=account.user.display_name,
            role=account.member.role,
            is_owner=account.is_owner,
            joined_at=account.member.created_at,
        )


class UpdateMemberRequest(BaseModel):
    role: MemberRole


class CreateInviteRequest(BaseModel):
    role: MemberRole = "member"


class InviteResponse(BaseModel):
    id: UUID
    role: MemberRole
    created_at: datetime
    expires_at: datetime

    @classmethod
    def of(cls, invite: WorkspaceInvite) -> "InviteResponse":
        return cls(
            id=invite.id,
            role=invite.role,
            created_at=invite.created_at,
            expires_at=invite.expires_at,
        )


class IssuedInviteResponse(InviteResponse):
    # Only here: the server keeps a digest and cannot show the token again.
    token: str


class InviteTokenRequest(BaseModel):
    """The token travels in the body so it stays out of URLs and access logs."""

    token: str = Field(min_length=1, max_length=128)


class InvitePreviewResponse(BaseModel):
    workspace_name: str
    invited_by: str
    role: MemberRole
