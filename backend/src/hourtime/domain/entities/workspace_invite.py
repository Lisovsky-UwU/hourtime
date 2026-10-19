from datetime import datetime, timedelta
from uuid import UUID

from hourtime.domain.entities.base import Entity, UtcDatetime
from hourtime.domain.entities.workspace_member import MemberRole

INVITE_TTL = timedelta(days=7)


class WorkspaceInvite(Entity):
    """A one-time link an admin hands out; only the token's digest is stored."""

    id: UUID
    workspace_id: UUID
    token_hash: str
    role: MemberRole
    created_by: UUID
    created_at: UtcDatetime
    expires_at: UtcDatetime
    used_at: UtcDatetime | None = None

    def is_open(self, now: datetime) -> bool:
        return self.used_at is None and now < self.expires_at
